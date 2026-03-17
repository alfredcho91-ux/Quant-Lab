"""AI service layer for research and analyst-agent workflows."""

from __future__ import annotations

import logging
import os
from functools import partial
from typing import Any, Dict, List, Optional

import requests

from config import settings
from core.indicators import build_indicator_adapter
from core.strategies import STRATS
from models.request import BacktestParams
from modules.ai_lab import (
    analyst_agent as ai_analyst_agent,
    analyzer as ai_analyzer,
    constants as ai_constants,
    llm_gateway,
    optimization as ai_optimization,
    params_normalizer as ai_params_normalizer,
    parser as ai_parser,
    request_policy as ai_request_policy,
    research_workflow as ai_research_workflow,
    result_factory as ai_result_factory,
)
from modules.ai_lab.prompts import SYSTEM_PROMPT_TEMPLATE, SYSTEM_PROMPT_VERSION
from modules.ai_lab.tools.python_repl import execute_pandas_code
from modules.ai_lab.types import AIAnalystResult, AIServiceResult
from modules.backtest.service import run_backtest_advanced_service, run_backtest_service
from services.ai_clients import build_llm_client
from utils.cache import DataCache
from utils.data_loader import load_data_for_analysis
from utils.stats import calculate_binomial_pvalue, wilson_confidence_interval

logger = logging.getLogger(__name__)
STRATEGY_IDS = [str(item["id"]) for item in STRATS if item.get("id")]

GEMINI_DEFAULT_MODEL = ai_constants.GEMINI_DEFAULT_MODEL
GEMINI_MODEL_ALIASES = ai_constants.GEMINI_MODEL_ALIASES
ERROR_CODE_PROVIDER_UNSUPPORTED = ai_constants.ERROR_CODE_PROVIDER_UNSUPPORTED
ERROR_CODE_API_KEY_INVALID = ai_constants.ERROR_CODE_API_KEY_INVALID
ERROR_CODE_MODEL_HTTP = ai_constants.ERROR_CODE_MODEL_HTTP
ERROR_CODE_MODEL_NETWORK = ai_constants.ERROR_CODE_MODEL_NETWORK
ERROR_CODE_MODEL_RESPONSE_EMPTY = ai_constants.ERROR_CODE_MODEL_RESPONSE_EMPTY
ERROR_CODE_MODEL_RESPONSE_FORMAT = ai_constants.ERROR_CODE_MODEL_RESPONSE_FORMAT
ERROR_CODE_BACKTEST_EXECUTION = ai_constants.ERROR_CODE_BACKTEST_EXECUTION
MISSING_VALUE_TOKENS = ai_constants.MISSING_VALUE_TOKENS
VALID_BACKTEST_INTERVALS = ai_constants.VALID_BACKTEST_INTERVALS
LOWERCASE_BACKTEST_INTERVALS = ai_constants.LOWERCASE_BACKTEST_INTERVALS
INTERVAL_ALIASES = ai_constants.INTERVAL_ALIASES
OPTIMIZATION_TRIALS = ai_constants.OPTIMIZATION_TRIALS
OPTIMIZATION_TRAIN_RATIO = ai_constants.OPTIMIZATION_TRAIN_RATIO
OPTIMIZATION_MONTE_CARLO_RUNS = ai_constants.OPTIMIZATION_MONTE_CARLO_RUNS
OPTIMIZATION_FEATURE_LABELS = ai_constants.OPTIMIZATION_FEATURE_LABELS

AI_RESPONSE_CACHE = DataCache(
    ttl_seconds=max(60, int(os.getenv("AI_RESPONSE_CACHE_TTL_SECONDS", "600")))
)


def run_data_analyst_agent(
    api_key: str,
    coin: str,
    interval: str,
    user_prompt: str,
    model: str = GEMINI_DEFAULT_MODEL,
) -> AIAnalystResult:
    return ai_analyst_agent.run_data_analyst_agent(
        api_key=api_key,
        coin=coin,
        interval=interval,
        user_prompt=user_prompt,
        model=model,
        build_llm_client_fn=build_llm_client,
        execute_pandas_code_fn=execute_pandas_code,
    )


