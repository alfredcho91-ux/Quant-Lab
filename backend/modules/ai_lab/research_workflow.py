"""High-level orchestration for AI research requests."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Type


@dataclass(frozen=True)
class AIResearchDependencies:
    build_ai_result_fn: Callable[..., Dict[str, Any]]
    normalize_result_payload_fn: Callable[..., Dict[str, Any]]
    split_prompt_and_ui_context_fn: Callable[[str], tuple[str, Dict[str, str]]]
    looks_like_optimization_request_fn: Callable[[str], bool]
    contains_probability_intent_fn: Callable[[str], bool]
    extract_leverage_from_prompt_fn: Callable[[str], Optional[int]]
    normalize_gemini_model_fn: Callable[[str], str]
    build_ai_cache_key_fn: Callable[..., str]
    looks_ambiguous_prompt_fn: Callable[[str], bool]
    build_clarification_payload_fn: Callable[[str, Dict[str, str]], Dict[str, Any]]
    build_optimization_clarification_payload_fn: Callable[[str, Dict[str, str]], Dict[str, Any]]
    run_conditional_probability_analysis_fn: Callable[[str, Dict[str, str]], Optional[Dict[str, Any]]]
    validate_gemini_key_fn: Callable[[str], Optional[str]]
    call_gemini_fn: Callable[..., Dict[str, Any]]
    sanitize_backtest_params_fn: Callable[[Any], Dict[str, Any]]
    minimal_backtest_params_fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    run_backtest_parameter_optimization_fn: Callable[[Any, str], Dict[str, Any]]
    run_backtest_service_fn: Callable[[Any], Dict[str, Any]]
    backtest_params_cls: Type[Any]
    ai_response_cache: Any
    default_settings_api_key: Optional[str]
    error_code_provider_unsupported: str
    error_code_api_key_invalid: str
    error_code_backtest_execution: str
    logger: logging.Logger


def _cache_and_normalize(
    *,
    cache: Any,
    cache_key: str,
    payload: Dict[str, Any],
    execution_path: str,
    normalize_result_payload_fn: Callable[..., Dict[str, Any]],
) -> Dict[str, Any]:
    cache.set(cache_key, payload)
    return normalize_result_payload_fn(
        payload,
        execution_path=execution_path,
        cache_hit=False,
    )


def _run_backtest_stage(
    *,
    params_dict: Optional[Dict[str, Any]],
    is_optimization_request: bool,
    clean_prompt: str,
    thought: str,
    deps: AIResearchDependencies,
) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], str, Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    backtest_result = None
    final_analysis_result = None
    ai_error = None
    ai_error_code = None

    if params_dict is None:
        return backtest_result, final_analysis_result, thought, ai_error, ai_error_code, params_dict

    try:
        try:
            bt_params = deps.backtest_params_cls(**params_dict)
        except Exception as validation_error:
            deps.logger.warning(
                "Invalid AI backtest params detected. Falling back to minimal safe params. error=%s raw=%s",
                validation_error,
                params_dict,
            )
            params_dict = deps.minimal_backtest_params_fn(params_dict)
            bt_params = deps.backtest_params_cls(**params_dict)
            thought += "\n(Invalid AI params were normalized to safe defaults.)"

        deps.logger.info("AI generated params: %s", bt_params)
        if is_optimization_request:
            optimization_payload = deps.run_backtest_parameter_optimization_fn(bt_params, clean_prompt)
            if optimization_payload.get("error") is None:
                params_dict = optimization_payload.get("params")
                backtest_result = optimization_payload.get("backtest_result")
                final_analysis_result = optimization_payload.get("analysis_result")
                thought = f"{thought}\n\n{optimization_payload.get('answer', '')}".strip()
            else:
                thought += "\n(Auto optimization failed, so a single backtest was executed.)"
                backtest_result = deps.run_backtest_service_fn(bt_params)
        else:
            backtest_result = deps.run_backtest_service_fn(bt_params)
    except Exception as exc:
        deps.logger.error("Backtest execution failed: %s", exc)
        thought += f"\n(Backtest failed: {str(exc)})"
        ai_error = str(exc)
        ai_error_code = deps.error_code_backtest_execution

    return backtest_result, final_analysis_result, thought, ai_error, ai_error_code, params_dict


def process_ai_research(
    *,
    prompt: str,
    api_key: Optional[str],
    model: str,
    provider: str,
    history: Optional[list],
    temperature: float,
    deps: AIResearchDependencies,
) -> Dict[str, Any]:
    provider_norm = (provider or "gemini").strip().lower()
    if provider_norm != "gemini":
        msg = f"Provider '{provider_norm}' is not supported yet. Use provider='gemini'."
        return deps.build_ai_result_fn(
            answer=msg,
            execution_path="provider_validation",
            error=msg,
            error_code=deps.error_code_provider_unsupported,
        )

    effective_api_key = api_key or deps.default_settings_api_key
    clean_prompt, ui_context = deps.split_prompt_and_ui_context_fn(prompt)
    is_optimization_request = deps.looks_like_optimization_request_fn(clean_prompt)
    prompt_leverage = deps.extract_leverage_from_prompt_fn(clean_prompt)
    normalized_model = deps.normalize_gemini_model_fn(model)
    cache_key = deps.build_ai_cache_key_fn(
        clean_prompt=clean_prompt,
        ui_context=ui_context,
        provider=provider_norm,
        model=normalized_model,
        temperature=temperature,
        history=history,
    )

    cached = deps.ai_response_cache.get(cache_key)
    if isinstance(cached, dict):
        execution_path = str(cached.get("execution_path") or "cached")
        return deps.normalize_result_payload_fn(
            cached,
            execution_path=execution_path,
            cache_hit=True,
        )

    if is_optimization_request and deps.contains_probability_intent_fn(clean_prompt):
        payload = deps.build_optimization_clarification_payload_fn(clean_prompt, ui_context)
        return _cache_and_normalize(
            cache=deps.ai_response_cache,
            cache_key=cache_key,
            payload=payload,
            execution_path="optimization_clarification",
            normalize_result_payload_fn=deps.normalize_result_payload_fn,
        )

    if deps.looks_ambiguous_prompt_fn(clean_prompt) and not is_optimization_request:
        payload = deps.build_clarification_payload_fn(clean_prompt, ui_context)
        return _cache_and_normalize(
            cache=deps.ai_response_cache,
            cache_key=cache_key,
            payload=payload,
            execution_path="clarification",
            normalize_result_payload_fn=deps.normalize_result_payload_fn,
        )

    probability_result = deps.run_conditional_probability_analysis_fn(clean_prompt, ui_context)
    if probability_result is not None:
        normalized_probability = deps.normalize_result_payload_fn(
            probability_result,
            execution_path="conditional_probability",
            cache_hit=False,
        )
        if normalized_probability.get("error") is None:
            deps.ai_response_cache.set(cache_key, normalized_probability)
        return normalized_probability

    key_error = deps.validate_gemini_key_fn(effective_api_key)
    if key_error:
        return deps.build_ai_result_fn(
            answer=key_error,
            execution_path="api_key_validation",
            error=key_error,
            error_code=deps.error_code_api_key_invalid,
        )

    ai_response = deps.call_gemini_fn(
        api_key=effective_api_key,
        prompt=prompt,
        model=normalized_model,
        history=history,
        temperature=temperature,
    )
    thought = ai_response.get("thought", "Analysis failed.")
    raw_params = ai_response.get("params")

    if raw_params is not None:
        params_dict = deps.sanitize_backtest_params_fn(raw_params)
        if prompt_leverage is not None:
            params_dict["leverage"] = prompt_leverage
    elif is_optimization_request and ai_response.get("error") is None:
        payload = deps.build_optimization_clarification_payload_fn(clean_prompt, ui_context)
        return _cache_and_normalize(
            cache=deps.ai_response_cache,
            cache_key=cache_key,
            payload=payload,
            execution_path="optimization_clarification",
            normalize_result_payload_fn=deps.normalize_result_payload_fn,
        )
    else:
        params_dict = None

    ai_error = ai_response.get("error")
    ai_error_code = ai_response.get("error_code")

    (
        backtest_result,
        final_analysis_result,
        thought,
        backtest_error,
        backtest_error_code,
        params_dict,
    ) = _run_backtest_stage(
        params_dict=params_dict,
        is_optimization_request=is_optimization_request,
        clean_prompt=clean_prompt,
        thought=thought,
        deps=deps,
    )
    if backtest_error is not None:
        ai_error = backtest_error
        ai_error_code = backtest_error_code

    if ai_error is not None:
        execution_path = "llm_or_backtest_error"
    elif backtest_result is not None and is_optimization_request:
        execution_path = "llm_backtest_optimized"
    elif backtest_result is not None:
        execution_path = "llm_backtest"
    else:
        execution_path = "llm_text"

    final_result = deps.build_ai_result_fn(
        answer=thought,
        backtest_params=params_dict,
        backtest_result=backtest_result,
        analysis_result=final_analysis_result,
        execution_path=execution_path,
        error=ai_error,
        error_code=ai_error_code,
    )
    if final_result.get("error") is None:
        deps.ai_response_cache.set(cache_key, final_result)
    return final_result
