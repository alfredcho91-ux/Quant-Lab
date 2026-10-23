from datetime import datetime, timezone

import pandas as pd
import pytest

from backend.modules.stop_loss_lab.schemas import LabRequest, Distance
from backend.modules.stop_loss_lab.statistics import DAY, prepare, snapshot, distributions
from backend.modules.stop_loss_lab.simulation import execute, metrics, make_sessions, simulate, optimize, distance, partition, breakout_distribution
from backend.modules.stop_loss_lab.service import analyze


HOUR = 3600000
START = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()*1000)


def config(**changes):
    return LabRequest.model_validate({"start": "2025-01-01", "end": "2025-01-20", "lookback": 3, "execution_interval": "1h", "fee_bps": 0, "slippage_bps": 0, "min_trades": 3, **changes})


def path(*rows):
    return [{"open_time": START+i*HOUR, "end_time": START+(i+1)*HOUR, "open": row[0], "high": row[1], "low": row[2], "close": row[3]} for i, row in enumerate(rows)]


def fixture():
    reference = pd.DataFrame([{"open_time": START+i*DAY, "open": 100, "high": 101, "low": 99, "close": 100} for i in range(-40, 21)])
    execution = pd.DataFrame([{"open_time": START+i*HOUR, "open": 100, "high": 102 if i % 24 == 0 else 100.5, "low": 99.5, "close": 100} for i in range(21*24)])
    return prepare(reference, "1d", START+21*DAY, 3), prepare(execution, "1h", START+21*DAY, 3)


@pytest.mark.parametrize("side,rows,entry", [("Long", [(100, 104, 96, 100)], 100), ("Short", [(100, 104, 96, 100)], 100)])
def test_same_bar_both_barriers_is_conservative_stop(side, rows, entry):
    trade = execute(path(*rows), side, entry, 2, 3, config())
    assert trade["reason"] == "stop" and trade["ambiguous"]
    assert trade["r_multiple"] == -1


@pytest.mark.parametrize("side,rows,expected", [
    ("Long", [(100, 101, 99, 100), (95, 96, 94, 95)], 95),
    ("Short", [(100, 101, 99, 100), (105, 106, 104, 105)], 105),
])
def test_stop_market_gaps_fill_at_open_not_ideal_stop(side, rows, expected):
    trade = execute(path(*rows), side, 100, 2, 3, config())
    assert trade["reason"] == "stop" and trade["exit_price"] == expected
    assert trade["r_multiple"] == -2.5


def test_intrabar_target_before_entry_is_not_invented():
    outcome = execute(path((99, 101, 97, 100)), "Short", 100, 2, 2, config())
    assert outcome["status"] == "entry_order_unknown"
    confirmed = execute(path((99, 101, 97, 97)), "Short", 100, 2, 2, config())
    assert confirmed["reason"] == "target"


def test_costs_real_timeout_and_risk_sizing():
    req = config(fee_bps=5, slippage_bps=2)
    trade = execute(path((100, 101, 99, 100), (100, 101, 99, 100.5)), "Long", 100, 2, 4, req)
    assert trade["reason"] == "timeout"
    assert trade["entry_price"] == pytest.approx(100.02)
    assert trade["exit_price"] == pytest.approx(100.5*.9998)
    expected = trade["exit_price"]-trade["entry_price"]-(trade["exit_price"]+trade["entry_price"])*.0005
    assert trade["unit_pnl"] == pytest.approx(expected)
    summary, sized = metrics([trade], req)
    assert sized[0]["quantity"] == 50
    assert summary["equity"] == pytest.approx(10000+50*expected)
    other = metrics([trade], config(fee_bps=5, slippage_bps=2, risk_pct=2))[1][0]
    assert other["quantity"] == pytest.approx(min(100, 10000/100.02))
    assert trade["mae_lower_pct"] <= trade["mae_upper_pct"]


def test_gap_loss_is_not_clipped_and_bankrupt_account_stops():
    trade = execute(path((100, 100.5, 99.5, 100), (250, 251, 249, 250)), "Short", 100, 1, 3, config())
    result, rows = metrics([trade, trade], config())
    assert len(rows) == 1
    assert result["equity"] == -5000
    assert result["max_drawdown_pct"] == 150


def test_reference_orders_use_only_past_and_unchanged_prefix():
    reference, execution = fixture()
    req = config()
    sessions, _ = make_sessions(req, reference, execution, START, START+20*DAY, .5)
    assert sessions[0]["orders"][0]["trigger"] == pytest.approx(101*1.005)
    changed = reference.copy()
    changed.loc[changed.open_time >= START+10*DAY, ["high", "low"]] = [1000, 1]
    later, _ = make_sessions(req, changed, execution, START, START+20*DAY, .5)
    assert [s["orders"] for s in sessions[:10]] == [s["orders"] for s in later[:10]]
    assert sessions[0]["orders"][0]["conditional"] == []
    assert len(sessions[1]["orders"][0]["conditional"]) == 1