_split_prompt_and_ui_context = ai_parser.split_prompt_and_ui_context
_build_ai_result = ai_result_factory.build_ai_result
_normalize_result_payload = ai_result_factory.normalize_result_payload
_build_ai_cache_key = partial(
    ai_result_factory.build_ai_cache_key,
    prompt_version=SYSTEM_PROMPT_VERSION,
)


_infer_interval_from_prompt = ai_parser.infer_interval_from_prompt


_normalize_coin_from_text = ai_parser.normalize_coin_from_text


_contains_probability_intent = ai_parser.contains_probability_intent


_looks_like_optimization_request = ai_parser.looks_like_optimization_request


_score_advanced_backtest = ai_optimization.score_advanced_backtest
_build_optimization_characteristics = partial(
    ai_optimization.build_optimization_characteristics,
    feature_labels=OPTIMIZATION_FEATURE_LABELS,
)

_build_ui_result_from_advanced_payload = ai_optimization.build_ui_result_from_advanced_payload


def _run_backtest_parameter_optimization(base_params: BacktestParams, prompt: str) -> Dict[str, Any]:
    return ai_optimization.run_backtest_parameter_optimization(
        base_params=base_params,
        prompt=prompt,
        run_backtest_service_fn=run_backtest_service,
        run_backtest_advanced_service_fn=run_backtest_advanced_service,
        optimization_trials=OPTIMIZATION_TRIALS,
        optimization_train_ratio=OPTIMIZATION_TRAIN_RATIO,
        optimization_monte_carlo_runs=OPTIMIZATION_MONTE_CARLO_RUNS,
        feature_labels=OPTIMIZATION_FEATURE_LABELS,
        logger=logger,
    )


def _is_missing_value(value: Any) -> bool:
    return ai_params_normalizer.is_missing_value(value, MISSING_VALUE_TOKENS)


def _normalize_leverage(value: Any, default: int = 1) -> int:
    if _is_missing_value(value):
        return default
    return ai_params_normalizer.normalize_leverage(value, default=default)


_extract_leverage_from_prompt = ai_params_normalizer.extract_leverage_from_prompt


_normalize_coin = partial(
    ai_params_normalizer.normalize_coin,
    missing_value_tokens=MISSING_VALUE_TOKENS,
)

_normalize_interval = partial(
    ai_params_normalizer.normalize_interval,
    missing_value_tokens=MISSING_VALUE_TOKENS,
    valid_backtest_intervals=VALID_BACKTEST_INTERVALS,
    interval_aliases=INTERVAL_ALIASES,
    lowercase_backtest_intervals=LOWERCASE_BACKTEST_INTERVALS,
)

_normalize_direction = partial(
    ai_params_normalizer.normalize_direction,
    missing_value_tokens=MISSING_VALUE_TOKENS,
)

_normalize_strategy_id = partial(
    ai_params_normalizer.normalize_strategy_id,
    missing_value_tokens=MISSING_VALUE_TOKENS,
    strategy_ids=[str(item["id"]) for item in STRATS],
)

_sanitize_backtest_params = partial(
    ai_params_normalizer.sanitize_backtest_params,
    missing_value_tokens=MISSING_VALUE_TOKENS,
    valid_backtest_intervals=VALID_BACKTEST_INTERVALS,
    interval_aliases=INTERVAL_ALIASES,
    lowercase_backtest_intervals=LOWERCASE_BACKTEST_INTERVALS,
    strategy_ids=[str(item["id"]) for item in STRATS],
    default_coin="BTC",
    default_interval="4h",
    default_strategy_id="RSI",
    default_direction="Long",
)

_minimal_backtest_params = ai_params_normalizer.minimal_backtest_params
_normalize_gemini_model = partial(
    llm_gateway.normalize_gemini_model,
    default_model=GEMINI_DEFAULT_MODEL,
    model_aliases=GEMINI_MODEL_ALIASES,
)
_validate_gemini_key = llm_gateway.validate_gemini_key


_looks_ambiguous_prompt = partial(
    ai_request_policy.looks_ambiguous_prompt,
    contains_probability_intent_fn=_contains_probability_intent,
    strategies=STRATS,
)
_build_clarification_payload = partial(
    ai_request_policy.build_clarification_payload,
    normalize_coin_from_text_fn=_normalize_coin_from_text,
    normalize_interval_fn=_normalize_interval,
    build_ai_result_fn=_build_ai_result,
)
_build_optimization_clarification_payload = partial(
    ai_request_policy.build_optimization_clarification_payload,
    normalize_coin_from_text_fn=_normalize_coin_from_text,
    normalize_interval_fn=_normalize_interval,
    build_ai_result_fn=_build_ai_result,
)


