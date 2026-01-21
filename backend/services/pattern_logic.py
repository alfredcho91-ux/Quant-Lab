# services/pattern_logic.py
"""패턴 분석 비즈니스 로직 - FastAPI 독립적"""

import pandas as pd
import numpy as np
from typing import Dict, Any


PATTERN_DEFINITIONS = {
    "Bullish Engulfing": {"direction": "bull"},
    "Bearish Engulfing": {"direction": "bear"},
    "Hammer": {"direction": "bull"},
    "Shooting Star": {"direction": "bear"},
    "Doji": {"direction": None},
}


def detect_patterns(df: pd.DataFrame) -> Dict[str, Dict]:
    """Detect candle patterns and return signals - matching original Streamlit logic."""
    df = df.copy()
    
    # Basic candle features
    o = df["open"]
    h = df["high"]
    l = df["low"]
    c = df["close"]
    
    is_bull = c > o
    is_bear = c < o
    
    body = (c - o).abs()
    body = body.replace(0, 1e-8)  # Avoid division by zero
    range_size = h - l
    range_size = range_size.replace(0, 1e-8)
    
    body_top = np.where(is_bull, c, o)
    body_bottom = np.where(is_bull, o, c)
    
    upper_wick = h - body_top
    lower_wick = body_bottom - l
    body_rel_range = body / range_size
    
    patterns = {}
    
    # Previous candle data
    prev = df.shift(1)
    prev_bull = prev["close"] > prev["open"]
    prev_bear = prev["close"] < prev["open"]
    
    prev_top = prev[["open", "close"]].max(axis=1)
    prev_bot = prev[["open", "close"]].min(axis=1)
    curr_top = df[["open", "close"]].max(axis=1)
    curr_bot = df[["open", "close"]].min(axis=1)
    
    # Bullish Engulfing - 상승 장악형
    engulf_cond = (curr_top >= prev_top) & (curr_bot <= prev_bot)
    patterns["Bullish Engulfing"] = {
        "signal": (prev_bear & is_bull & engulf_cond).fillna(False),
        "direction": "bull"
    }
    
    # Bearish Engulfing - 하락 장악형
    patterns["Bearish Engulfing"] = {
        "signal": (prev_bull & is_bear & engulf_cond).fillna(False),
        "direction": "bear"
    }
    
    # Bullish Harami - 상승 잉태형
    inside_cond = (curr_top <= prev_top) & (curr_bot >= prev_bot)
    patterns["Bullish Harami"] = {
        "signal": (prev_bear & is_bull & inside_cond).fillna(False),
        "direction": "bull"
    }
    
    # Bearish Harami - 하락 잉태형
    patterns["Bearish Harami"] = {
        "signal": (prev_bull & is_bear & inside_cond).fillna(False),
        "direction": "bear"
    }
    
    # Hammer (양봉 망치형) - MUST be bullish candle
    patterns["Hammer"] = {
        "signal": (
            is_bull &
            (lower_wick >= 2.0 * body) &
            (upper_wick <= 0.5 * body)
        ).fillna(False),
        "direction": "bull"
    }
    
    # Hanging Man (교수형) - Small body, any direction
    patterns["Hanging Man"] = {
        "signal": (
            (body_rel_range <= 0.4) &
            (lower_wick >= 2.0 * body) &
            (upper_wick <= 0.5 * body)
        ).fillna(False),
        "direction": "bear"
    }
    
    # Shooting Star (슈팅 스타) - Small body with long upper wick
    patterns["Shooting Star"] = {
        "signal": (
            (body_rel_range <= 0.4) &
            (upper_wick >= 2.0 * body) &
            (lower_wick <= 0.5 * body)
        ).fillna(False),
        "direction": "bear"
    }
    
    # Doji (십자형) - Very small body
    patterns["Doji"] = {
        "signal": (body_rel_range <= 0.1).fillna(False),
        "direction": None  # Neutral
    }
    
    # Morning Star (모닝 스타)
    prev2 = df.shift(2)
    prev1 = df.shift(1)
    c1_red = prev2["close"] < prev2["open"]
    small_mid_body = (prev1["close"] - prev1["open"]).abs() / (prev1["high"] - prev1["low"]).replace(0, 1e-8) <= 0.4
    c1_mid = (prev2["open"] + prev2["close"]) / 2.0
    c3_above_mid = c >= c1_mid
    patterns["Morning Star"] = {
        "signal": (c1_red & small_mid_body & is_bull & c3_above_mid).fillna(False),
        "direction": "bull"
    }
    
    # Evening Star (이브닝 스타)
    c1_green = prev2["close"] > prev2["open"]
    c3_below_mid = c <= c1_mid
    patterns["Evening Star"] = {
        "signal": (c1_green & small_mid_body & is_bear & c3_below_mid).fillna(False),
        "direction": "bear"
    }
    
    # Three White Soldiers (적삼병)
    df1 = df.shift(1)
    df2 = df.shift(2)
    bull0 = is_bull
    bull1 = df1["close"] > df1["open"]
    bull2 = df2["close"] > df2["open"]
    cond_close_up = (c > df1["close"]) & (df1["close"] > df2["close"])
    patterns["Three White Soldiers"] = {
        "signal": (bull0 & bull1 & bull2 & cond_close_up).fillna(False),
        "direction": "bull"
    }
    
    # Three Black Crows (흑삼병)
    bear0 = is_bear
    bear1 = df1["close"] < df1["open"]
    bear2 = df2["close"] < df2["open"]
    cond_close_down = (c < df1["close"]) & (df1["close"] < df2["close"])
    patterns["Three Black Crows"] = {
        "signal": (bear0 & bear1 & bear2 & cond_close_down).fillna(False),
        "direction": "bear"
    }
    
    return patterns


