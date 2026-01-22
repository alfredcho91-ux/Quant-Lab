# strategy/combo_filter/logic.py
"""Combo Filter Strategy Logic"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

from core.indicators import compute_rsi


def add_combo_indicators(df: pd.DataFrame, sma_short: int, sma_long: int) -> pd.DataFrame:
    """Add indicators for combo filter - matching original Streamlit."""
    df = df.copy()
    close = df["close"]
    
    # SMA
    df[f"SMA{sma_short}"] = close.rolling(window=sma_short, min_periods=sma_short).mean()
    df[f"SMA{sma_long}"] = close.rolling(window=sma_long, min_periods=sma_long).mean()
    
    # BB
    mid = close.rolling(window=20, min_periods=20).mean()
    std = close.rolling(window=20, min_periods=20).std()
    df["BB_mid"] = mid
    df["BB_upper"] = mid + 2.0 * std
    df["BB_lower"] = mid - 2.0 * std
    df["RSI"] = compute_rsi(close, length=14)
    
    # Candle features
    df = _add_candle_features(df)
    
    return df


def _add_candle_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add candle features for pattern detection."""
    df = df.copy()
    df["is_bull"] = df["close"] > df["open"]
    df["is_bear"] = df["close"] < df["open"]
    df["body"] = (df["close"] - df["open"]).abs()
    df["range"] = df["high"] - df["low"]
    df["body_rel_range"] = df["body"] / df["range"].replace(0, 1e-8)
    df["body_top"] = df[["open", "close"]].max(axis=1)
    df["body_bottom"] = df[["open", "close"]].min(axis=1)
    return df


def build_ma_filter(df: pd.DataFrame, mode: str, sma_short: int, sma_long: int) -> pd.Series:
    """Build MA cross filter mask."""
    s = df[f"SMA{sma_short}"]
    l = df[f"SMA{sma_long}"]
    prev_s, prev_l = s.shift(1), l.shift(1)
    if mode == "golden":
        cross = (prev_s <= prev_l) & (s > l)
    else:
        cross = (prev_s >= prev_l) & (s < l)
    return cross.fillna(False)


def build_bb_filter(df: pd.DataFrame, mode: str, max_bars: int = 7) -> pd.Series:
    """Build BB filter mask."""
    low, high = df["low"], df["high"]
    # 터치 기준 (관통이 아닌 터치)
    touch_lower = low <= df["BB_lower"]
    touch_upper = high >= df["BB_upper"]
    touch_mid = (low <= df["BB_mid"]) & (df["BB_mid"] <= high)
    
    if mode == "lower_touch":
        touch_series = touch_lower.astype(int)
        first_touch = (touch_series.shift(1, fill_value=0) == 0) & (touch_series == 1)
        return first_touch.fillna(False)
    if mode == "upper_touch":
        touch_series = touch_upper.astype(int)
        first_touch = (touch_series.shift(1, fill_value=0) == 0) & (touch_series == 1)
        return first_touch.fillna(False)
    
    # mid_reversion (mid_touch)
    touch_combined = touch_lower | touch_upper
    touch_series = touch_combined.astype(int)
    first_touch = (touch_series.shift(1, fill_value=0) == 0) & (touch_series == 1)
    
    event_idx = df.index[first_touch]
    if len(event_idx) == 0:
        return pd.Series(False, index=df.index)
    
    pos_idx = df.index.get_indexer(event_idx)
    touch_mid_vals = touch_mid.values
    ok_flags = np.zeros(len(df), dtype=bool)
    max_i = len(df) - 1
    
    for i in pos_idx:
        start, end = i + 1, i + max_bars
        if start > max_i:
            continue
        end = min(end, max_i)
        if start > end:
            continue
        if np.any(touch_mid_vals[start:end + 1]):
            ok_flags[i] = True
    
    return pd.Series(ok_flags, index=df.index)


