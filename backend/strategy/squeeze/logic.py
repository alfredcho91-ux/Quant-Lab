# strategy/squeeze/logic.py
"""Multi-TF Squeeze Strategy Logic"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

import sys
from pathlib import Path
backend_path = str(Path(__file__).parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from core.indicators import compute_rsi

# Timeframe to minutes mapping
TIMEFRAME_TO_MINUTES = {
    "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "1h": 60,
    "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720, "1d": 1440,
}


def calc_bbands_df(df: pd.DataFrame, length: int = 20, std_mult: float = 2.0) -> pd.DataFrame:
    """Calculate Bollinger Bands."""
    df = df.copy()
    close = df["close"]
    mid = close.rolling(window=length, min_periods=length).mean()
    std = close.rolling(window=length, min_periods=length).std(ddof=0)
    df["bb_mid"] = mid
    df["bb_upper"] = mid + std_mult * std
    df["bb_lower"] = mid - std_mult * std
    df["bb_width_pct"] = (df["bb_upper"] - df["bb_lower"]) / close
    return df


def add_squeeze_indicators(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Add squeeze-related indicators to DataFrame."""
    df = df.copy()
    
    # Handle datetime
    if "open_time" in df.columns:
        last_ts = df["open_time"].iloc[-1]
        unit = "us" if last_ts > 1e14 else "ms"
        df["open_dt"] = pd.to_datetime(df["open_time"], unit=unit)
    elif not np.issubdtype(df.index.dtype, np.datetime64):
        df["open_dt"] = pd.to_datetime(df.index)
    else:
        df["open_dt"] = df.index
    
    df = df.sort_values("open_dt").reset_index(drop=True)
    df = calc_bbands_df(df)
    df["rsi14"] = compute_rsi(df["close"], length=14)
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    
    minutes = TIMEFRAME_TO_MINUTES.get(tf, 60)
    df["close_dt"] = df["open_dt"] + pd.Timedelta(minutes=minutes)
    
    return df


def find_squeeze_breakouts(df: pd.DataFrame, squeeze_thr: float = 0.02) -> pd.DataFrame:
    """Find squeeze breakout events."""
    if "bb_width_pct" not in df.columns:
        return pd.DataFrame()
    
    cond_sq = df["bb_width_pct"] <= squeeze_thr
    is_sq = cond_sq.astype(int)
    if is_sq.sum() == 0:
        return pd.DataFrame()
    
    diff = is_sq.diff().fillna(0).to_numpy()
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0] - 1
    
    if is_sq.iloc[0] == 1:
        starts = np.r_[0, starts]
    if is_sq.iloc[-1] == 1:
        ends = np.r_[ends, len(is_sq) - 1]
    
    events = []
    for s, e in zip(starts, ends):
        j = e + 1
        while j < len(df) and df["bb_width_pct"].iloc[j] <= squeeze_thr:
            j += 1
        if j >= len(df):
            continue
        
        break_idx = j
        squeeze_close = df["close"].iloc[e]
        break_close = df["close"].iloc[break_idx]
        direction = "up" if break_close > squeeze_close else "down"
        immediate_ret = (break_close - squeeze_close) / squeeze_close
        
        events.append({
            "squeeze_end_time": df["open_dt"].iloc[e],
            "break_time": df["open_dt"].iloc[break_idx],
            "direction": direction,
            "immediate_ret": immediate_ret,
        })
    
    return pd.DataFrame(events)


def analyze_multi_tf_squeeze(
    high_df: pd.DataFrame,
    low_df: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Main entry point for multi-TF squeeze analysis."""
    high_tf = params.get("high_tf", "2h")
    low_tf = params.get("low_tf", "15m")
    squeeze_thr_high = params.get("squeeze_thr_high", 0.02)
    squeeze_thr_low = params.get("squeeze_thr_low", 0.02)
    lower_lookback_bars = params.get("lower_lookback_bars", 2)
    rsi_min = params.get("rsi_min", 40)
    rsi_max = params.get("rsi_max", 60)
    require_above_mid = params.get("require_above_mid", True)
    
    high_df = add_squeeze_indicators(high_df, high_tf)
    low_df = add_squeeze_indicators(low_df, low_tf)
    
    # Find squeeze breakouts in high TF
    events = find_squeeze_breakouts(high_df, squeeze_thr_high)
    if events.empty:
        return {"events": [], "stats": {}}
    
    # Summarize lower TF state before each breakout
    minutes_low = TIMEFRAME_TO_MINUTES.get(low_tf, 60)
    lookback_window = pd.Timedelta(minutes=minutes_low * lower_lookback_bars)
    
    records = []
    for _, ev in events.iterrows():
        break_time = ev["break_time"]
        mask = (low_df["close_dt"] <= break_time) & (low_df["close_dt"] > break_time - lookback_window)
        seg = low_df.loc[mask]
        
        if seg.empty:
            continue
        
        last = seg.iloc[-1]
        lt_rsi_last = float(last["rsi14"]) if pd.notna(last["rsi14"]) else 50
        lt_above_mid = bool(last["close"] > last["bb_mid"]) if pd.notna(last["bb_mid"]) else False
        lt_above_ema20 = bool(last["close"] > last["ema20"]) if pd.notna(last["ema20"]) else False
        
        lt_rsi_mean = float(seg["rsi14"].mean()) if len(seg) > 0 else np.nan
        
        width = last["bb_upper"] - last["bb_lower"]
        if width != 0 and np.isfinite(width):
            lt_pos_band = float((last["close"] - last["bb_lower"]) / width)
        else:
            lt_pos_band = np.nan
        
        cond_sq_low = seg["bb_width_pct"] <= squeeze_thr_low
        lt_squeeze_any = bool(cond_sq_low.any())
        lt_squeeze_ratio = float(cond_sq_low.mean()) if len(seg) > 0 else np.nan
        
        records.append({
            "break_time": str(ev["break_time"]),
            "direction": ev["direction"],
            "immediate_ret": float(ev["immediate_ret"]) * 100,
            "lt_n_bars": len(seg),
            "lt_rsi_last": lt_rsi_last,
            "lt_rsi_mean": lt_rsi_mean,
            "lt_pos_band": lt_pos_band,
            "lt_above_mid": lt_above_mid,
            "lt_above_ema20": lt_above_ema20,
            "lt_squeeze_any": lt_squeeze_any,
            "lt_squeeze_ratio": lt_squeeze_ratio,
        })
    
    df_all = pd.DataFrame(records)
    
    # Apply filters
    if not df_all.empty:
        df_filtered = df_all[df_all["lt_rsi_last"].between(rsi_min, rsi_max)]
        if require_above_mid:
            df_filtered = df_filtered[df_filtered["lt_above_mid"] == True]
    else:
        df_filtered = df_all
    
    # Calculate stats
    total = len(df_all)
    filtered = len(df_filtered)
    
    stats = {"total_events": total, "filtered_events": filtered}
    if filtered > 0:
        up_df = df_filtered[df_filtered["direction"] == "up"]
        down_df = df_filtered[df_filtered["direction"] == "down"]
        stats["p_up"] = len(up_df) / filtered * 100
        stats["p_down"] = len(down_df) / filtered * 100
        stats["n_up"] = len(up_df)
        stats["n_down"] = len(down_df)
        stats["avg_ret_up"] = float(up_df["immediate_ret"].mean()) if len(up_df) > 0 else None
        stats["avg_ret_down"] = float(down_df["immediate_ret"].mean()) if len(down_df) > 0 else None
    
    return {
        "events": df_filtered.to_dict(orient="records") if not df_filtered.empty else [],
        "stats": stats,
    }
