"""LLM client adapters used by AI backtest service."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Protocol, TypedDict

import requests

ERROR_CODE_MODEL_HTTP = "MODEL_HTTP_ERROR"
ERROR_CODE_MODEL_NETWORK = "MODEL_NETWORK_ERROR"
ERROR_CODE_MODEL_RESPONSE_EMPTY = "MODEL_RESPONSE_EMPTY"
ERROR_CODE_MODEL_RESPONSE_FORMAT = "MODEL_RESPONSE_FORMAT"


class LLMGenerateResult(TypedDict):
    text: Optional[str]
    error: Optional[str]
    error_code: Optional[str]


class LLMClient(Protocol):
    def generate(
        self,
        *,
        system_prompt: str,
        prompt: str,
        history: Optional[list] = None,
        temperature: float = 0.2,
        tools: Optional[list] = None,
    ) -> LLMGenerateResult:
        ...


def _build_gemini_history(history: Optional[list]) -> list[Dict[str, Any]]:
    """Convert client history to Gemini contents format."""
    if not isinstance(history, list):
        return []

    contents: list[Dict[str, Any]] = []
    for item in history[-12:]:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, str):
            continue
        text = content.strip()
        if not text:
            continue

        role_raw = str(item.get("role", "user")).strip().lower()
        role = "model" if role_raw in {"assistant", "model", "ai"} else "user"
        contents.append({"role": role, "parts": [{"text": text}]})

    return contents


def _extract_gemini_text(data: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return None, "Gemini response has no candidates.", ERROR_CODE_MODEL_RESPONSE_EMPTY, None

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list) or not parts:
            continue
        
        for part in parts:
            if isinstance(part, dict) and "functionCall" in part:
                return None, None, None, part["functionCall"]
                
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str) and part.get("text").strip():
                return part["text"], None, None, None

    finish_reason = None
    first_candidate = candidates[0]
    if isinstance(first_candidate, dict):
        finish_reason = first_candidate.get("finishReason")

    if finish_reason:
        return (
            None,
            f"Gemini returned no text output (finishReason={finish_reason}).",
            ERROR_CODE_MODEL_RESPONSE_EMPTY,
            None
        )
    return None, "Gemini returned no text output.", ERROR_CODE_MODEL_RESPONSE_EMPTY, None


class GeminiClient:
    """Gemini REST adapter. Returns text/error contract to upper service layer."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
        http_post: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._http_post = http_post or requests.post

    def generate(
        self,
        *,
        system_prompt: str,
        prompt: str,
        history: Optional[list] = None,
        temperature: float = 0.2,
        tools: Optional[list] = None,
    ) -> LLMGenerateResult:
        # API key is sent via header to avoid leaking secrets in URL/query logs.
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent"

        contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
        contents.extend(_build_gemini_history(history))
        contents.append({"role": "user", "parts": [{"text": f"Request: {prompt}"}]})

        safe_temperature = min(1.0, max(0.0, float(temperature)))
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": safe_temperature,
                "maxOutputTokens": 1000,
            },
        }
        
        if tools:
            payload["tools"] = tools

        try:
            response = self._http_post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self._api_key,
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            text, extract_error, extract_error_code, function_call = _extract_gemini_text(data)
            return {
                "text": text,
                "error": extract_error,
                "error_code": extract_error_code,
                "function_call": function_call
            }
        except requests.HTTPError as exc:
            response = exc.response
            status = response.status_code if response is not None else None
            api_message = None
            if response is not None:
                try:
                    payload_json = response.json()
                    api_message = payload_json.get("error", {}).get("message")
                except ValueError:
                    api_message = None
            safe_message = api_message or f"HTTP {status or 'error'} from Gemini API."
            return {
                "text": None,
                "error": safe_message,
                "error_code": ERROR_CODE_MODEL_HTTP,
                "function_call": None
            }
        except requests.RequestException as exc:
            safe_message = f"Network error while calling Gemini API: {exc.__class__.__name__}"
            return {
                "text": None,
                "error": safe_message,
                "error_code": ERROR_CODE_MODEL_NETWORK,
                "function_call": None
            }
        except Exception:
            return {
                "text": None,
                "error": "Unexpected response format from Gemini API.",
                "error_code": ERROR_CODE_MODEL_RESPONSE_FORMAT,
                "function_call": None
            }


def build_llm_client(
    provider: str,
    *,
    api_key: str,
    model: str,
    http_post: Optional[Callable[..., Any]] = None,
) -> LLMClient:
    provider_norm = (provider or "").strip().lower()
    if provider_norm == "gemini":
        return GeminiClient(api_key=api_key, model=model, http_post=http_post)
    raise ValueError(f"Unsupported LLM provider: {provider_norm}")
