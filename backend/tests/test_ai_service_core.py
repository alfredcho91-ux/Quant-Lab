"""AI service core orchestration tests."""

import pytest

from modules.ai_lab import service as ai_service


@pytest.fixture(autouse=True)
def clear_ai_response_cache():
    ai_service.AI_RESPONSE_CACHE.clear()
    yield
    ai_service.AI_RESPONSE_CACHE.clear()


def test_normalize_gemini_model_deprecated_aliases_fallback():
    assert ai_service._normalize_gemini_model("gemini-3.0-pro-preview") == ai_service.GEMINI_DEFAULT_MODEL
    assert ai_service._normalize_gemini_model("gemini-3.0-pro-exp") == ai_service.GEMINI_DEFAULT_MODEL
    assert ai_service._normalize_gemini_model("gemini-3.0-pro-preivew") == ai_service.GEMINI_DEFAULT_MODEL


def test_normalize_gemini_model_flash_aliases():
    assert ai_service._normalize_gemini_model("gemini-3-flash") == ai_service.GEMINI_DEFAULT_MODEL
    assert ai_service._normalize_gemini_model("Gemini 3 Flash") == ai_service.GEMINI_DEFAULT_MODEL


def test_normalize_gemini_model_unknown_gemini3_family_fallback():
    assert ai_service._normalize_gemini_model("gemini-3.1-ultra") == ai_service.GEMINI_DEFAULT_MODEL


def test_process_ai_research_rejects_browser_client_key():
    result = ai_service.process_ai_research(
        prompt="RSI strategy",
        api_key="gen-lang-client-0665891800",
        model="gemini-3.0-pro-preview",
        provider="gemini",
    )

    assert result["backtest_params"] is None
    assert result["backtest_result"] is None
    assert result["error"] is not None
    assert "gen-lang-client" in result["answer"]


def test_process_ai_research_rejects_unsupported_provider():
    result = ai_service.process_ai_research(
        prompt="RSI strategy",
        api_key="AIzaDummyKey",
        model="gpt-4o",
        provider="openai",
    )

    assert result["backtest_params"] is None
    assert result["backtest_result"] is None
    assert result["error"] is not None
    assert "not supported" in result["answer"]
    assert result["error_code"] == ai_service.ERROR_CODE_PROVIDER_UNSUPPORTED


def test_process_ai_research_returns_clarification_for_ambiguous_prompt():
    result = ai_service.process_ai_research(
        prompt="돈 버는 전략 추천해줘",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["needs_clarification"] is True
    assert result["clarifying_questions"] is not None
    assert len(result["clarifying_questions"]) >= 3
    assert result["execution_path"] == "clarification"


def test_process_ai_research_uses_prompt_cache(monkeypatch):
    calls = {"count": 0}

    def fake_call_gemini(*args, **kwargs):
        calls["count"] += 1
        return {
            "thought": "cached answer",
            "params": None,
            "error": None,
        }

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)

    first = ai_service.process_ai_research(
        prompt="RSI 전략 설명해줘",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )
    second = ai_service.process_ai_research(
        prompt="RSI 전략 설명해줘",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert calls["count"] == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["answer"] == first["answer"]
