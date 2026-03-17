"""Typed structures for AI lab service responses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class AIServiceResult(TypedDict, total=False):
    thought: str
    params: Optional[Dict[str, Any]]
    answer: str
    backtest_params: Optional[Dict[str, Any]]
    backtest_result: Optional[Dict[str, Any]]
    analysis_result: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarifying_questions: Optional[List[str]]
    cache_hit: Optional[bool]
    execution_path: Optional[str]
    error: Optional[str]
    error_code: Optional[str]


class AIAnalystResult(TypedDict, total=False):
    success: bool
    answer: str
    error: Optional[str]
    execution_path: str
