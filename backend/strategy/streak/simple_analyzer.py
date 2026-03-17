"""Facade for simple streak analytics."""

from __future__ import annotations

from .simple_analysis_details import calculate_comparative_report, calculate_short_signal
from .simple_analysis_summary import calculate_simple_metrics

__all__ = [
    "calculate_comparative_report",
    "calculate_short_signal",
    "calculate_simple_metrics",
]
