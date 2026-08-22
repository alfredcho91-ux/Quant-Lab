"""Transport checks for credential endpoints."""

from __future__ import annotations

import json
import os

from fastapi import HTTPException, Request, status

from backend.config.settings import get_app_environment


def require_secure_credential_transport(request: Request) -> None:
    if get_app_environment() != "production" or _is_secure(request):
        return
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credentials must be sent over HTTPS")


def _is_secure(request: Request) -> bool:
    if request.url.scheme == "https":
        return True
    if os.getenv("TRUST_PROXY_HEADERS", "false").lower() not in {"1", "true", "yes", "on"}:
        return False
    if request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower() == "https":
        return True
    try:
        return json.loads(request.headers.get("cf-visitor", "{}")).get("scheme") == "https"
    except (TypeError, ValueError, json.JSONDecodeError):
        return False


__all__ = ["require_secure_credential_transport"]
