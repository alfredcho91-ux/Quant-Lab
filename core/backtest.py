import numpy as np
import pandas as pd


def run_backtest(
    df: pd.DataFrame,
    signal_col: str,
    direction: str = "Long",          # "Long" or "Short"
    strategy_type: str = "Fixed",     # "Fixed" | "Connors" | "Squeeze"
    tp_pct: float = 0.02,
    sl_pct: float = 0.01,
    max_bars: int = 48,
    leverage: int = 5,
    fee_entry_rate: float = 0.0005,
    fee_exit_rate: float = 0.0005,
) -> pd.DataFrame:
    """
    공통 백테스트 엔진 (8개 전략용)

    df           : prepare_strategy_data()를 거친 OHLCV 데이터프레임
    signal_col   : 진입 시그널 컬럼 이름 (예: 'Sig_Connors_Long')
    direction    : "Long" 또는 "Short"
    strategy_type: 'Fixed', 'Connors', 'Squeeze'
    tp_pct       : 익절 퍼센트 (0.02 = +2%)
    sl_pct       : 손절 퍼센트 (0.01 = -1%)
    max_bars     : 진입 후 최대 보유 봉 수
    leverage     : 선물 레버리지
    fee_entry_rate, fee_exit_rate : 편도 수수료율 (예: 0.0005 = 0.05%)
    """

    df = df.copy()
    mask = df[signal_col].fillna(False).astype(bool)
    sig_idx = df.index[mask]
    if len(sig_idx) == 0:
        return pd.DataFrame()

    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    times = df["open_dt"].values
    regimes = df["Regime"].values

    sma_short = df["SMA_1"].values if "SMA_1" in df.columns else None
    bb_mid = df["BB_Mid"].values if "BB_Mid" in df.columns else None

    fee_total = (fee_entry_rate + fee_exit_rate) * leverage
    res = []
    n = len(df)

    for idx in sig_idx:
        if idx + 1 >= n:
            continue

        entry_price = closes[idx]
        entry_time = times[idx]
        entry_regime = regimes[idx]

        # 방향에 따른 기본 TP/SL/청산가
        if direction == "Long":
            liq = entry_price * (1 - 1.0 / leverage)
            target = entry_price * (1 + tp_pct)
            stop = entry_price * (1 - sl_pct)
        else:  # Short
            liq = entry_price * (1 + 1.0 / leverage)
            target = entry_price * (1 - tp_pct)
            stop = entry_price * (1 + sl_pct)

        outcome = "TimeOut"
        raw = 0.0
        exit_idx = min(idx + max_bars, n - 1)
        exit_price = closes[exit_idx]

        for i in range(1, max_bars + 1):
            ci = idx + i
            if ci >= n:
                break

            c = closes[ci]
            h = highs[ci]
            l = lows[ci]
            done = False

            # 1) 강제 청산
            if (direction == "Long" and l <= liq) or (direction == "Short" and h >= liq):
                outcome = "💀 Liquidation"
                raw = -1.0
                exit_price = liq
                exit_idx = ci
                done = True
            if done:
                break

            # 2) 전략별 특수 청산 (Connors: SMA, Squeeze: BB Mid)
            if strategy_type == "Connors" and sma_short is not None:
                if direction == "Long" and c > sma_short[ci]:
                    outcome = "Exit (SMA↑)"
                    raw = (c - entry_price) / entry_price
                    exit_price = c
                    exit_idx = ci
                    done = True
                elif direction == "Short" and c < sma_short[ci]:
                    outcome = "Exit (SMA↓)"
                    raw = (entry_price - c) / entry_price
                    exit_price = c
                    exit_idx = ci
                    done = True
                if done:
                    break

            if strategy_type == "Squeeze" and bb_mid is not None:
                if direction == "Long" and c < bb_mid[ci]:
                    outcome = "Exit (Mid↓)"
                    raw = (c - entry_price) / entry_price
                    exit_price = c
                    exit_idx = ci
                    done = True
                elif direction == "Short" and c > bb_mid[ci]:
                    outcome = "Exit (Mid↑)"
                    raw = (entry_price - c) / entry_price
                    exit_price = c
                    exit_idx = ci
                    done = True
                if done:
                    break

            # 3) 일반 TP/SL
            if direction == "Long":
                if l <= stop:
                    outcome = "SL"
                    raw = -sl_pct
                    exit_price = stop
                    exit_idx = ci
                    done = True
                elif h >= target:
                    outcome = "TP"
                    raw = tp_pct
                    exit_price = target
                    exit_idx = ci
                    done = True
            else:  # Short
                if h >= stop:
                    outcome = "SL"
                    raw = -sl_pct
                    exit_price = stop
                    exit_idx = ci
                    done = True
                elif l <= target:
                    outcome = "TP"
                    raw = tp_pct
                    exit_price = target
                    exit_idx = ci
                    done = True

            if done:
                break

        # 4) 타임아웃 (max_bars 도달)
        if outcome == "TimeOut":
            if direction == "Long":
                raw = (exit_price - entry_price) / entry_price
            else:
                raw = (entry_price - exit_price) / entry_price

        # 최종 PnL (레버리지 및 수수료 반영)
        if outcome == "💀 Liquidation":
            pnl = -1.0
        else:
            pnl = raw * leverage - fee_total

        res.append(
            {
                "Entry Time": entry_time,
                "Entry Price": entry_price,
                "Exit Time": times[exit_idx],
                "Exit Price": exit_price,
                "Outcome": outcome,
                "Direction": direction,
                "Regime": entry_regime,
                "PnL": pnl,
            }
        )

    return pd.DataFrame(res)


def summarize_trades(trades_df: pd.DataFrame) -> dict:
    """
    공통 트레이드 요약 함수.
    - trades_df 는 최소한 'PnL' 또는 'pnl_%' 컬럼을 가지고 있다고 가정합니다.
    - μ 전략(trades['pnl_%']) / run_backtest(trades['PnL']) 둘 다 지원합니다.
    """
    if trades_df is None or trades_df.empty:
        return {
            "n_trades": 0,
            "win_rate": float("nan"),
            "avg_pnl": float("nan"),
            "total_pnl": float("nan"),
        }

    n_trades = len(trades_df)

    # 어떤 컬럼을 쓸지 결정 (μ 전략: 'pnl_%', 8전략 엔진: 'PnL')
    if "pnl_%" in trades_df.columns:
        pnl_series = trades_df["pnl_%"]
        wins = trades_df[trades_df["pnl_%"] > 0]
        is_percent = True
    elif "PnL" in trades_df.columns:
        pnl_series = trades_df["PnL"]
        wins = trades_df[trades_df["PnL"] > 0]
        is_percent = False
    else:
        return {
            "n_trades": n_trades,
            "win_rate": float("nan"),
            "avg_pnl": float("nan"),
            "total_pnl": float("nan"),
        }

    win_rate = len(wins) / n_trades * 100.0
    avg_pnl = pnl_series.mean()

    if is_percent:
        # % 단위 (예: 2 → 2%) → 배수 (1.02)
        total_pnl = (pnl_series / 100 + 1).prod() - 1
    else:
        # 이미 수익률(배수 - 1)이라고 가정 (예: 0.03 → 3%)
        total_pnl = (pnl_series + 1).prod() - 1

    return {
        "n_trades": n_trades,
        "win_rate": win_rate,
        "avg_pnl": avg_pnl,
        "total_pnl": total_pnl * 100,  # %로 반환
    }