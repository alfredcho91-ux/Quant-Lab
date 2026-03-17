"""AI service LLM adapter tests."""

import pytest

from modules.ai_lab import service as ai_service


@pytest.fixture(autouse=True)
def clear_ai_response_cache():
    ai_service.AI_RESPONSE_CACHE.clear()
    yield
    ai_service.AI_RESPONSE_CACHE.clear()


def test_call_gemini_http_error_returns_sanitized_message(monkeypatch):
    class FakeResponse:
        status_code = 400

        def raise_for_status(self):
            raise ai_service.requests.HTTPError("bad request", response=self)

        def json(self):
            return {
                "error": {
                    "message": "API key expired. Please renew the API key.",
                }
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(ai_service.requests, "post", fake_post)
    result = ai_service._call_gemini(
        api_key="AIzaDummyKey",
        prompt="test",
        model=ai_service.GEMINI_DEFAULT_MODEL,
    )

    assert result["params"] is None
    assert result["error"] == "API key expired. Please renew the API key."
    assert "API key expired" in result["thought"]
    assert "AIza" not in result["thought"]
    assert result["error_code"] == ai_service.ERROR_CODE_MODEL_HTTP


def test_call_gemini_plain_text_response_fallback(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "일반 자연어 답변입니다."}]
                        }
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(ai_service.requests, "post", fake_post)
    result = ai_service._call_gemini(
        api_key="AIzaDummyKey",
        prompt="test",
        model=ai_service.GEMINI_DEFAULT_MODEL,
    )

    assert result["error"] is None
    assert result["params"] is None
    assert "일반 자연어 답변" in result["thought"]
    assert result["error_code"] is None


def test_call_gemini_uses_llm_client_adapter(monkeypatch):
    captured = {}

    class FakeClient:
        def generate(self, *, system_prompt, prompt, history=None, temperature=0.2):
            captured["system_prompt"] = system_prompt
            captured["prompt"] = prompt
            return {
                "text": "{\"thought\":\"adapter ok\",\"params\":{\"coin\":\"BTC\",\"interval\":\"1d\",\"strategy_id\":\"RSI\",\"direction\":\"Long\"}}",
                "error": None,
                "error_code": None,
            }

    def fake_build_llm_client(provider, **kwargs):
        captured["provider"] = provider
        captured["kwargs"] = kwargs
        return FakeClient()

    monkeypatch.setattr(ai_service, "build_llm_client", fake_build_llm_client)
    result = ai_service._call_gemini(
        api_key="AIzaDummyKey",
        prompt="test",
        model=ai_service.GEMINI_DEFAULT_MODEL,
    )

    assert captured["provider"] == "gemini"
    assert captured["kwargs"]["api_key"] == "AIzaDummyKey"
    assert captured["kwargs"]["model"] == ai_service.GEMINI_DEFAULT_MODEL
    assert "RSI" in captured["system_prompt"]
    assert result["error"] is None
    assert result["params"]["coin"] == "BTC"
    assert result["thought"] == "adapter ok"


def test_call_gemini_applies_history_role_mapping(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "{\"thought\":\"ok\",\"params\":{}}"}]
                        }
                    }
                ]
            }

    def fake_post(url, json, headers, timeout):
        captured["payload"] = json
        return FakeResponse()

    monkeypatch.setattr(ai_service.requests, "post", fake_post)
    ai_service._call_gemini(
        api_key="AIzaDummyKey",
        prompt="test",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        history=[
            {"role": "assistant", "content": "prev answer"},
            {"role": "user", "content": "prev question"},
        ],
    )

    roles = [entry.get("role") for entry in captured["payload"]["contents"]]
    assert "model" in roles
    assert roles.count("user") >= 2


def test_call_gemini_handles_empty_candidates_with_error_code(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {}

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(ai_service.requests, "post", fake_post)
    result = ai_service._call_gemini(
        api_key="AIzaDummyKey",
        prompt="test",
        model=ai_service.GEMINI_DEFAULT_MODEL,
    )

    assert result["params"] is None
    assert result["error_code"] == ai_service.ERROR_CODE_MODEL_RESPONSE_EMPTY


def test_call_gemini_sends_api_key_in_header_not_query(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "{\"thought\":\"ok\",\"params\":{}}"}]
                        }
                    }
                ]
            }

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(ai_service.requests, "post", fake_post)
    ai_service._call_gemini(
        api_key="AIzaDummyKey",
        prompt="test",
        model=ai_service.GEMINI_DEFAULT_MODEL,
    )

    assert "?key=" not in captured["url"]
    assert captured["headers"]["x-goog-api-key"] == "AIzaDummyKey"


def test_run_data_analyst_agent_returns_error_when_tool_fails(monkeypatch):
    class FakeClient:
        def generate(self, **kwargs):
            return {
                "text": None,
                "error": None,
                "error_code": None,
                "function_call": {
                    "name": "execute_pandas_code",
                    "args": {"code": "result = 1"},
                },
            }

    monkeypatch.setattr(ai_service, "build_llm_client", lambda *args, **kwargs: FakeClient())
    
    # Updated mock to return a dictionary as expected by the service layer
    monkeypatch.setattr(ai_service, "execute_pandas_code", lambda *args, **kwargs: {"success": False, "error": "sandbox timed out"})

    result = ai_service.run_data_analyst_agent(
        api_key="AIzaDummyKey",
        coin="BTC",
        interval="1d",
        user_prompt="analyze",
        model=ai_service.GEMINI_DEFAULT_MODEL,
    )

    assert result["success"] is False
    assert result["execution_path"] == "tool_execution_error"
    assert "sandbox timed out" in str(result["error"])


def test_run_data_analyst_agent_returns_success_after_tool_followup(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.calls = 0

        def generate(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return {
                    "text": None,
                    "error": None,
                    "error_code": None,
                    "function_call": {
                        "name": "execute_pandas_code",
                        "args": {"code": "result = 1"},
                    },
                }
            return {
                "text": "analysis ok",
                "error": None,
                "error_code": None,
                "function_call": None,
            }

    fake_client = FakeClient()
    monkeypatch.setattr(ai_service, "build_llm_client", lambda *args, **kwargs: fake_client)
    monkeypatch.setattr(ai_service, "execute_pandas_code", lambda *args, **kwargs: "42")

    result = ai_service.run_data_analyst_agent(
        api_key="AIzaDummyKey",
        coin="BTC",
        interval="1d",
        user_prompt="analyze",
        model=ai_service.GEMINI_DEFAULT_MODEL,
    )

    assert result["success"] is True
    assert result["execution_path"] == "tool_then_llm"
    assert result["answer"] == "analysis ok"
