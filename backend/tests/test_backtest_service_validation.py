"""Fast-failure behavior for backtest service validation."""

import pytest

from backend.modules.backtest import service
from backend.modules.backtest.schemas import AdvancedBacktestParams, BacktestParams


@pytest.mark.parametrize(
    ("runner", "params"),
    [
        (service.run_backtest_service, BacktestParams(strategy_id="missing")),
        (
            service.run_backtest_advanced_service,
            AdvancedBacktestParams(strategy_id="missing"),
        ),
    ],
)
def test_unknown_strategy_fails_before_loading_market_data(monkeypatch, runner, params):
    def fail_if_called(_params):
        pytest.fail("market data should not load for an unknown strategy")

    monkeypatch.setattr(service, "_load_and_prepare_data", fail_if_called)

    result = runner(params)

    assert result == {
        "success": False,
        "error": "Strategy missing not found",
    }