def build_pattern_filter(df: pd.DataFrame, pattern_key: str) -> pd.Series:
    """Full pattern detection matching original Streamlit (13 patterns)."""
    mask = pd.Series(False, index=df.index)
    
    if "body_top" not in df.columns:
        df = _add_candle_features(df)
    
    prev = df.shift(1)
    prev2 = df.shift(2)
    
    prev_top = prev[["open", "close"]].max(axis=1)
    prev_bot = prev[["open", "close"]].min(axis=1)
    curr_top = df[["open", "close"]].max(axis=1)
    curr_bot = df[["open", "close"]].min(axis=1)
    
    engulf_cond = (curr_top >= prev_top) & (curr_bot <= prev_bot)
    inside_cond = (curr_top <= prev_top) & (curr_bot >= prev_bot)
    
    if pattern_key == "Bullish Engulfing":
        mask = prev["is_bear"] & df["is_bull"] & engulf_cond
    elif pattern_key == "Bearish Engulfing":
        mask = prev["is_bull"] & df["is_bear"] & engulf_cond
    elif pattern_key == "Bullish Harami":
        mask = prev["is_bear"] & df["is_bull"] & inside_cond
    elif pattern_key == "Bearish Harami":
        mask = prev["is_bull"] & df["is_bear"] & inside_cond
    elif pattern_key == "Three Inside Up":
        c1_red = prev2["is_bear"]
        c2_green = prev["is_bull"]
        c1_top = prev2[["open", "close"]].max(axis=1)
        c1_bot = prev2[["open", "close"]].min(axis=1)
        c2_top = prev[["open", "close"]].max(axis=1)
        c2_bot = prev[["open", "close"]].min(axis=1)
        inside_c2 = (c2_top <= c1_top) & (c2_bot >= c1_bot)
        confirm = df["is_bull"] & (df["close"] > prev["close"])
        mask = c1_red & c2_green & inside_c2 & confirm
    elif pattern_key == "Hammer":
        lower_wick = df["body_bottom"] - df["low"] if "body_bottom" in df.columns else df[["open", "close"]].min(axis=1) - df["low"]
        upper_wick = df["high"] - df["body_top"] if "body_top" in df.columns else df["high"] - df[["open", "close"]].max(axis=1)
        mask = df["is_bull"] & (lower_wick >= 2.0 * df["body"]) & (upper_wick <= 0.5 * df["body"])
    elif pattern_key == "Hanging Man":
        body_rel = df["body_rel_range"] if "body_rel_range" in df.columns else df["body"] / df["range"]
        lower_wick = df["body_bottom"] - df["low"] if "body_bottom" in df.columns else df[["open", "close"]].min(axis=1) - df["low"]
        upper_wick = df["high"] - df["body_top"] if "body_top" in df.columns else df["high"] - df[["open", "close"]].max(axis=1)
        mask = (body_rel <= 0.4) & (lower_wick >= 2.0 * df["body"]) & (upper_wick <= 0.5 * df["body"])
    elif pattern_key == "Doji (bullish)":
        body_rel = df["body_rel_range"] if "body_rel_range" in df.columns else df["body"] / df["range"]
        mask = body_rel <= 0.1
    elif pattern_key == "Morning Star":
        c1_red = prev2["is_bear"]
        small_body = (prev["close"] - prev["open"]).abs() / (prev["high"] - prev["low"]).replace(0, 1e-8) <= 0.4
        c1_mid = (prev2["open"] + prev2["close"]) / 2.0
        c3_above_mid = df["close"] >= c1_mid
        mask = c1_red & small_body & df["is_bull"] & c3_above_mid
    elif pattern_key == "Evening Star":
        c1_green = prev2["is_bull"]
        small_body = (prev["close"] - prev["open"]).abs() / (prev["high"] - prev["low"]).replace(0, 1e-8) <= 0.4
        c1_mid = (prev2["open"] + prev2["close"]) / 2.0
        c3_below_mid = df["close"] <= c1_mid
        mask = c1_green & small_body & df["is_bear"] & c3_below_mid
    elif pattern_key == "Three White Soldiers":
        bull0, bull1, bull2 = df["is_bull"], prev["is_bull"], prev2["is_bull"]
        cond_up = (df["close"] > prev["close"]) & (prev["close"] > prev2["close"])
        mask = bull0 & bull1 & bull2 & cond_up
    elif pattern_key == "Three Black Crows":
        bear0, bear1, bear2 = df["is_bear"], prev["is_bear"], prev2["is_bear"]
        cond_down = (df["close"] < prev["close"]) & (prev["close"] < prev2["close"])
        mask = bear0 & bear1 & bear2 & cond_down
    elif pattern_key == "Shooting Star":
        body_rel = df["body_rel_range"] if "body_rel_range" in df.columns else df["body"] / df["range"]
        upper_wick = df["high"] - df["body_top"] if "body_top" in df.columns else df["high"] - df[["open", "close"]].max(axis=1)
        lower_wick = df["body_bottom"] - df["low"] if "body_bottom" in df.columns else df[["open", "close"]].min(axis=1) - df["low"]
        mask = (body_rel <= 0.4) & (upper_wick >= 2.0 * df["body"]) & (lower_wick <= 0.5 * df["body"])
    
    return mask.fillna(False)


