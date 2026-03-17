"""Result payload and cache-key helpers for AI lab service."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


def build_ai_result(
    *,
    answer: str,
    backtest_params: Optional[Dict[str, Any]] = None,
    backtest_result: Optional[Dict[str, Any]] = None,
    analysis_result: Optional[Dict[str, Any]] = None,
    needs_clarification: bool = False,
    clarifying_questions: Optional[List[str]] = None,
    cache_hit: Optional[bool] = False,
    execution_path: Optional[str] = None,
    error: Optional[str] = None,
    error_code: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "answer": answer,
        "backtest_params": backtest_params,
        "backtest_result": backtest_result,
        "analysis_result": analysis_result,
        "needs_clarification": bool(needs_clarification),
        "clarifying_questions": clarifying_questions or None,
        "cache_hit": cache_hit,
        "execution_path": execution_path,
        "error": error,
        "error_code": error_code,
    }


def normalize_result_payload(
    result: Dict[str, Any],
    *,
    execution_path: str,
    cache_hit: bool,
) -> Dict[str, Any]:
    return build_ai_result(
        answer=str(result.get("answer", "")),
        backtest_params=result.get("backtest_params"),
        backtest_result=result.get("backtest_result"),
        analysis_result=result.get("analysis_result"),
        needs_clarification=bool(result.get("needs_clarification", False)),
        clarifying_questions=result.get("clarifying_questions"),
        cache_hit=cache_hit,
        execution_path=execution_path,
        error=result.get("error"),
        error_code=result.get("error_code"),
    )


def compact_history_for_cache(history: Optional[list]) -> List[Dict[str, str]]:
    compact: List[Dict[str, str]] = []
    if not isinstance(history, list):
        return compact

    for item in history[-6:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "user")).strip().lower()
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        compact.append({"role": role, "content": content[:240]})
    return compact


def build_ai_cache_key(
    *,
    clean_prompt: str,
    ui_context: Dict[str, str],
    provider: str,
    model: str,
    temperature: float,
    history: Optional[list],
    prompt_version: str,
) -> str:
    payload = {
        "v": 4,
        "prompt_version": prompt_version,
        "prompt": clean_prompt.strip(),
        "ui_context": dict(sorted(ui_context.items())),
        "provider": provider,
        "model": model,
        "temperature": round(float(temperature), 3),
        "history_tail": compact_history_for_cache(history),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"ai_research:{digest}"
