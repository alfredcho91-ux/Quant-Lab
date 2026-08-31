"""Redact credential-shaped values from application log records."""

from __future__ import annotations

import logging
import re
from threading import RLock
from typing import Any

_LOCK = RLock()
_VALUES: set[str] = set()
_INSTALLED = False
_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key|secret(?:[_-]?key)?|passphrase)(\s*[:=]\s*)([^\s,;}&]+)")


def register_sensitive_values(*values: str) -> None:
    with _LOCK:
        _VALUES.update(value for raw in values if len(value := str(raw or "").strip()) >= 4)


def redact_text(value: Any) -> str:
    text = _KEY_PATTERN.sub(r"\1\2[REDACTED]", str(value))
    with _LOCK:
        secrets = tuple(_VALUES)
    for secret in secrets:
        text = text.replace(secret, "[REDACTED]")
    return text


def _redact_log_args(value: Any) -> Any:
    """Redact string arguments without changing formatter-specific tuple shapes."""
    if isinstance(value, tuple):
        return tuple(_redact_log_args(item) for item in value)
    if isinstance(value, list):
        return [_redact_log_args(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_log_args(item) for key, item in value.items()}
    return redact_text(value) if isinstance(value, str) else value


def install_log_redaction() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    previous = logging.getLogRecordFactory()
    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = previous(*args, **kwargs)
        record.msg = redact_text(record.msg)
        record.args = _redact_log_args(record.args)
        return record
    logging.setLogRecordFactory(factory)
    _INSTALLED = True


__all__ = ["install_log_redaction", "register_sensitive_values"]
