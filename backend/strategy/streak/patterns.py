"""Pattern profile helpers for complex streak analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class PatternProfile:
    """Derived metadata from a complex pattern."""

    pattern: List[int]
    rise_len: int
    drop_len: int
    last_direction: int
    expected_c1_direction: int


def build_pattern_profile(complex_pattern: Optional[List[int]]) -> Optional[PatternProfile]:
    """Build derived pattern metadata used by matcher/analyzer pipeline."""
    if not complex_pattern:
        return None
    if any(v not in (-1, 1) for v in complex_pattern):
        return None

    last_direction = complex_pattern[-1]
    return PatternProfile(
        pattern=list(complex_pattern),
        rise_len=complex_pattern.count(1),
        drop_len=complex_pattern.count(-1),
        last_direction=last_direction,
        expected_c1_direction=-last_direction,
    )