def compute_pattern_stats(df: pd.DataFrame, patterns: Dict, horizon: int, tp_pct: float, mode: str, position: str) -> Dict[str, Any]:
    """Compute TP hit statistics for patterns."""
    if df.empty:
        return {}
    
    # Forward-looking calculations
    rev_high = df["high"].iloc[::-1]
    rev_low = df["low"].iloc[::-1]
    
    roll_max = rev_high.rolling(horizon, min_periods=1).max().shift(1).iloc[::-1]
    roll_min = rev_low.rolling(horizon, min_periods=1).min().shift(1).iloc[::-1]
    
    stats = {}
    last_idx = df.index[-2] if len(df) > 1 else None
    
    for key, info in patterns.items():
        direction = info.get("direction")
        sig = info.get("signal", pd.Series(False, index=df.index))
        sig = sig.reindex(df.index).fillna(False)
        
        # Exclude last bar (in progress)
        if len(sig) > 0:
            sig.iloc[-1] = False
        
        if not sig.any():
            stats[key] = {"direction": direction, "signals": 0, "hit_rate": None, "last_on": False}
            continue
        
        entry_prices = df.loc[sig, "close"]
        signals_count = int(sig.sum())
        
        # Compute hit rate based on mode
        if mode == "natural":
            if direction == "bull":
                target = roll_max.loc[sig]
                valid = ~target.isna()
                if valid.any():
                    roi = (target[valid] - entry_prices[valid]) / entry_prices[valid]
                    hit_rate = float((roi >= tp_pct).mean() * 100.0)
                else:
                    hit_rate = None
            elif direction == "bear":
                target = roll_min.loc[sig]
                valid = ~target.isna()
                if valid.any():
                    roi = (entry_prices[valid] - target[valid]) / entry_prices[valid]
                    hit_rate = float((roi >= tp_pct).mean() * 100.0)
                else:
                    hit_rate = None
            else:
                hit_rate = None
        else:  # position mode
            if position == "long":
                target = roll_max.loc[sig]
                valid = ~target.isna()
                if valid.any():
                    roi = (target[valid] - entry_prices[valid]) / entry_prices[valid]
                    hit_rate = float((roi >= tp_pct).mean() * 100.0)
                else:
                    hit_rate = None
            else:
                target = roll_min.loc[sig]
                valid = ~target.isna()
                if valid.any():
                    roi = (entry_prices[valid] - target[valid]) / entry_prices[valid]
                    hit_rate = float((roi >= tp_pct).mean() * 100.0)
                else:
                    hit_rate = None
        
        last_on = bool(sig.loc[last_idx]) if last_idx is not None and last_idx in sig.index else False
        
        stats[key] = {
            "direction": direction,
            "signals": signals_count,
            "hit_rate": hit_rate,
            "last_on": last_on,
        }
    
    return stats
