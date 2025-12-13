# core/mtf_touch_stats.py

import numpy as np
import pandas as pd
from typing import List, Tuple, Literal


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    DatetimeIndex 가 없으면 가능한 경우 컬럼을 이용해 생성합니다.

    - 이미 DatetimeIndex 이면 정렬만 수행
    - 'datetime' 컬럼이 있으면 그걸 인덱스로 사용
    - 'open_time' 컬럼이 있으면 ms/us 혼합 타임스탬프로 가정하고 변환
    - 위가 모두 아니면 ValueError

    NOTE:
      - open_time 이 정수형(ms/us)일 때를 기준으로 합니다.
      - 만약 다른 형식이면, 이 부분만 고객님 데이터 스펙에 맞게 수정하셔야 합니다.
    """
    if isinstance(df.index, pd.DatetimeIndex):
        out = df.copy()
        out = out.sort_index()
        return out

    df = df.copy()

    # 1) datetime 컬럼 사용
    if "datetime" in df.columns:
        if not np.issubdtype(df["datetime"].dtype, np.datetime64):
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"])
        df = df.sort_values("datetime")
        df = df.set_index("datetime")
        return df

    # 2) open_time 컬럼 사용 (ms/us 혼합 가정)
    if "open_time" in df.columns:
        col = df["open_time"]

        # 이미 datetime이면 그대로 사용
        if np.issubdtype(col.dtype, np.datetime64):
            df = df.sort_values("open_time")
            df = df.set_index("open_time")
            return df

        # 정수형으로 가정하고 ms/us 추정
        ts = col.astype("int64").values
        # 1e14 이상이면 us, 아니면 ms 로 가정
        is_us = ts > 1_000_000_000_000_00  # 1e14
        ts_us = np.where(is_us, ts, ts * 1000)

        dt = pd.to_datetime(ts_us, unit="us")
        df["datetime"] = dt
        df = df.sort_values("datetime")
        df = df.set_index("datetime")
        return df

    raise ValueError(
        "DataFrame 에 DatetimeIndex, 'datetime', 'open_time' 중 하나는 필요합니다."
    )


def add_sma(df: pd.DataFrame, windows: List[int]) -> pd.DataFrame:
    """
    주어진 윈도우 리스트에 대해 close 기준 SMA 추가.
    """
    if "close" not in df.columns:
        raise ValueError("add_sma: 'close' 컬럼이 필요합니다.")

    df = df.copy()
    for w in windows:
        col = f"SMA{w}"
        if col not in df.columns:
            df[col] = df["close"].rolling(window=w, min_periods=w).mean()
    return df


def find_cross_indices(
    df: pd.DataFrame,
    short_len: int,
    long_len: int,
    mode: Literal["golden", "dead"] = "golden",
) -> np.ndarray:
    """
    단기 SMA(short_len), 장기 SMA(long_len)에 대해
    골든/데드크로스 발생 인덱스를 반환.

    골든: 이전 s <= l, 현재 s > l
    데드 : 이전 s >= l, 현재 s < l
    """
    s_col = f"SMA{short_len}"
    l_col = f"SMA{long_len}"

    if s_col not in df.columns or l_col not in df.columns:
        raise ValueError(f"find_cross_indices: {s_col}, {l_col} 이 df에 없습니다.")

    s = df[s_col]
    l = df[l_col]

    prev_s = s.shift(1)
    prev_l = l.shift(1)

    if mode == "golden":
        cond_prev = prev_s <= prev_l
        cond_now = s > l
    else:  # "dead"
        cond_prev = prev_s >= prev_l
        cond_now = s < l

    cross = cond_prev & cond_now
    cross = cross & s.notna() & l.notna() & prev_s.notna() & prev_l.notna()

    return np.where(cross.values)[0]


def map_higher_sma20_to_lower(
    lower_df: pd.DataFrame,
    higher_df: pd.DataFrame,
    sma_len: int = 20,
) -> pd.Series:
    """
    상위 타임프레임의 SMA(sma_len)을
    하위 타임프레임의 타임라인으로 매핑하여,
    각 하위봉 시점에서의 상위 SMA 값을 반환.

    - higher_df의 index: datetime (상위 TF)
    - lower_df의 index : datetime (하위 TF)
    """
    col = f"SMA{sma_len}"
    if col not in higher_df.columns:
        raise ValueError(f"higher_df에 {col} 컬럼이 없습니다. 먼저 add_sma를 호출해야 합니다.")

    higher_sma = higher_df[col]
    mapped = higher_sma.reindex(lower_df.index, method="ffill")
    return mapped


def compute_touch_stats(
    lower_df: pd.DataFrame,
    higher_sma_on_lower: pd.Series,
    cross_indices: np.ndarray,
    n_bars: int = 8,
) -> Tuple[int, int, float]:
    """
    하위 TF에서 발생한 크로스(cross_indices)를 기준으로,
    각 이벤트 이후 n_bars개의 하위봉 안에 상위 SMA를 터치할 확률 계산.

    터치 정의:
      - 해당 구간의 어떤 캔들이라도
        low <= 상위_sma <= high 를 만족하면 터치 성공.

    반환:
      (성공 개수, 유효 이벤트 수, 확률 %)
    """
    required = {"low", "high"}
    missing = required - set(lower_df.columns)
    if missing:
        raise ValueError(f"compute_touch_stats: lower_df에 {missing} 컬럼이 없습니다.")

    lows = lower_df["low"].values
    highs = lower_df["high"].values
    higher_vals = higher_sma_on_lower.values

    total = 0
    success = 0

    max_idx = len(lower_df) - 1

    for idx in cross_indices:
        # 이후 n_bars 캔들 범위 [idx+1, idx+n_bars]
        start = idx + 1
        end = idx + n_bars

        if start > max_idx:
            continue
        if end > max_idx:
            end = max_idx
        if start > end:
            continue

        total += 1

        seg_lows = lows[start : end + 1]
        seg_highs = highs[start : end + 1]
        seg_sma = higher_vals[start : end + 1]

        # low <= sma <= high 인 캔들이 하나라도 있으면 성공
        touched = np.any((seg_lows <= seg_sma) & (seg_sma <= seg_highs))
        if touched:
            success += 1

    prob = success / total * 100.0 if total > 0 else float("nan")
    return success, total, prob


def run_pair_touch_stats_df(
    lower_df: pd.DataFrame,
    higher_df: pd.DataFrame,
    n_bars: int = 8,
    short_len: int = 5,
    long_len: int = 20,
) -> pd.DataFrame:
    """
    (하위 TF df, 상위 TF df) 에 대해
    - 골든크로스(Golden)
    - 데드크로스(Dead)
    각각
      → n_bars개 하위봉 안에 상위 TF SMA(long_len)을 터치할 확률 계산.

    lower_df / higher_df 는 같은 심볼에 대한 서로 다른 타임프레임이라고 가정합니다.
    open/high/low/close 컬럼이 있어야 하며,
    DatetimeIndex 또는 'datetime' / 'open_time' 컬럼 중 하나는 반드시 있어야 합니다.
    """
    # 인덱스를 datetime 으로 정리
    lower = _ensure_datetime_index(lower_df)
    higher = _ensure_datetime_index(higher_df)

    # OHLC 컬럼 체크
    needed = {"open", "high", "low", "close"}
    for name, df in [("lower_df", lower), ("higher_df", higher)]:
        missing = needed - set(df.columns)
        if missing:
            raise ValueError(f"{name} 에 필수 컬럼 누락: {missing}")

    # SMA 계산
    lower = add_sma(lower, [short_len, long_len])
    higher = add_sma(higher, [long_len])

    # 상위 TF SMA(long_len) 을 하위 타임라인으로 매핑
    higher_on_lower = map_higher_sma20_to_lower(lower, higher, sma_len=long_len)

    # 골든 / 데드 크로스 인덱스
    gc_idx = find_cross_indices(lower, short_len, long_len, mode="golden")
    dc_idx = find_cross_indices(lower, short_len, long_len, mode="dead")

    # 터치 통계 계산
    gc_succ, gc_total, gc_prob = compute_touch_stats(
        lower, higher_on_lower, gc_idx, n_bars=n_bars
    )
    dc_succ, dc_total, dc_prob = compute_touch_stats(
        lower, higher_on_lower, dc_idx, n_bars=n_bars
    )

    rows = [
        {
            "Cross_Type": "Golden",
            "Short_MA": short_len,
            "Long_MA": long_len,
            "Events": gc_total,
            "Success": gc_succ,
            "Prob_%": gc_prob,
        },
        {
            "Cross_Type": "Dead",
            "Short_MA": short_len,
            "Long_MA": long_len,
            "Events": dc_total,
            "Success": dc_succ,
            "Prob_%": dc_prob,
        },
    ]

    return pd.DataFrame(rows)