def test_missing_execution_candle_is_explicit_not_filled():
    reference, execution = fixture()
    execution = execution.drop(5).reset_index(drop=True)
    sessions, counts = make_sessions(config(), reference, execution, START, START+2*DAY, .5)
    assert counts["execution_gap"] == 1 and len(sessions) == 1


def test_zero_distance_stop_unavailable_and_conditional_requires_prior_samples():
    reference, execution = fixture()
    req = config(stop={"mode": "mae_percentile"})
    sessions, _ = make_sessions(req, reference, execution, START, START+6*DAY, .5)
    trades, counts = simulate(req, sessions, execution, 1, 1.5)
    assert counts["insufficient_conditional_sample"] == 3
    assert all(t["conditional_sample_size"] >= 3 for t in trades)
    state = snapshot(reference, 3, "1d")
    assert distance(Distance(mode="wick_mean"), 2, 100, state, "Short", reference, []) == 2


def test_period_end_and_holding_horizon_and_reentry():
    reference, execution = fixture()
    req = config(exit_rule="holding_hours", holding_hours=4)
    sessions, _ = make_sessions(req, reference, execution, START, START+2*DAY, .5)
    trades, _ = simulate(req, sessions, execution, 10, 10)
    assert trades and all(t["holding_hours"] == 4 for t in trades)
    assert all(t["exit_price"] == 100 for t in trades)
    # No access to the missing future horizon; never assume a close.
    truncated = execution.loc[execution.open_time < START+2*HOUR]
    _, counts = simulate(req, sessions[:1], truncated, 10, 10)
    assert counts["incomplete_holding_horizon"] == 1


def test_percent_open_distributions_differ_from_close_and_keep_zeros():
    reference, _ = fixture()
    reference.loc[reference.open_time == START, ["high", "close"]] = [104, 102]
    reference = prepare(reference, "1d", START+21*DAY, 3)
    result = distributions({"1d": reference}, START, START+DAY)["1d"]["metrics"]
    assert result["upper"]["percent_open"]["mean"] == 2
    assert result["upper"]["price"]["mean"] == 2


def test_optimization_reproducible_purged_and_not_selected_from_test():
    reference, execution = fixture()
    req = config(entry_values=[.3, .5], stop_values=[.5, 1], target_values=[1, 1.5])
    first = optimize(req, reference, execution, START, START+20*DAY)
    assert first == optimize(req, reference, execution, START, START+20*DAY)
    split = first["split_time"]
    altered = execution.copy()
    altered.loc[altered.open_time >= split, ["high", "low", "close"]] = [110, 90, 105]
    other = optimize(req, reference, altered, START, START+20*DAY)
    assert first["selected_id"] == other["selected_id"]
    assert [c["train"] for c in first["candidates"]] == [c["train"] for c in other["candidates"]]
    assert len(first["walk_forward"]) == 3
    for candidate in first["candidates"]:
        assert all(t["exit_time"] <= split for t in partition(candidate["trades"], START, split))
    assert partition([{"entry_time": split-1, "exit_time": split+1}], START, split) == []


def test_breakout_statistics_are_separate_from_conditional_entry():
    reference, execution = fixture()
    # Increasing completed highs create descriptive overshoots.
    reference.loc[reference.open_time >= START, "high"] = 102
    output = breakout_distribution(reference, execution, "1d", START, START+2*DAY)
    assert output["Short"]["depth_pct"]["count"] == 1
    assert output["Short"]["returns_confirmed"] == 1


def test_reference_gap_rejected_before_wilder_calculation():
    reference, _ = fixture()
    with pytest.raises(ValueError, match="contains gaps"):
        prepare(reference.drop(5), "1d", START+21*DAY, 3)


def test_both_sides_same_candle_order_is_unknown_and_reentry_is_bounded():
    reference, execution = fixture()
    execution.loc[0, ["high", "low"]] = [103, 97]
    req = config(direction="Both")
    sessions, _ = make_sessions(req, reference, execution, START, START+DAY, 0)
    trades, counts = simulate(req, sessions, execution, .5, 1.5)
    assert trades == [] and counts["both_direction_order_unknown"] == 1
    req = config(max_entries_per_period=3)
    execution.loc[:23, "high"] = 103
    sessions, _ = make_sessions(req, reference, execution, START, START+DAY, 0)
    trades, counts = simulate(req, sessions, execution, .5, 1.5)
    assert len(trades) == 3 and counts["filled"] == 3
    assert trades[0]["exit_time"] <= trades[1]["entry_time"]


def test_weekly_sessions_start_monday_and_need_completed_previous_week():
    from backend.modules.stop_loss_lab.statistics import INTERVAL_MS
    reference, execution = fixture()
    monday = START+5*DAY
    weekly = pd.DataFrame([{"open_time": monday+i*7*DAY, "open": 100, "high": 101, "low": 99, "close": 100} for i in range(-5, 3)])
    weekly = prepare(weekly, "1w", monday+21*DAY, 3)
    req = config(reference_interval="1w")
    sessions, _ = make_sessions(req, weekly, execution, START, START+20*DAY, .5)
    assert len(sessions) == 2
    assert sessions[0]["opening"] == monday
    assert sessions[0]["state"]["last"].end_time == monday
    assert sessions[0]["closing"]-monday == INTERVAL_MS["1w"]