def _run_conditional_probability_analysis(prompt: str, ui_context: Dict[str, str]) -> Optional[Dict[str, Any]]:
    def _identity_prepare(frame):
        return frame

    def _trend_adapter(frame):
        return build_indicator_adapter(frame, mode="trend_judgment")

    return ai_analyzer.run_conditional_probability_analysis(
        prompt,
        ui_context,
        load_data_for_analysis_fn=load_data_for_analysis,
        prepare_strategy_data_fn=_identity_prepare,
        compute_trend_judgment_indicators_fn=_trend_adapter,
        normalize_interval_fn=_normalize_interval,
        calculate_binomial_pvalue_fn=calculate_binomial_pvalue,
        wilson_confidence_interval_fn=wilson_confidence_interval,
    )


_extract_json_from_text = llm_gateway.extract_json_from_text


def _call_gemini(
    api_key: str,
    prompt: str,
    model: str = GEMINI_DEFAULT_MODEL,
    history: Optional[list] = None,
    temperature: float = 0.2,
) -> AIServiceResult:
    return llm_gateway.call_gemini(
        api_key=api_key,
        prompt=prompt,
        model=model,
        history=history,
        temperature=temperature,
        default_model=GEMINI_DEFAULT_MODEL,
        model_aliases=GEMINI_MODEL_ALIASES,
        build_llm_client_fn=build_llm_client,
        requests_post_fn=requests.post,
        system_prompt_template=SYSTEM_PROMPT_TEMPLATE,
        strategy_ids=STRATEGY_IDS,
        error_code_http=ERROR_CODE_MODEL_HTTP,
        error_code_network=ERROR_CODE_MODEL_NETWORK,
        error_code_response_format=ERROR_CODE_MODEL_RESPONSE_FORMAT,
        logger=logger,
    )


def _build_research_dependencies() -> ai_research_workflow.AIResearchDependencies:
    return ai_research_workflow.AIResearchDependencies(
        build_ai_result_fn=_build_ai_result,
        normalize_result_payload_fn=_normalize_result_payload,
        split_prompt_and_ui_context_fn=_split_prompt_and_ui_context,
        looks_like_optimization_request_fn=_looks_like_optimization_request,
        contains_probability_intent_fn=_contains_probability_intent,
        extract_leverage_from_prompt_fn=_extract_leverage_from_prompt,
        normalize_gemini_model_fn=_normalize_gemini_model,
        build_ai_cache_key_fn=_build_ai_cache_key,
        looks_ambiguous_prompt_fn=_looks_ambiguous_prompt,
        build_clarification_payload_fn=_build_clarification_payload,
        build_optimization_clarification_payload_fn=_build_optimization_clarification_payload,
        run_conditional_probability_analysis_fn=_run_conditional_probability_analysis,
        validate_gemini_key_fn=_validate_gemini_key,
        call_gemini_fn=_call_gemini,
        sanitize_backtest_params_fn=_sanitize_backtest_params,
        minimal_backtest_params_fn=_minimal_backtest_params,
        run_backtest_parameter_optimization_fn=_run_backtest_parameter_optimization,
        run_backtest_service_fn=run_backtest_service,
        backtest_params_cls=BacktestParams,
        ai_response_cache=AI_RESPONSE_CACHE,
        default_settings_api_key=settings.GEMINI_API_KEY,
        error_code_provider_unsupported=ERROR_CODE_PROVIDER_UNSUPPORTED,
        error_code_api_key_invalid=ERROR_CODE_API_KEY_INVALID,
        error_code_backtest_execution=ERROR_CODE_BACKTEST_EXECUTION,
        logger=logger,
    )


def process_ai_research(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = GEMINI_DEFAULT_MODEL,
    provider: str = "gemini",
    history: Optional[list] = None,
    temperature: float = 0.2,
) -> AIServiceResult:
    """AI parameter extraction and backtest orchestration."""
    return ai_research_workflow.process_ai_research(
        prompt=prompt,
        api_key=api_key,
        model=model,
        provider=provider,
        history=history,
        temperature=temperature,
        deps=_build_research_dependencies(),
    )
