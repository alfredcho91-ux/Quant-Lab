"""Detail calculators for simple streak analysis."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from strategy.streak.common import RSI_OVERBOUGHT


def calculate_comparative_report(
    df: pd.DataFrame,
    n_streak: int,
    direction: str,
) -> Optional[Dict[str, Any]]:
    """Comparative report based on dynamic nG+1R / nR+1G pattern."""
    is_green_pattern = direction == "green"

    streak_cond = pd.Series([True] * len(df), index=df.index)
    for i in range(2, n_streak + 2):
        streak_cond &= df["is_green"].shift(i) == is_green_pattern

    reversal_pattern_cond = streak_cond & (df["is_green"].shift(1) == (not is_green_pattern))
    reversal_pattern_cases = df[reversal_pattern_cond].copy()

    if is_green_pattern:
        success_cases = reversal_pattern_cases[reversal_pattern_cases["is_green"] == True]
        failure_cases = reversal_pattern_cases[reversal_pattern_cases["is_green"] == False]
    else:
        success_cases = reversal_pattern_cases[reversal_pattern_cases["is_green"] == False]
        failure_cases = reversal_pattern_cases[reversal_pattern_cases["is_green"] == True]

    if len(reversal_pattern_cases) == 0:
        return None

    def safe_mean(series: pd.Series):
        vals = series.dropna()
        return float(vals.mean()) if len(vals) > 0 else None

    return {
        "pattern_total": len(reversal_pattern_cases),
        "success_count": len(success_cases),
        "failure_count": len(failure_cases),
        "success_rate": round(len(success_cases) / len(reversal_pattern_cases) * 100, 2)
        if len(reversal_pattern_cases) > 0
        else None,
        "pattern_type": "nG + 1R" if is_green_pattern else "nR + 1G",
        "success": {
            "prev_rsi": round(safe_mean(success_cases["rsi"].shift(1)), 2)
            if len(success_cases) > 0 and safe_mean(success_cases["rsi"].shift(1))
            else None,
            "prev_body_pct": round(safe_mean(success_cases["body_pct"].shift(1)), 2)
            if len(success_cases) > 0 and safe_mean(success_cases["body_pct"].shift(1))
            else None,
            "prev_vol_change": round(safe_mean(success_cases["vol_change"].shift(1)), 2)
            if len(success_cases) > 0 and safe_mean(success_cases["vol_change"].shift(1))
            else None,
        },
        "failure": {
            "prev_rsi": round(safe_mean(failure_cases["rsi"].shift(1)), 2)
            if len(failure_cases) > 0 and safe_mean(failure_cases["rsi"].shift(1))
            else None,
            "prev_body_pct": round(safe_mean(failure_cases["body_pct"].shift(1)), 2)
            if len(failure_cases) > 0 and safe_mean(failure_cases["body_pct"].shift(1))
            else None,
            "prev_vol_change": round(safe_mean(failure_cases["vol_change"].shift(1)), 2)
            if len(failure_cases) > 0 and safe_mean(failure_cases["vol_change"].shift(1))
            else None,
        },
    }


def calculate_short_signal(
    df: pd.DataFrame,
    n_streak: int,
    avg_rise: Optional[float],
) -> Optional[Dict[str, Any]]:
    """Short signal stats for green streak mode."""
    short_cond = pd.Series([True] * len(df), index=df.index)
    for i in range(1, n_streak + 1):
        short_cond &= df["is_green"].shift(i) == True

    short_filter = short_cond & (df["rsi"].shift(1) >= RSI_OVERBOUGHT)
    short_targets = df[short_filter].copy()

    if len(short_targets) < 3:
        return None

    base_rise = avg_rise if avg_rise is not None else 0.5
    target_entry_rise = max(0.1, base_rise * 0.6)

    short_targets["entry_threshold"] = short_targets["open"] * (1 + target_entry_rise / 100)
    short_targets["is_filled"] = short_targets["high"] >= short_targets["entry_threshold"]

    total_signals = len(short_targets)
    filled_cases = short_targets[short_targets["is_filled"]].copy()
    unfilled_cases = short_targets[~short_targets["is_filled"]].copy()
    fill_rate = (len(filled_cases) / total_signals * 100) if total_signals > 0 else 0

    if len(filled_cases) == 0:
        return None

    filled_cases["is_win"] = filled_cases["close"] < filled_cases["entry_threshold"]
    short_win_count = int(filled_cases["is_win"].sum())
    short_win_rate = (short_win_count / len(filled_cases)) * 100 if len(filled_cases) > 0 else 0

    filled_cases["pnl_pct"] = (
        (filled_cases["entry_threshold"] - filled_cases["close"]) / filled_cases["entry_threshold"] * 100
    )
    wins = filled_cases[filled_cases["pnl_pct"] > 0]
    avg_profit = float(wins["pnl_pct"].mean()) if len(wins) > 0 else 0
    overall_win_rate = (short_win_count / total_signals * 100) if total_signals > 0 else 0

    reliability = "high" if fill_rate >= 70 else "medium" if fill_rate >= 50 else "low"
    bias_warning = fill_rate < 50

    return {
        "enabled": short_win_rate >= 60 and fill_rate >= 50,
        "total_signals": total_signals,
        "filled_cases": len(filled_cases),
        "unfilled_cases": len(unfilled_cases),
        "fill_rate": round(fill_rate, 2),
        "win_count": short_win_count,
        "win_rate": round(short_win_rate, 2),
        "overall_win_rate": round(overall_win_rate, 2),
        "entry_rise_pct": round(target_entry_rise, 2),
        "take_profit_pct": round(avg_profit, 2),
        "stop_loss_pct": 2.0,
        "rsi_threshold": RSI_OVERBOUGHT,
        "reliability": reliability,
        "bias_warning": bias_warning,
        "note": "Bias Removed: All signals tracked, only filled cases analyzed",
    }


__all__ = [
    "calculate_comparative_report",
    "calculate_short_signal",
]
