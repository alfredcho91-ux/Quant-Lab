"""Index matching helpers for complex chart data."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def resolve_chart_position(df_index: pd.Index, pattern_date: Any) -> Optional[int]:
    """Convert pattern_date to dataframe index position."""
    if pattern_date is None:
        return None
    try:
        pattern_ts = pd.to_datetime(pattern_date, errors="coerce")
        if pd.isna(pattern_ts):
            return None
        if isinstance(df_index, pd.DatetimeIndex):
            if pattern_ts.tzinfo is None and df_index.tz is not None:
                pattern_ts = pattern_ts.tz_localize(df_index.tz)
            elif pattern_ts.tzinfo is not None and df_index.tz is None:
                pattern_ts = pattern_ts.tz_localize(None)
            elif pattern_ts.tzinfo is not None and df_index.tz is not None:
                pattern_ts = pattern_ts.tz_convert(df_index.tz)

        pos = df_index.get_indexer([pattern_ts])[0]
        return int(pos) if pos >= 0 else None
    except (ValueError, TypeError, KeyError, IndexError, pd.errors.ParserError):
        return None


def build_chart_positions(
    df: pd.DataFrame,
    chart_data: List[Dict[str, Any]],
) -> List[Tuple[Dict[str, Any], int]]:
    """Resolve all chart pattern positions once and reuse downstream."""
    resolved_positions: List[Tuple[Dict[str, Any], int]] = []
    max_pos = len(df.index) - 1
    for item in chart_data:
        cached_pos = item.get("pattern_pos")
        if isinstance(cached_pos, int) and 0 <= cached_pos <= max_pos:
            resolved_positions.append((item, cached_pos))
            continue
        pos = resolve_chart_position(df.index, item.get("pattern_date"))
        if pos is not None:
            resolved_positions.append((item, pos))
    return resolved_positions
