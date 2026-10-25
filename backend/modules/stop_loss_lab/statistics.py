"""Pure OHLC distributions. No storage/network or retrospective fit of orders."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from core.indicator_primitives import _true_range, compute_atr_wilder
from core.support_resistance import detect_swings

DAY = 86_400_000
INTERVAL_MS = {"5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": DAY, "1w": DAY * 7}


def finite(value):
    return float(value) if value is not None and math.isfinite(float(value)) else None


def describe(values, *, histogram=False):
    data = np.asarray([float(v) for v in values if finite(v) is not None], dtype=float)
    if not len(data):
        return {"count": 0, **{k: None for k in ("mean", "median", "std", "p50", "p75", "p90", "p95", "p99", "mean_median_ratio")}, "histogram": [], "ecdf": []}
    maximum = float(np.max(np.abs(data)))
    scaled = data / maximum if maximum else data
    mean = float(np.mean(scaled) * maximum)
    median = float(np.median(data))
    # Sparse 0.1-percentage-point bins; zero observations remain in bin zero.
    bins = {}
    if histogram:
        for value in data:
            scaled_bin = float(value * 10)
            near = round(scaled_bin)
            index = near if abs(scaled_bin - near) < 1e-10 else math.floor(scaled_bin)
            bins[index] = bins.get(index, 0) + 1
    unique, counts = np.unique(data, return_counts=True)
    return {
        "count": len(data), "mean": finite(mean), "median": finite(median),
        "std": finite(float(np.std(scaled, ddof=0) * maximum)),
        **{f"p{p}": finite(float(np.percentile(data, p, method="linear"))) for p in (50, 75, 90, 95, 99)},
        "mean_median_ratio": finite(mean / median) if median else None,
        "histogram": [{"lower": index / 10, "upper": (index + 1) / 10, "count": count, "share_pct": count / len(data) * 100} for index, count in sorted(bins.items())],
        "ecdf": [{"value": float(value), "probability_pct": float(count / len(data) * 100)} for value, count in zip(unique, np.cumsum(counts))] if histogram else [],
    }


def prepare(frame: pd.DataFrame, interval: str, as_of: int, lookback: int):
    if frame is None or frame.empty:
        raise ValueError(f"No {interval} market data")
    required = ["open_time", "open", "high", "low", "close"]
    if any(key not in frame for key in required):
        raise ValueError("Missing OHLC columns")
    result = frame.copy().reset_index(drop=True)
    numeric = result[required].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy()).all() or (numeric[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("Nonfinite or nonpositive OHLC")
    if result.open_time.duplicated().any() or not result.open_time.is_monotonic_increasing:
        raise ValueError("Candle timestamps must be unique and chronological")
    result[required] = numeric
    if ((result.high < result[["open", "close"]].max(axis=1)) | (result.low > result[["open", "close"]].min(axis=1))).any():
        raise ValueError("Invalid OHLC geometry")
    duration = INTERVAL_MS[interval]
    anchor = DAY * 4 if interval == "1w" else 0  # Unix Thursday -> Monday
    if ((result.open_time - anchor) % duration != 0).any():
        raise ValueError(f"{interval} timestamps do not align with UTC exchange boundaries")
    result["end_time"] = result.open_time + duration
    result = result.loc[result.end_time <= as_of].copy().reset_index(drop=True)
    if result.empty:
        raise ValueError(f"No completed {interval} candles")
    if interval in ("1d", "1w") and not (result.open_time.diff().dropna() == duration).all():
        raise ValueError(f"Reference {interval} history contains gaps; ATR must not bridge missing candles")
    if interval not in ("1d", "1w"):
        return result  # Execution paths need validated OHLC, not duplicate indicators.
    result["tr"] = _true_range(result)
    result["atr"] = compute_atr_wilder(result, length=lookback)
    result["mtr"] = result.tr.rolling(lookback, min_periods=lookback).median()
    result["upper"] = result.high - result[["open", "close"]].max(axis=1)
    result["lower"] = result[["open", "close"]].min(axis=1) - result.low
    result = detect_swings(result, lookback=3)
    result["swing_high_price"] = result.swing_high_price.ffill()
    result["swing_low_price"] = result.swing_low_price.ffill()
    return result


def contiguous(frame, interval):
    return len(frame) > 0 and bool((frame.open_time.diff().dropna() == INTERVAL_MS[interval]).all())


def snapshot(history, lookback, interval):
    if len(history) < lookback or not contiguous(history.tail(lookback), interval):
        return None
    window = history.tail(lookback)
    last = history.iloc[-1]
    if finite(last.atr) is None or finite(last.mtr) is None:
        return None
    trend = (last.close / window.iloc[0].close - 1) * 100
    ratio = last.atr / last.mtr if last.mtr > 0 else None
    return {"last": last, "window": window, "atr": float(last.atr), "mtr": float(last.mtr),
            "regime": "bull" if trend > 2 else "bear" if trend < -2 else "sideways",
            "volatility_regime": "expanding" if ratio and ratio >= 1.25 else "contracting" if ratio and ratio <= 0.8 else "normal"}


def _distribution(window):
    metrics = {}
    for key in ("upper", "lower", "tr", "atr", "mtr"):
        metrics[key] = {"price": describe(window[key]), "percent_open": describe(window[key] / window.open * 100, histogram=True)}
    metrics["atr_mtr_ratio"] = describe(window.atr / window.mtr.replace(0, np.nan))
    return {"candle_count": len(window), "metrics": metrics}


def distributions(frames, start, end):
    return {
        interval: _distribution(frame.loc[(frame.open_time >= start) & (frame.end_time <= end)])
        for interval, frame in frames.items()
    }


def weekend_distribution(daily, start, end):
    """Describe completed UTC Saturday/Sunday daily candles only."""
    window = daily.loc[(daily.open_time >= start) & (daily.end_time <= end)].copy()
    weekdays = pd.to_datetime(window.open_time, unit="ms", utc=True).dt.dayofweek
    weekend = window.loc[weekdays >= 5]
    result = _distribution(weekend)
    result.update({
        "timezone": "UTC",
        "weekdays": ["Saturday", "Sunday"],
        "day_counts": {
            "Saturday": int((weekdays == 5).sum()),
            "Sunday": int((weekdays == 6).sum()),
        },
    })
    return result


def historical_breakouts(history, side, lookback):
    """Completed reference-candle overshoot, known before the current decision."""
    extreme = history.high if side == "Short" else history.low
    previous = extreme.shift(1)
    depth = (history.high - previous) / previous * 100 if side == "Short" else (previous - history.low) / previous * 100
    return depth.loc[depth > 0].tail(lookback).tolist()
