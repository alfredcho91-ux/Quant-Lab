"""Runner utilities for simple streak pattern extraction."""

from __future__ import annotations

import logging
from typing import List

import pandas as pd

from strategy.streak.common import DEBUG_MODE, normalize_indices

logger = logging.getLogger(__name__)


def collect_simple_target_cases(
    df: pd.DataFrame,
    n_streak: int,
    min_total_body_pct: float | None = None,
) -> pd.DataFrame:
    """Collect validated simple-mode pattern completion rows."""
    condition = pd.Series([True] * len(df), index=df.index)
    condition &= df["target_bit"] == True
    for i in range(1, n_streak):
        condition &= df["target_bit"].shift(i) == True

    target_indices_raw = df[condition].index.tolist()
    valid_indices = normalize_indices(target_indices_raw, df)

    if min_total_body_pct is not None and min_total_body_pct > 0:
        valid_indices = _apply_min_body_filter(df, valid_indices, n_streak, min_total_body_pct)
        if DEBUG_MODE:
            logger.debug(
                f"[Simple Mode] body filter applied: {len(target_indices_raw)} -> {len(valid_indices)} "
                f"(min {min_total_body_pct}%)"
            )

    if len(valid_indices) == 0:
        return df.iloc[0:0].copy()

    unique_idx = pd.Index(valid_indices).drop_duplicates()
    return df.loc[unique_idx].copy()


def _apply_min_body_filter(
    df: pd.DataFrame,
    indices: List[pd.Timestamp],
    n_streak: int,
    min_total_body_pct: float,
) -> List[pd.Timestamp]:
    """Keep only rows whose N-bar body sum passes threshold."""
    filtered = []
    for idx in indices:
        try:
            pos = df.index.get_loc(idx)
            total_body_pct = 0.0
            for i in range(n_streak):
                if pos - i >= 0:
                    body_val = df.iloc[pos - i]["body_pct"]
                    if pd.notna(body_val):
                        total_body_pct += body_val
            if total_body_pct >= min_total_body_pct:
                filtered.append(idx)
        except (KeyError, IndexError, TypeError):
            continue
    return filtered
