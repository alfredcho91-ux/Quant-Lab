# core/support_resistance.py
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional


def detect_swings(df: pd.DataFrame, lookback: int = 3) -> pd.DataFrame:
    """
    스윙 고점/저점 탐지 (A안).
    lookback 봉 수 기준으로 좌우보다 높으면 swing_high, 낮으면 swing_low.
    """
    df = df.copy()
    n = len(df)
    if n == 0:
        df["swing_high"] = False
        df["swing_low"] = False
        return df

    highs = df["high"].values
    lows = df["low"].values

    swing_high = np.zeros(n, dtype=bool)
    swing_low = np.zeros(n, dtype=bool)

    for i in range(lookback, n - lookback):
        left_h = highs[i - lookback : i + 1].max()
        right_h = highs[i : i + lookback + 1].max()
        if highs[i] >= left_h and highs[i] >= right_h:
            swing_high[i] = True

        left_l = lows[i - lookback : i + 1].min()
        right_l = lows[i : i + lookback + 1].min()
        if lows[i] <= left_l and lows[i] <= right_l:
            swing_low[i] = True

    df["swing_high"] = swing_high
    df["swing_low"] = swing_low
    return df


def _cluster_prices(prices: np.ndarray, tolerance_pct: float):
    """
    가격들을 정렬 후, tolerance_pct 비율 안에 들어오는 것끼리 클러스터링.
    예: tolerance_pct = 0.003 → ±0.3% 이내면 같은 레벨로 본다.
    """
    prices = np.asarray(prices, dtype=float)
    prices = prices[~np.isnan(prices)]
    if prices.size == 0:
        return []

    prices = np.sort(prices)
    clusters = []
    current = [prices[0]]

    for p in prices[1:]:
        if abs(p - current[-1]) / current[-1] <= tolerance_pct:
            current.append(p)
        else:
            clusters.append((np.mean(current), len(current)))
            current = [p]

    if current:
        clusters.append((np.mean(current), len(current)))

    return clusters


def build_sr_levels_from_swings(
    df: pd.DataFrame,
    lookback: int = 3,
    tolerance_pct: float = 0.003,   # 0.3 %
    min_touches: int = 2,
    timeframe_label: str = "main",
) -> pd.DataFrame:
    """
    스윙 포인트(A)를 이용해 지지/저항 레벨 생성.
    반환: columns = [price, touches, kind, timeframe, source]
    """
    if "swing_high" not in df.columns or "swing_low" not in df.columns:
        df = detect_swings(df, lookback=lookback)

    highs = df.loc[df["swing_high"], "high"].values
    lows = df.loc[df["swing_low"], "low"].values

    hi_clusters = _cluster_prices(highs, tolerance_pct)
    lo_clusters = _cluster_prices(lows, tolerance_pct)

    records = []

    for price, touches in hi_clusters:
        if touches >= min_touches:
            records.append(
                {
                    "price": float(price),
                    "touches": int(touches),
                    "kind": "resistance",
                    "timeframe": timeframe_label,
                    "source": "swing",
                    "label": "",
                }
            )

    for price, touches in lo_clusters:
        if touches >= min_touches:
            records.append(
                {
                    "price": float(price),
                    "touches": int(touches),
                    "kind": "support",
                    "timeframe": timeframe_label,
                    "source": "swing",
                    "label": "",
                }
            )

    return pd.DataFrame(records)


# ───────── B. Pivot Points (일봉 피벗) ─────────
def compute_daily_pivots(df: pd.DataFrame, last_n: int = 3) -> pd.DataFrame:
    """
    B안: 일봉 기준 Pivot / R1 / R2 / S1 / S2 계산.
    last_n: 최근 며칠 것만 레벨로 만들지.
    반환: price, kind='pivot', timeframe='1D', source='pivot', label (P/R1/...)
    """
    if "open_dt" not in df.columns:
        return pd.DataFrame(columns=["price", "kind", "timeframe", "source", "label"])

    tmp = df.set_index("open_dt").sort_index()
    daily = tmp[["open", "high", "low", "close"]].resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    )
    daily = daily.dropna()

    records = []
    for ts, row in daily.tail(last_n).iterrows():
        H = float(row["high"])
        L = float(row["low"])
        C = float(row["close"])
        P = (H + L + C) / 3.0
        R1 = 2 * P - L
        S1 = 2 * P - H
        R2 = P + (H - L)
        S2 = P - (H - L)

        levels = [
            ("P", P),
            ("R1", R1),
            ("S1", S1),
            ("R2", R2),
            ("S2", S2),
        ]
        for label, price in levels:
            records.append(
                {
                    "price": float(price),
                    "touches": 1,
                    "kind": "pivot",
                    "timeframe": "1D",
                    "source": "pivot",
                    "label": label,
                }
            )

    return pd.DataFrame(records)


# ───────── D. 상위 타임프레임 스윙 레벨 ─────────
def _resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """
    rule: '4H', '1D' 등 pandas resample 규칙.
    """
    if "open_dt" not in df.columns:
        return pd.DataFrame(columns=df.columns)

    tmp = df.set_index("open_dt").sort_index()
    ohlc = tmp[["open", "high", "low", "close", "volume"]].resample(rule).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    ohlc = ohlc.dropna().reset_index()
    return ohlc


def compute_htf_sr_levels(
    df: pd.DataFrame,
    rule: str = "4H",              # '4H' or '1D'
    lookback: int = 3,
    tolerance_pct: float = 0.003,
    min_touches: int = 2,
) -> pd.DataFrame:
    """
    D안: 상위 타임프레임(4H, 1D 등)으로 리샘플링 후 스윙 레벨 계산.
    """
    htf = _resample_ohlc(df, rule)
    if htf.empty:
        return pd.DataFrame(columns=["price", "touches", "kind", "timeframe", "source", "label"])

    tf_label = rule
    return build_sr_levels_from_swings(
        htf,
        lookback=lookback,
        tolerance_pct=tolerance_pct,
        min_touches=min_touches,
        timeframe_label=tf_label,
    )