def test_service_uses_bounded_historical_public_source_and_content_fingerprint():
    reference, execution = fixture()
    weekly = pd.DataFrame([{"open_time": (START//(7*DAY))*7*DAY+4*DAY+i*7*DAY, "open": 100, "high": 103, "low": 97, "close": 100} for i in range(-20, 4)])
    calls = []
    def fetch(symbol, interval, **kwargs):
        calls.append((symbol, interval, kwargs))
        return {"1d": reference, "1w": weekly, "1h": execution}[interval].copy()
    result = analyze(config(), now=datetime(2025, 2, 1, tzinfo=timezone.utc), fetch=fetch)
    assert len(calls) == 3
    assert all(c[0] == "BTCUSDT" and c[2]["end_time"] == START+20*DAY-1 for c in calls)
    assert len(result["data"]["fingerprint_sha256"]) == 64
    assert result == analyze(config(), now=datetime(2025, 2, 1, tzinfo=timezone.utc), fetch=fetch)


def test_router_validates_before_fetch_and_offloads(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.modules.stop_loss_lab import router as module
    app = FastAPI()
    app.include_router(module.router)
    calls = []
    monkeypatch.setattr(module, "analyze", lambda request: calls.append(request.coin) or {"ok": True})
    with TestClient(app) as client:
        assert client.post("/api/stop-loss-lab/analyze", json={"start": "bad"}).status_code == 422
        assert not calls
        response = client.post("/api/stop-loss-lab/analyze", json=config().model_dump(mode="json"))
        assert response.json() == {"success": True, "data": {"ok": True}}
        monkeypatch.setattr(module, "analyze", lambda request: (_ for _ in ()).throw(ValueError("No market data")))
        assert client.post("/api/stop-loss-lab/analyze", json=config().model_dump(mode="json")).status_code == 422


@pytest.mark.parametrize("mode", ["fixed_pct", "atr", "mtr", "wick_mean", "wick_median", "wick_percentile", "breakout_percentile", "mae_percentile"])
def test_distance_modes_never_use_the_execution_candle(mode):
    reference, _ = fixture()
    state = snapshot(reference, 3, "1d")
    value = distance(Distance(mode=mode), 1, 100, state, "Short", reference, [1, 2, 3])
    if mode == "breakout_percentile":
        assert value is None  # No previous-high breakouts in flat reference data.
    else:
        assert value is not None and value > 0


def test_reference_choices_require_confirmed_nonzero_information():
    from backend.modules.stop_loss_lab.simulation import reference_price
    reference, _ = fixture()
    state = snapshot(reference, 3, "1d")
    assert reference_price(state, "Short", "previous_close") == 100
    assert reference_price(state, "Long", "previous_open") == 100
    state["last"] = state["last"].copy()
    state["last"]["upper"] = 0
    assert reference_price(state, "Short", "wick_extreme") is None
    state["last"]["swing_high_price"] = float("nan")
    assert reference_price(state, "Short", "confirmed_swing") is None


def test_holdout_order_exclusions_cannot_change_training_selection():
    reference, execution = fixture()
    req = config(entry_values=[.3, .5])
    baseline = optimize(req, reference, execution, START, START+20*DAY)
    changed = execution.loc[execution.open_time != baseline["split_time"]+3*HOUR].copy()
    other = optimize(req, reference, changed, START, START+20*DAY)
    assert baseline["selected_id"] == other["selected_id"]
    assert [c["train_quality_exclusions"] for c in baseline["candidates"]] == [c["train_quality_exclusions"] for c in other["candidates"]]


def test_nonfinite_derived_risk_levels_are_rejected_not_serialized_as_infinity():
    assert execute(path((100, 101, 99, 100)), "Long", 100, 1e-310, 1e7, config())["status"] == "invalid_levels"


def test_historical_fetch_seed_is_anchored_to_start_even_when_end_extends():
    # An end date extension must not shift the initial Wilder candle.
    import backend.modules.stop_loss_lab.service as module
    calls = []
    def fetch(symbol, interval, total_candles, end_time):
        from backend.modules.stop_loss_lab.statistics import INTERVAL_MS
        step = INTERVAL_MS[interval]
        anchor = 4*DAY if interval == "1w" else 0
        last = ((end_time-anchor)//step)*step+anchor
        calls.append((interval, last-(total_candles-1)*step))
        return pd.DataFrame([{"open_time": last-i*step, "open": 100, "high": 102, "low": 98, "close": 100} for i in reversed(range(total_candles))])
    first = module.analyze(config(end="2025-01-20"), now=datetime(2025, 2, 1, tzinfo=timezone.utc), fetch=fetch)
    second = module.analyze(config(end="2025-01-22"), now=datetime(2025, 2, 1, tzinfo=timezone.utc), fetch=fetch)
    assert calls[:3] == calls[3:]
    assert first["candidates"][0]["trades"] == [t for t in second["candidates"][0]["trades"] if t["reference_time"] < START+20*DAY]
