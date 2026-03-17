"""Streak API service layer."""

from __future__ import annotations

from typing import Any, Dict

from strategy import analyze_streak_pattern, clear_cache, get_cache_stats


def run_streak_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run streak analysis and normalize envelope fields."""
    result = analyze_streak_pattern(params)
    if not isinstance(result, dict):
        return {"success": False, "data": None, "error": "Invalid streak analysis response"}
    if result.get("success"):
        return {"success": True, "data": result}
    return {
        "success": False,
        "data": None,
        "error": result.get("error", "Streak analysis failed"),
    }


def get_streak_cache_stats() -> Dict[str, Any]:
    """Get streak cache status."""
    return get_cache_stats()


def clear_streak_cache() -> Dict[str, Any]:
    """Clear streak cache."""
    return clear_cache()