def run_tp_backtest(df: pd.DataFrame, event_mask: pd.Series, tp_pct: float, horizon: int, direction: str) -> Dict[str, Any]:
    """TP-only backtest - Look-ahead Bias 제거 버전.
    
    핵심 변경:
    - 시그널 봉 T의 종가에서 시그널 발생
    - 실제 진입은 봉 T+1의 시가에서 수행 (실제 트레이딩과 동일)
    """
    event_mask = event_mask.reindex(df.index).fillna(False)
    if not event_mask.any():
        return {"events": 0, "tp_hits": 0, "no_tp": 0, "hit_rate": None, "avg_ret": None}
    
    opens = df["open"].values
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    idx_events = np.where(event_mask.values)[0]
    max_i = len(df) - 1
    
    tp_hits, no_tp = 0, 0
    rets = []
    
    for i in idx_events:
        entry_bar = i + 1
        if entry_bar > max_i:
            continue
        
        entry = opens[entry_bar]
        if not np.isfinite(entry) or entry <= 0:
            continue
        
        start, end = entry_bar, entry_bar + horizon
        if start > max_i:
            continue
        end = min(end, max_i)
        if start > end:
            continue
        
        last_close = closes[end]
        
        if direction == "short":
            tp_price = entry * (1 - tp_pct)
            seg_low = lows[start:end + 1]
            hit_tp = np.any(seg_low <= tp_price)
            if hit_tp:
                tp_hits += 1
                rets.append((entry - tp_price) / entry * 100.0)
            else:
                no_tp += 1
                rets.append((entry - last_close) / entry * 100.0)
        else:
            tp_price = entry * (1 + tp_pct)
            seg_high = highs[start:end + 1]
            hit_tp = np.any(seg_high >= tp_price)
            if hit_tp:
                tp_hits += 1
                rets.append((tp_price - entry) / entry * 100.0)
            else:
                no_tp += 1
                rets.append((last_close - entry) / entry * 100.0)
    
    events = tp_hits + no_tp
    hit_rate = tp_hits / events * 100.0 if events > 0 else None
    avg_ret = float(np.mean(rets)) if rets else None
    
    return {"events": events, "tp_hits": tp_hits, "no_tp": no_tp, "hit_rate": hit_rate, "avg_ret": avg_ret}


def analyze_combo_filter(params: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """Main entry point for combo filter analysis."""
    df = add_combo_indicators(df, params.get("sma_short", 5), params.get("sma_long", 20))
    
    # Build filter mask
    mask = pd.Series(True, index=df.index)
    
    for ftype, fparams in [
        (params.get("filter1_type", "none"), params.get("filter1_params", {})),
        (params.get("filter2_type", "none"), params.get("filter2_params", {})),
        (params.get("filter3_type", "none"), params.get("filter3_params", {})),
    ]:
        if ftype == "ma_cross":
            mode = fparams.get("ma_mode", "golden")
            fmask = build_ma_filter(df, mode, params.get("sma_short", 5), params.get("sma_long", 20))
            mask &= fmask
        elif ftype == "bb":
            mode = fparams.get("bb_mode", "lower_touch")
            fmask = build_bb_filter(df, mode, params.get("horizon", 5))
            mask &= fmask
        elif ftype == "pattern":
            pkey = fparams.get("pattern_key", "")
            if pkey:
                fmask = build_pattern_filter(df, pkey)
                mask &= fmask
    
    # RSI filter
    rsi_mask = df["RSI"].between(params.get("rsi_min", 40), params.get("rsi_max", 60))
    mask &= rsi_mask
    
    if not mask.any():
        return {"events": 0, "tp_hits": 0, "no_tp": 0, "hit_rate": None, "avg_ret": None}
    
    # Run backtest
    tp_ratio = params.get("tp_pct", 1.0) / 100.0
    stats = run_tp_backtest(df, mask, tp_ratio, params.get("horizon", 5), params.get("direction", "long"))
    
    return stats
