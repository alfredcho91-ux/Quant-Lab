# core/mu_long.py

import math
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from core.data import mu_load_and_filter_data


# μ 연구에 사용할 타임프레임 목록
MU_TFS = ["15m", "30m", "1h", "2h", "4h", "12h", "1d"]

# 타임프레임 정렬용
MU_TF_ORDER = {
    "15m": 0,
    "30m": 1,
    "1h":  2,
    "2h":  3,
    "4h":  4,
    "12h": 5,
    "1d":  6,
}


def mu_get_files_for_coin(coin: str) -> Dict[str, str]:
    """
    선택한 코인(BTC, ETH, XRP, SOL 등)에 대해
    각 타임프레임별 CSV 파일명을 만들어 줍니다.
    예: 'BTC' → 'BTCUSDT-1h-merged.csv'
    """
    return {tf: f"{coin}USDT-{tf}-merged.csv" for tf in MU_TFS}


def mu_periods_per_year(tf: str) -> int:
    if tf == "15m":
        return 365 * 24 * 4
    if tf == "30m":
        return 365 * 24 * 2
    if tf == "1h":
        return 365 * 24
    if tf == "2h":
        return 365 * 12
    if tf == "4h":
        return 365 * 6
    if tf == "12h":
        return 365 * 2
    if tf == "1d":
        return 365
    return 365


def compute_full_stats_mu(df: pd.DataFrame, tf: str, mode: str = "candle") -> dict:
    """
    단일 타임프레임 df에 대해:
      - 승률, 평균 상승/하락폭, 총 수익률, Sharpe 등을 계산
    """
    df = df.copy()

    # 수익률 계산
    if mode == "candle":
        df["ret"] = (df["close"] - df["open"]) / df["open"]
    elif mode == "close":
        df["ret"] = df["close"].pct_change()
    else:
        raise ValueError("mode must be 'candle' or 'close'")

    df = df.dropna(subset=["ret"])

    up = df[df["ret"] > 0]["ret"]
    down = df[df["ret"] < 0]["ret"]

    n_up = len(up)
    n_down = len(down)
    n_total = n_up + n_down

    avg_up = float(up.mean()) if n_up > 0 else float("nan")
    avg_down = float(down.mean()) if n_down > 0 else float("nan")
    win_rate = (n_up / n_total) if n_total > 0 else float("nan")

    # 구간 총 수익률 (첫 open → 마지막 close)
    start_price = df.iloc[0]["open"]
    end_price = df.iloc[-1]["close"]
    total_ret = (end_price - start_price) / start_price

    # Sharpe 연율화
    ann_factor = math.sqrt(mu_periods_per_year(tf))
    vol = df["ret"].std(ddof=1)
    if vol == 0 or np.isnan(vol):
        sharpe = float("nan")
    else:
        sharpe = (df["ret"].mean() * ann_factor) / vol

    return {
        "tf": tf,
        "n_total": n_total,
        "n_up": n_up,
        "n_down": n_down,
        "win_rate_%": win_rate * 100 if not math.isnan(win_rate) else float("nan"),
        "avg_up_%": avg_up * 100 if not math.isnan(avg_up) else float("nan"),
        "avg_down_%": avg_down * 100 if not math.isnan(avg_down) else float("nan"),
        "total_ret_%": total_ret * 100,
        "sharpe": sharpe,
        "order": MU_TF_ORDER.get(tf, 999),
    }


def compute_stats_for_range(
    coin: str,
    start_date: str,
    end_date: str = None,
    mode: str = "candle",
) -> pd.DataFrame:
    """
    μ 연구 탭에서 쓰는 함수.
    - coin      : 'BTC', 'ETH', 'XRP', 'SOL' 등
    - start_date, end_date : 'YYYY-MM-DD'
    """
    mu_files = mu_get_files_for_coin(coin)

    rows = []
    for tf, path in mu_files.items():
        df = mu_load_and_filter_data(path, start_date, end_date)
        if df.empty:
            continue
        stats = compute_full_stats_mu(df, tf, mode=mode)
        rows.append(stats)

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows).sort_values("order")
    return result


def mu_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    단순 RSI 구현 (μ 전략용)
    """
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    gain = pd.Series(gain, index=series.index)
    loss = pd.Series(loss, index=series.index)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val


def prepare_1h_4h_data(
    coin: str,
    start_date: str,
    end_date: str = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    μ 전략용으로 1h, 4h 데이터를 준비:
      - coin: 'BTC', 'ETH', 'XRP', 'SOL' 등
      - 1h: 캔들 수익률, RSI(14)
      - 4h: EMA(200) (간단히 ewm으로 계산)
      - 4h 지표를 1h 타임프레임에 merge_asof로 매핑
      - [start_date, end_date] 구간으로 잘라서 사용
    """
    mu_files = mu_get_files_for_coin(coin)

    df_1h = mu_load_and_filter_data(mu_files["1h"], start_date, end_date)
    df_4h = mu_load_and_filter_data(mu_files["4h"], start_date, end_date)

    # 1h: 캔들 기준 수익률, RSI
    df_1h = df_1h.sort_values("date").reset_index(drop=True)
    df_1h["ret_candle"] = (df_1h["close"] - df_1h["open"]) / df_1h["open"] * 100.0
    df_1h["rsi_14"] = mu_rsi(df_1h["close"], period=14)

    # 4h: EMA(200)
    df_4h = df_4h.sort_values("date").reset_index(drop=True)
    df_4h["ema_200"] = df_4h["close"].ewm(span=200, adjust=False).mean()

    # 4h → 1h로 매핑 (가장 최근 4h 값을 1h에 붙임)
    df_4h_slim = df_4h[["date", "close", "ema_200"]].copy()
    df_merged = pd.merge_asof(
        df_1h.sort_values("date"),
        df_4h_slim.sort_values("date"),
        on="date",
        direction="backward",
        suffixes=("", "_4h"),
    )

    return df_merged, df_1h, df_4h


