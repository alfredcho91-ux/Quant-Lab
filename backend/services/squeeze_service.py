# services/squeeze_service.py
"""Multi-TF Squeeze analysis service"""

from typing import Dict
import pandas as pd
import numpy as np
from config.settings import TIMEFRAME_TO_MINUTES


def calc_bbands_df(df, length=20, std_mult=2.0):
    """Calculate Bollinger Bands"""
    df = df.copy()
    close = df["close"]
    mid = close.rolling(window=length, min_periods=length).mean()
    std = close.rolling(window=length, min_periods=length).std(ddof=0)
    df["bb_mid"] = mid
    df["bb_upper"] = mid + std_mult * std
    df["bb_lower"] = mid - std_mult * std
    df["bb_width_pct"] = (df["bb_upper"] - df["bb_lower"]) / close
    return df


def calc_rsi_series(series, length=14):
    """Calculate RSI"""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def add_squeeze_indicators(df, tf):
    """Add squeeze-related indicators to dataframe"""
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
    df["rsi14"] = calc_rsi_series(df["close"])
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    
    minutes = TIMEFRAME_TO_MINUTES.get(tf, 60)
    df["close_dt"] = df["open_dt"] + pd.Timedelta(minutes=minutes)
    
    return df


def find_squeeze_breakouts(df, squeeze_thr=0.02):
    """Find squeeze breakout events"""
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
    high_tf: str,
    low_tf: str,
    squeeze_thr_high: float,
    squeeze_thr_low: float,
    lower_lookback_bars: int,
    rsi_min: float,
    rsi_max: float,
    require_above_mid: bool,
) -> Dict:
    """Analyze multi-timeframe squeeze patterns"""
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
        
        # Additional lower TF features
        lt_rsi_mean = float(seg["rsi14"].mean()) if len(seg) > 0 else np.nan
        
        # Band position (0=lower, 1=upper)
        width = last["bb_upper"] - last["bb_lower"]
        if width != 0 and np.isfinite(width):
            lt_pos_band = float((last["close"] - last["bb_lower"]) / width)
        else:
            lt_pos_band = np.nan
        
        # Lower TF squeeze
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
