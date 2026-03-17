"""AI service parameter sanitization tests."""

import pytest

from modules.ai_lab import service as ai_service


@pytest.fixture(autouse=True)
def clear_ai_response_cache():
    ai_service.AI_RESPONSE_CACHE.clear()
    yield
    ai_service.AI_RESPONSE_CACHE.clear()


def test_process_ai_research_sanitizes_none_and_missing_params(monkeypatch):
    def fake_call_gemini(*args, **kwargs):
        return {
            "thought": "ok",
            "params": {
                "coin": None,
                "interval": "MISSING",
                "strategy_id": "rsi",
                "direction": "buy",
            },
            "error": None,
        }

    captured = {}

    def fake_run_backtest_service(params):
        captured["params"] = params
        return {"success": True, "summary": {}, "trades": [], "chart_data": []}

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "run_backtest_service", fake_run_backtest_service)

    result = ai_service.process_ai_research(
        prompt="RSI strategy test",
        api_key="AIzaDummyKey",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        provider="gemini",
    )

    assert result["error"] is None
    assert result["backtest_result"] is not None
    assert result["backtest_params"]["coin"] == "BTC"
    assert result["backtest_params"]["interval"] == "4h"
    assert result["backtest_params"]["strategy_id"] == "RSI"
    assert result["backtest_params"]["direction"] == "Long"
    assert result["backtest_params"]["leverage"] == 1
    assert result["backtest_params"]["use_csv"] is True
    assert captured["params"].coin == "BTC"
    assert captured["params"].interval == "4h"
    assert captured["params"].leverage == 1
    assert captured["params"].use_csv is True


def test_process_ai_research_uses_minimal_params_fallback_on_validation_error(monkeypatch):
    def fake_call_gemini(*args, **kwargs):
        return {
            "thought": "ok",
            "params": {
                "coin": "ETH",
                "interval": "1h",
                "strategy_id": "RSI",
                "direction": "Long",
                "sma1_len": 300,
                "sma2_len": 20,
            },
            "error": None,
        }

    captured = {}

    def fake_run_backtest_service(params):
        captured["params"] = params
        return {"success": True, "summary": {}, "trades": [], "chart_data": []}

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "run_backtest_service", fake_run_backtest_service)

    result = ai_service.process_ai_research(
        prompt="RSI strategy test",
        api_key="AIzaDummyKey",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        provider="gemini",
    )

    assert result["error"] is None
    assert result["backtest_result"] is not None
    assert "normalized to safe defaults" in result["answer"]
    assert result["backtest_params"] == {
        "coin": "ETH",
        "interval": "1h",
        "strategy_id": "RSI",
        "direction": "Long",
        "leverage": 1,
        "use_csv": True,
    }
    assert captured["params"].sma1_len == 20
    assert captured["params"].sma2_len == 60
    assert captured["params"].leverage == 1
    assert captured["params"].use_csv is True


def test_process_ai_research_respects_llm_leverage_when_provided(monkeypatch):
    def fake_call_gemini(*args, **kwargs):
        return {
            "thought": "ok",
            "params": {
                "coin": "BTC",
                "interval": "4h",
                "strategy_id": "RSI",
                "direction": "Long",
                "leverage": 50,
            },
            "error": None,
        }

    captured = {}

    def fake_run_backtest_service(params):
        captured["params"] = params
        return {"success": True, "summary": {}, "trades": [], "chart_data": []}

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "run_backtest_service", fake_run_backtest_service)

    result = ai_service.process_ai_research(
        prompt="RSI strategy test",
        api_key="AIzaDummyKey",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        provider="gemini",
    )

    assert result["error"] is None
    assert result["backtest_params"]["leverage"] == 50
    assert captured["params"].leverage == 50


def test_process_ai_research_prompt_leverage_overrides_llm_value(monkeypatch):
    def fake_call_gemini(*args, **kwargs):
        return {
            "thought": "ok",
            "params": {
                "coin": "BTC",
                "interval": "4h",
                "strategy_id": "RSI",
                "direction": "Long",
                "leverage": 3,
            },
            "error": None,
        }

    captured = {}

    def fake_run_backtest_service(params):
        captured["params"] = params
        return {"success": True, "summary": {}, "trades": [], "chart_data": []}

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "run_backtest_service", fake_run_backtest_service)

    result = ai_service.process_ai_research(
        prompt="RSI strategy test, leverage 12x",
        api_key="AIzaDummyKey",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        provider="gemini",
    )

    assert result["error"] is None
    assert result["backtest_params"]["leverage"] == 12
    assert captured["params"].leverage == 12
