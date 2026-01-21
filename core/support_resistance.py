# core/support_resistance.py
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional


def detect_swings(df: pd.DataFrame, lookback: int = 3) -> pd.DataFrame:
    """
    스윙 고점/저점 탐지 (Look-ahead Bias 제거 버전).
    
    핵심 원리:
    - 시간 T의 스윙 포인트는 T + lookback 시점에서만 확인 가능
    - 즉, 시그널은 lookback 봉 후에 "확정"됨
    - 실시간 트레이딩과 동일하게 작동
    
    예시 (lookback=3):
    - 봉 10이 스윙 고점인지 확인하려면 봉 11, 12, 13이 필요
    - 따라서 봉 13이 끝난 후에야 "봉 10은 스윙 고점"이라고 알 수 있음
    - swing_high[13] = True (봉 10의 정보가 봉 13에서 확정)
    """
    df = df.copy()
    n = len(df)
    if n == 0:
        df["swing_high"] = False
        df["swing_low"] = False
        df["swing_high_price"] = np.nan
        df["swing_low_price"] = np.nan
        return df

    highs = df["high"].values
    lows = df["low"].values

    swing_high = np.zeros(n, dtype=bool)
    swing_low = np.zeros(n, dtype=bool)
    swing_high_price = np.full(n, np.nan)
    swing_low_price = np.full(n, np.nan)

    # 과거 데이터만 사용하여 스윙 포인트 탐지
    # 봉 i에서 확인: 봉 (i - 2*lookback) ~ (i - lookback) 구간의 스윙
    for i in range(2 * lookback, n):
        # 확인할 후보 봉: i - lookback (이 봉이 스윙인지 확인)
        candidate_idx = i - lookback
        
        # 왼쪽 구간: candidate_idx - lookback ~ candidate_idx
        # 오른쪽 구간: candidate_idx ~ candidate_idx + lookback (= i)
        left_start = candidate_idx - lookback
        left_end = candidate_idx + 1
        right_start = candidate_idx
        right_end = i + 1  # candidate_idx + lookback + 1
        
        # Swing High 확인 (좌우 lookback 봉 중 가장 높은지)
        left_max = highs[left_start:left_end].max()
        right_max = highs[right_start:right_end].max()
        
        if highs[candidate_idx] >= left_max and highs[candidate_idx] >= right_max:
            # 스윙 고점이 확정됨 - 현재 봉 i에서 시그널 발생
            swing_high[i] = True
            swing_high_price[i] = highs[candidate_idx]
        
        # Swing Low 확인
        left_min = lows[left_start:left_end].min()
        right_min = lows[right_start:right_end].min()
        
        if lows[candidate_idx] <= left_min and lows[candidate_idx] <= right_min:
            swing_low[i] = True
            swing_low_price[i] = lows[candidate_idx]

    df["swing_high"] = swing_high
    df["swing_low"] = swing_low
    df["swing_high_price"] = swing_high_price  # 확정된 스윙 고점의 실제 가격
    df["swing_low_price"] = swing_low_price    # 확정된 스윙 저점의 실제 가격
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
    
    수정됨: Look-ahead bias가 제거된 detect_swings와 호환
    - swing_high_price: 확정된 스윙 고점의 실제 가격
    - swing_low_price: 확정된 스윙 저점의 실제 가격
    """
    if "swing_high" not in df.columns or "swing_low" not in df.columns:
        df = detect_swings(df, lookback=lookback)

    # 새 버전: swing_high_price/swing_low_price 사용
    if "swing_high_price" in df.columns:
        highs = df.loc[df["swing_high"], "swing_high_price"].dropna().values
    else:
        # 구버전 호환
        highs = df.loc[df["swing_high"], "high"].values
    
    if "swing_low_price" in df.columns:
        lows = df.loc[df["swing_low"], "swing_low_price"].dropna().values
    else:
        # 구버전 호환
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