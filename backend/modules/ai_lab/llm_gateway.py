"""LLM gateway helpers for AI backtest lab."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional


def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    clean_text = raw_text.replace("```json", "").replace("```", "").strip()
    if not clean_text:
        return None

    try:
        parsed = json.loads(clean_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(clean_text):
        if ch != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(clean_text[idx:])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def normalize_gemini_model(
    model: str,
    *,
    default_model: str,
    model_aliases: Dict[str, str],
) -> str:
    """잘못된 또는 deprecated Gemini 모델명을 사용 가능한 모델로 치환."""
    if not model or not model.strip():
        return default_model
    key = model.strip().lower().replace("_", "-").replace(" ", "-")
    while "--" in key:
        key = key.replace("--", "-")
    if key in model_aliases:
        return model_aliases[key]
    # gemini-3 계열 중 미확인 하위 모델명은 기본 모델로 강등
    if key.startswith("gemini-3"):
        return default_model
    return key


def validate_gemini_key(api_key: str) -> Optional[str]:
    """Gemini REST API 키 형식 사전 검증."""
    key = (api_key or "").strip()
    if not key:
        return "API key is empty."
    if key.startswith("gen-lang-client-"):
        return (
            "Invalid key format: 'gen-lang-client-...' is a browser client key, not a Gemini REST API key. "
            "Use an AI Studio key (usually starts with 'AIza')."
        )
    return None


def call_gemini(
    *,
    api_key: str,
    prompt: str,
    model: str,
    history: Optional[list],
    temperature: float,
    default_model: str,
    model_aliases: Dict[str, str],
    build_llm_client_fn: Callable[..., Any],
    requests_post_fn: Callable[..., Any],
    system_prompt_template: str,
    strategy_ids: List[str],
    error_code_http: str,
    error_code_network: str,
    error_code_response_format: str,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """Google Gemini API 호출 래퍼. 내부 전송은 llm client adapter를 사용."""
    log = logger or logging.getLogger(__name__)

    normalized_model = normalize_gemini_model(
        model,
        default_model=default_model,
        model_aliases=model_aliases,
    )

    full_system_prompt = system_prompt_template.format(strategy_list=", ".join(strategy_ids))

    client = build_llm_client_fn(
        "gemini",
        api_key=api_key,
        model=normalized_model,
        # Keep this injection so existing tests can monkeypatch ai_service.requests.post.
        http_post=requests_post_fn,
    )
    llm_result = client.generate(
        system_prompt=full_system_prompt,
        prompt=prompt,
        history=history,
        temperature=temperature,
    )

    error = llm_result.get("error")
    error_code = llm_result.get("error_code")
    if error is not None:
        if error_code == error_code_http:
            log.error("Gemini API HTTP error (model=%s): %s", normalized_model, error)
        elif error_code == error_code_network:
            log.error("Gemini API request error (model=%s): %s", normalized_model, error)
        elif error_code == error_code_response_format:
            log.error("Gemini API unexpected parse error (model=%s): %s", normalized_model, error)
        return {
            "thought": f"Error calling AI ({normalized_model}): {error}",
            "params": None,
            "error": error,
            "error_code": error_code,
        }

    text = str(llm_result.get("text") or "")
    parsed = extract_json_from_text(text)
    if parsed is None:
        # JSON 형식이 아니면 자연어 답변으로 처리 (기본 동작)
        return {
            "thought": text.strip(),
            "params": None,
            "error": None,
            "error_code": None,
        }

    return {
        "thought": parsed.get("thought", ""),
        "params": parsed.get("params"),
        "error": None,
        "error_code": None,
    }