def build_tp_sl_from_stats(
    stats_1h: pd.Series,
    k_entry: float = 1.0,
    k_SL: float = 1.5,
    k_TP: float = 2.0,
) -> dict:
    """
    1h 통계에서 평균 상승/하락폭을 읽어와 TP/SL % 파라미터 계산
    """
    mu_up = stats_1h["avg_up_%"]           # 예: +0.5 (%)
    mu_down = abs(stats_1h["avg_down_%"])  # 예: 0.5 (%)

    SL_pct = k_SL * mu_down   # 손절폭 (%)
    TP_pct = k_TP * mu_up     # 익절폭 (%)

    return {
        "mu_up": mu_up,
        "mu_down": mu_down,
        "k_entry": k_entry,
        "k_SL": k_SL,
        "k_TP": k_TP,
        "SL_pct": SL_pct,
        "TP_pct": TP_pct,
    }


def backtest_long_strategy(
    df_merged: pd.DataFrame,
    tp_sl_cfg: dict,
    sharpe_4h: float,
    rsi_oversold: float = 30.0,
) -> pd.DataFrame:
    """
    μ 기반 단순 Long-only 전략 백테스트
    """
    df = df_merged.copy().reset_index(drop=True)

    # Sharpe 4h가 0 이하이면 전략 비활성화 (예: 관망)
    if sharpe_4h <= 0:
        return pd.DataFrame(
            columns=[
                "entry_time",
                "exit_time",
                "entry_price",
                "exit_price",
                "pnl_%",
                "reason",
            ]
        )

    SL_pct = tp_sl_cfg["SL_pct"]
    TP_pct = tp_sl_cfg["TP_pct"]
    k_entry = tp_sl_cfg["k_entry"]
    mu_down = tp_sl_cfg["mu_down"]

    trades = []
    position = None
    entry_price = None
    sl_price = None
    tp_price = None
    entry_time = None

    for i in range(1, len(df)):
        row_prev = df.iloc[i - 1]
        row = df.iloc[i]

        price_open = row["open"]
        price_high = row["high"]
        price_low = row["low"]
        price_close = row["close"]

        ema_200_4h = row["ema_200"]
        price_4h = row["close_4h"] if "close_4h" in df.columns else row["close"]

        # 상위 추세 필터: 상승 추세 (4h 가격 > EMA200)
        uptrend = (not pd.isna(ema_200_4h)) and (price_4h > ema_200_4h)

        # 포지션 없음 → 진입 조건 체크
        if position is None:
            ret_prev = row_prev["ret_candle"]   # 이전 캔들 수익률 (%)
            rsi_prev = row_prev["rsi_14"]

            cond_pullback = ret_prev <= -mu_down * k_entry   # 충분한 하락
            cond_oversold = (rsi_prev < rsi_oversold)
            cond_rebound = (price_close > price_open)        # 현재 캔들이 양봉
            cond_trend = uptrend

            if cond_trend and cond_pullback and cond_oversold and cond_rebound:
                position = "long"
                entry_price = price_open
                entry_time = row["date"]
                sl_price = entry_price * (1 - SL_pct / 100.0)
                tp_price = entry_price * (1 + TP_pct / 100.0)
                continue

        # 포지션 보유 중 → SL/TP 체크
        else:
            hit_SL = price_low <= sl_price
            hit_TP = price_high >= tp_price

            exit_price = None
            reason = None

            if hit_SL and hit_TP:
                exit_price = sl_price
                reason = "SL_and_TP_same_bar(SL_priority)"
            elif hit_SL:
                exit_price = sl_price
                reason = "SL"
            elif hit_TP:
                exit_price = tp_price
                reason = "TP"

            if exit_price is not None:
                pnl_pct = (exit_price - entry_price) / entry_price * 100.0
                trades.append(
                    {
                        "entry_time": entry_time,
                        "exit_time": row["date"],
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_%": pnl_pct,
                        "reason": reason,
                    }
                )
                position = None
                entry_price = sl_price = tp_price = entry_time = None

    trades_df = pd.DataFrame(trades)
    return trades_df


def summarize_trades(trades_df: pd.DataFrame) -> dict:
    """
    μ 전략용 트레이드 요약 (UI 에서 metric으로 쓰기 좋게 dict 반환)
    """
    if trades_df.empty:
        return {
            "n_trades": 0,
            "win_rate": float("nan"),
            "avg_pnl": float("nan"),
            "total_pnl": float("nan"),
        }

    n_trades = len(trades_df)
    wins = trades_df[trades_df["pnl_%"] > 0]

    win_rate = len(wins) / n_trades * 100.0
    avg_pnl = trades_df["pnl_%"].mean()
    total_pnl = (trades_df["pnl_%"] / 100 + 1).prod() - 1

    return {
        "n_trades": n_trades,
        "win_rate": win_rate,
        "avg_pnl": avg_pnl,
        "total_pnl": total_pnl * 100,
    }