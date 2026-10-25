import numpy as np
import pandas as pd
import pytest

from core.indicator_primitives import compute_atr_wilder
from backend.modules.stop_loss_lab.statistics import DAY, describe, prepare, snapshot, weekend_distribution
from backend.modules.stop_loss_lab.schemas import LabRequest


def candles(count=20, step=DAY):
    return pd.DataFrame([{"open_time": i * step, "open": 100, "high": 101 + i % 3, "low": 99, "close": 100, "volume": 1} for i in range(count)])


def test_zero_wicks_even_median_quantiles_and_ecdf():
    result = describe([0, 0, 2, 10], histogram=True)
    assert result["count"] == 4
    assert result["mean"] == 3
    assert result["median"] == 1
    assert result["p95"] == pytest.approx(np.percentile([0, 0, 2, 10], 95))
    assert result["std"] == pytest.approx(np.std([0, 0, 2, 10]))
    assert result["histogram"][0]["count"] == 2
    assert result["ecdf"][-1]["probability_pct"] == 100
    assert describe([0, 0])["mean_median_ratio"] is None
    assert describe([])["mean"] is None


def test_wilder_and_median_reuse_core_completed_only():
    raw = candles()
    result = prepare(raw, "1d", 19 * DAY, 3)
    assert len(result) == 19
    np.testing.assert_allclose(result.atr, compute_atr_wilder(raw.iloc[:19], 3), equal_nan=True)
    assert result.mtr.iloc[-1] == pytest.approx(np.median(result.tr.iloc[-3:]))
    assert snapshot(result.iloc[:2], 3, "1d") is None


def test_prefix_and_weekly_confirmation():
    raw = candles(20, DAY * 7)
    raw.open_time += DAY * 4
    result = prepare(raw, "1w", DAY * 4 + 19 * 7 * DAY, 3)
    assert len(result) == 19
    prefix = prepare(raw.iloc[:10], "1w", DAY * 4 + 19 * 7 * DAY, 3)
    np.testing.assert_allclose(prefix.atr, result.atr.iloc[:10], equal_nan=True)
    bad = raw.copy()
    bad.open_time += DAY
    with pytest.raises(ValueError, match="UTC exchange boundaries"):
        prepare(bad, "1w", 10**15, 3)


@pytest.mark.parametrize("changes", [{"high": 90}, {"close": 0}, {"open": float("nan")}])
def test_invalid_ohlc_is_never_imputed(changes):
    raw = candles()
    for key, value in changes.items():
        raw.loc[3, key] = value
    with pytest.raises(ValueError):
        prepare(raw, "1d", 100 * DAY, 3)


def test_bounded_validation_rejects_bad_grids_and_dates():
    for changes in ({"stop_values": [0]}, {"entry_values": [0.5, 0.5]}, {"target_values": [float("inf")]}, {"end": "2025-01-01"}, {"entry": {"mode": "mae_percentile"}}):
        with pytest.raises(ValueError):
            LabRequest.model_validate({"start": "2025-01-02", "end": "2025-01-10", **changes})


def test_grid_neighbors_use_numerical_order():
    request = LabRequest(start="2025-01-01", end="2025-01-10", stop_values=[1, .3, .5])
    assert request.stop_values == [.3, .5, 1]


def test_weekend_distribution_uses_only_utc_saturday_and_sunday_daily_candles():
    daily = prepare(candles(12), "1d", 12 * DAY, 3)
    result = weekend_distribution(daily, 0, 12 * DAY)

    # Unix epoch day zero is Thursday, so indices 2/3 and 9/10 are Sat/Sun.
    assert result["timezone"] == "UTC"
    assert result["weekdays"] == ["Saturday", "Sunday"]
    assert result["candle_count"] == 4
    assert result["day_counts"] == {"Saturday": 2, "Sunday": 2}
    assert result["metrics"]["upper"]["percent_open"]["count"] == 4
    assert result["metrics"]["upper"]["percent_open"]["mean"] == pytest.approx(1.75)
