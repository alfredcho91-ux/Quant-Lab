"""HTTP routing coverage for application-level routes."""

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
import pytest

from backend import main
from backend.utils.decorators import handle_api_errors


def test_strategies_route_is_registered_before_static_files():
    with TestClient(main.app) as client:
        response = client.get("/api/strategies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["data"], list)
    assert payload["data"]


def test_domain_errors_preserve_http_status_codes():
    with TestClient(main.app) as client:
        response = client.get("/api/strategy-info/not-a-real-strategy")

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


def test_legacy_failure_envelopes_are_promoted_to_http_errors(monkeypatch):
    monkeypatch.setattr(
        "backend.modules.backtest.router.run_backtest_service",
        lambda _params: {"success": False, "error": "Strategy missing not found"},
    )

    with TestClient(main.app) as client:
        response = client.post(
            "/api/backtest",
            json={
                "coin": "BTC",
                "interval": "1h",
                "strategy_id": "missing",
                "direction": "Long",
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": "Strategy missing not found",
        "error_code": "NOT_FOUND",
    }


def test_unhandled_errors_do_not_expose_internal_messages():
    test_app = FastAPI()
    router = APIRouter()

    @router.get("/test-internal-error")
    @handle_api_errors()
    async def fail():
        raise RuntimeError("secret database path: /private/data.db")

    test_app.include_router(router)

    with TestClient(test_app) as client:
        response = client.get("/test-internal-error")

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error": "An unexpected error occurred",
        "error_code": "INTERNAL_ERROR",
    }


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/market/prices"),
        ("get", "/api/market/fear-greed"),
        ("get", "/api/timeframes/{coin}"),
        ("get", "/api/ohlcv/{coin}/{interval}"),
        ("post", "/api/backtest"),
        ("get", "/api/presets"),
        ("post", "/api/presets"),
        ("delete", "/api/presets/{name}"),
        ("get", "/api/strategies"),
        ("get", "/api/strategy-info/{strategy_id}"),
        ("get", "/api/journal"),
        ("get", "/api/journal/current-market"),
        ("get", "/api/journal/sl-tp-analysis"),
        ("delete", "/api/journal/{entry_id}"),
        ("get", "/api/deepcoin/status"),
        ("post", "/api/deepcoin/sync"),
        ("get", "/api/support-resistance/{coin}/{interval}"),
        ("get", "/api/indicators/projection"),
        ("get", "/api/indicators/vpvr-source/{coin}/{interval}"),
        ("get", "/api/indicators/vpvr/{coin}/{interval}"),
        ("get", "/api/indicators/trade-report/{coin}/{interval}"),
        ("post", "/api/bb-mid"),
        ("post", "/api/combo-filter"),
        ("post", "/api/trend-indicators"),
        ("post", "/api/hybrid-analysis"),
        ("post", "/api/hybrid-backtest"),
        ("post", "/api/hybrid-live"),
        ("post", "/api/streak-analysis"),
        ("get", "/api/streak-cache-stats"),
        ("post", "/api/streak-cache-clear"),
        ("post", "/api/ai/research"),
        ("post", "/api/ai/analyst"),
    ],
)
def test_major_routes_publish_typed_success_contracts(method, path):
    operation = main.app.openapi()["paths"][path][method]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]

    assert response_schema
    assert "$ref" in response_schema


def test_removed_personal_only_routes_are_not_published():
    paths = main.app.openapi()["paths"]

    assert "/api/backtest-advanced" not in paths
    assert "/api/pattern-scanner" not in paths
    assert "/api/scanner" not in paths
