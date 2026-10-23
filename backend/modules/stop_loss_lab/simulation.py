"""Reference-level touch experiments, not an order execution service.

Orders use completed reference history; execution candles never set their levels.
Unknown entry-bar order is excluded, not silently turned into a profitable fill.
"""
from collections import Counter
from datetime import datetime, timezone
from itertools import product
import math

import numpy as np

from backend.modules.journal.sl_tp_analysis import performance
from .statistics import DAY, INTERVAL_MS, describe, finite, historical_breakouts, snapshot


def distance(spec, value, basis, state, side, history, conditional):
    mode = spec.mode
    if mode == "fixed_pct":
        return basis * value / 100
    if mode in ("atr", "mtr"):
        return state[mode] * value
    wicks = state["window"]["upper" if side == "Short" else "lower"].to_numpy()
    if mode == "wick_mean":
        return float(np.mean(wicks)) * value
    if mode == "wick_median":
        return float(np.median(wicks)) * value
    if mode == "wick_percentile":
        return float(np.percentile(wicks, spec.percentile)) * value
    samples = historical_breakouts(history, side, len(state["window"])) if mode == "breakout_percentile" else conditional
    if not samples:
        return None
    return basis * float(np.percentile(samples, spec.percentile)) / 100 * value


def reference_price(state, side, mode):
    last = state["last"]
    if mode == "previous_close":
        return float(last.close)
    if mode == "previous_open":
        return float(last.open)
    if mode == "confirmed_swing":
        return finite(last.swing_high_price if side == "Short" else last.swing_low_price)
    if mode == "wick_extreme" and last["upper" if side == "Short" else "lower"] <= 0:
        return None
    return float(last.high if side == "Short" else last.low)


def trigger_index(path, side, trigger, after=0):
    key = "high" if side == "Short" else "low"
    return next((i for i in range(after, len(path)) if (path[i][key] >= trigger if side == "Short" else path[i][key] <= trigger)), None)


def excursion(path, entry, side, exit_price=None):
    """OHLC upper bounds include uncertain entry/exit-bar extremes.

    Open prices of subsequent bars are observable while holding, hence lower
    bounds; do not advertise full-bar extrema as exact post-entry excursions.
    """
    sign = 1 if side == "Long" else -1
    known = [entry] + [b["open"] for b in path[1:]] + ([] if exit_price is None else [exit_price])
    all_prices = known + [v for b in path for v in (b["high"], b["low"])]
    def bounds(prices):
        returns = [(price / entry - 1) * sign * 100 for price in prices]
        return max(0., -min(returns)), max(0., max(returns))
    lower_mae, lower_mfe = bounds(known)
    upper_mae, upper_mfe = bounds(all_prices)
    return {"mae_lower_pct": lower_mae, "mae_upper_pct": upper_mae,
            "mfe_lower_pct": lower_mfe, "mfe_upper_pct": upper_mfe}


def execute(path, side, trigger, stop_distance, target_distance, request):
    """Path starts at first trigger candle and ends at the fixed exit horizon."""
    sign = 1 if side == "Long" else -1
    first = path[0]
    at_open = first["open"] <= trigger if side == "Long" else first["open"] >= trigger
    base_entry = first["open"] if at_open else trigger
    entry = base_entry * (1 + sign * request.slippage_bps / 10000)
    stop = entry - sign * stop_distance
    target = entry + sign * target_distance
    if not all(math.isfinite(v) for v in (entry, stop, target, stop_distance, target_distance)) or min(entry, stop, target) <= 0 or stop_distance <= 0 or target_distance <= 0:
        return {"status": "invalid_levels"}
    planned_r = target_distance / stop_distance
    if not math.isfinite(planned_r):
        return {"status": "invalid_levels"}
    reason, raw_exit, index, ambiguous = "timeout", path[-1]["close"], len(path) - 1, False
    for i, bar in enumerate(path):
        stop_hit = bar["low"] <= stop if side == "Long" else bar["high"] >= stop
        target_hit = bar["high"] >= target if side == "Long" else bar["low"] <= target
        # An opening gap establishes ordering before the rest of this candle.
        if i > 0 and (bar["open"] <= stop if side == "Long" else bar["open"] >= stop):
            reason, raw_exit, index = "stop", bar["open"], i
            break
        if i > 0 and (bar["open"] >= target if side == "Long" else bar["open"] <= target):
            reason, raw_exit, index = "target", bar["open"], i
            break
        if stop_hit:
            reason, raw_exit, index, ambiguous = "stop", stop, i, bool(target_hit)
            break
        if target_hit:
            # Before an intrabar entry, this candle's target-side extreme may
            # already have occurred. A favorable close proves a later crossing.
            crossed_at_close = bar["close"] >= target if side == "Long" else bar["close"] <= target
            if i == 0 and not at_open and not crossed_at_close:
                return {"status": "entry_order_unknown"}
            reason, raw_exit, index = "target", target, i
            break
    exit_price = raw_exit * (1 - sign * request.slippage_bps / 10000)
    unit_fee = (entry + exit_price) * request.fee_bps / 10000
    unit_pnl = sign * (exit_price - entry) - unit_fee
    realised_r = unit_pnl / stop_distance
    if not all(math.isfinite(v) for v in (exit_price, unit_fee, unit_pnl, realised_r)):
        return {"status": "invalid_levels"}
    later = path[index + 1:]
    later_target = any(b["high"] >= target if side == "Long" else b["low"] <= target for b in later)
    return {"status": "evaluated", "side": side, "entry_time": int(first["open_time"]),
            "exit_time": int(path[index]["end_time"]), "entry_price": entry, "exit_price": exit_price,
            "stop_price": stop, "target_price": target, "stop_distance": stop_distance,
            "planned_rr": planned_r, "r_multiple": realised_r,
            "unit_pnl": unit_pnl, "unit_fee": unit_fee, "reason": reason,
            "stop_hit": reason == "stop", "tp_hit": reason == "target", "ambiguous": ambiguous,
            "intrabar_entry": not at_open, "holding_hours": (path[index]["end_time"] - first["open_time"]) / 3600000,
            "post_stop_target": later_target if reason == "stop" else None,
            "post_stop_same_bar_unknown": bool(reason == "stop" and ambiguous),
            **excursion(path[:index + 1], entry, side, exit_price)}


def metrics(trades, request):
    """Replay position sizing from fresh equity for each evaluation slice."""
    equity, peak, drawdown, streak, maximum_streak = request.initial_equity, request.initial_equity, 0., 0, 0
    evaluated = []
    for original in trades:
        if equity <= 0:
            break
        trade = original.copy()
        quantity = min(equity * request.risk_pct / 100 / trade["stop_distance"], equity / trade["entry_price"]) if request.sizing == "risk" else equity * request.allocation_pct / 100 / trade["entry_price"]
        pnl = quantity * trade["unit_pnl"]
        trade.update(quantity=quantity, pnl=pnl, fees=quantity * trade["unit_fee"], return_pct=pnl / equity * 100)
        equity += pnl
        peak = max(peak, equity)
        drawdown = max(drawdown, (peak - equity) / peak * 100)
        streak = streak + 1 if pnl < 0 else 0
        maximum_streak = max(maximum_streak, streak)
        evaluated.append(trade)
    result = performance(evaluated)
    gross_loss = abs(sum(t["pnl"] for t in evaluated if t["pnl"] < 0))
    result["profit_factor"] = sum(t["pnl"] for t in evaluated if t["pnl"] > 0)/gross_loss if gross_loss else None
    r_values = [t["r_multiple"] for t in evaluated]
    wins, losses = [r for r in r_values if r > 0], [r for r in r_values if r < 0]
    n = len(evaluated)
    p = len(wins) / n if n else 0
    z = 1.96
    centre = (p + z*z/(2*n))/(1+z*z/n) if n else 0
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n) if n else 0
    se = float(np.std(r_values, ddof=1) / math.sqrt(n)) if n > 1 else None
    stops = [t for t in evaluated if t["stop_hit"]]
    result.update(cumulative_return_pct=(equity / request.initial_equity - 1) * 100,
                  max_drawdown_pct=drawdown, max_loss_streak=maximum_streak, equity=equity,
                  realised_payoff=float(np.mean(wins) / abs(np.mean(losses))) if wins and losses else None,
                  planned_rr=float(np.mean([t["planned_rr"] for t in evaluated])) if n else None,
                  mean_holding_hours=float(np.mean([t["holding_hours"] for t in evaluated])) if n else None,
                  win_rate_ci95=[max(0, centre-half)*100, min(1, centre+half)*100] if n else None,
                  ev_r_ci95=[float(np.mean(r_values))-z*se, float(np.mean(r_values))+z*se] if se is not None else None,
                  sufficient_sample=n >= request.min_trades,
                  post_stop_target_pct=sum(t["post_stop_target"] for t in stops)/len(stops)*100 if stops else None,
                  post_stop_count=len(stops), fees=sum(t["fees"] for t in evaluated),
                  **{key: float(np.mean([t[key] for t in evaluated])) if n else None for key in ("mae_lower_pct", "mae_upper_pct", "mfe_lower_pct", "mfe_upper_pct")})
    return result, evaluated


def make_sessions(request, reference, execution, start, end, entry_value, issues=None):
    step, period = INTERVAL_MS[request.execution_interval], INTERVAL_MS[request.reference_interval]
    anchor = 4 * DAY if request.reference_interval == "1w" else 0
    first = ((start - anchor + period - 1) // period) * period + anchor
    sides = ["Long", "Short"] if request.direction == "Both" else [request.direction]
    sessions, conditional, skipped = [], {side: [] for side in sides}, Counter()
    if first > start:
        skipped["incomplete_reference_period"] += 1
    records = execution.to_dict("records")
    times = execution.open_time.to_numpy()
    for opening in range(first, end, period):
        closing = opening + period
        if closing > end:
            skipped["incomplete_reference_period"] += 1
            continue
        history = reference.loc[reference.end_time <= opening]
        state = snapshot(history, request.lookback, request.reference_interval)
        if state is None or int(state["last"].end_time) != opening:
            skipped["insufficient_reference_history"] += 1
            continue
        path = records[int(np.searchsorted(times, opening)):int(np.searchsorted(times, closing))]
        if len(path) != period // step or not path or path[0]["open_time"] != opening or any(b["open_time"] != opening+i*step for i, b in enumerate(path)):
            skipped["execution_gap"] += 1
            if issues is not None:
                issues.append((closing, "execution_gap"))
            continue
        orders = []
        for side in sides:
            level = reference_price(state, side, request.reference)
            offset = distance(request.entry, entry_value, level, state, side, history, []) if level is not None else None
            if offset is None:
                skipped["unavailable_entry_statistic"] += 1
                continue
            trigger = level + (offset if side == "Short" else -offset)
            if trigger <= 0:
                skipped["invalid_entry_level"] += 1
                continue
            observed = [v for available, v in conditional[side] if available <= opening][-request.lookback:]
            orders.append({"side": side, "reference_price": level, "trigger": trigger, "conditional": observed})
            # Calibration uses the FIRST qualifying entry, independent of any
            # stop/target grid. Samples become available only after its horizon.
            index = trigger_index(path, side, trigger)
            if index is not None:
                entry_bar = path[index]
                horizon = closing if request.exit_rule == "period_end" else int(entry_bar["open_time"] + request.holding_hours*3600000)
                tail = records[int(np.searchsorted(times, entry_bar["open_time"])):int(np.searchsorted(times, horizon))]
                if tail and tail[-1]["end_time"] == horizon and len(tail)*step == horizon-entry_bar["open_time"]:
                    base = min(entry_bar["open"], trigger) if side == "Long" else max(entry_bar["open"], trigger)
                    observed_entry = base * (1 + (1 if side == "Long" else -1) * request.slippage_bps / 10000)
                    conditional[side].append((horizon, excursion(tail, observed_entry, side)["mae_upper_pct"]))
        sessions.append({"opening": opening, "closing": closing, "orders": orders, "path": path,
                         "state": state, "history": history, "regime": state["regime"], "volatility_regime": state["volatility_regime"]})
    return sessions, dict(skipped)


def simulate(request, sessions, execution, stop_value, target_value, issues=None):
    records, times = execution.to_dict("records"), execution.open_time.to_numpy()
    trades, counts, busy_until = [], Counter(), 0
    equity = request.initial_equity
    step = INTERVAL_MS[request.execution_interval]
    for session in sessions:
        if equity <= 0:
            counts["bankrupt_periods_not_traded"] += 1
            continue
        counts["signals"] += len(session["orders"])
        after = max(0, (busy_until - session["opening"] + step-1)//step)
        for _ in range(request.max_entries_per_period):
            if _ > 0 and after < len(session["path"]):
                counts["signals"] += len(session["orders"])
            candidates = [(index, order) for order in session["orders"] if (index := trigger_index(session["path"], order["side"], order["trigger"], after)) is not None]
            if not candidates:
                break
            candidates.sort(key=lambda item: item[0])
            index, order = candidates[0]
            if len(candidates) > 1 and candidates[1][0] == index:
                counts["both_direction_order_unknown"] += 1
                if issues is not None:
                    issues.append((session["path"][index]["end_time"], "both_direction_order_unknown"))
                break
            first = session["path"][index]
            horizon = session["closing"] if request.exit_rule == "period_end" else int(first["open_time"] + request.holding_hours*3600000)
            path = records[int(np.searchsorted(times, first["open_time"])):int(np.searchsorted(times, horizon))]
            if not path or path[-1]["end_time"] != horizon or len(path)*step != horizon-first["open_time"]:
                counts["incomplete_holding_horizon"] += 1
                if issues is not None:
                    issues.append((horizon, "incomplete_holding_horizon"))
                break
            side = order["side"]
            sign = 1 if side == "Long" else -1
            base = min(first["open"], order["trigger"]) if side == "Long" else max(first["open"], order["trigger"])
            entry = base * (1 + sign * request.slippage_bps/10000)
            if request.stop.mode == "mae_percentile" and len(order["conditional"]) < request.min_trades:
                counts["insufficient_conditional_sample"] += 1
                break
            sd = distance(request.stop, stop_value, entry, session["state"], side, session["history"], order["conditional"])
            if request.target_mode == "reference":
                td = sign*(order["reference_price"]-entry)
            elif request.target_mode == "price":
                td = sign*(target_value-entry)
            elif request.target_mode == "r_multiple":
                td = sd * target_value if sd is not None else None
            else:
                td = entry*target_value/100 if request.target_mode == "fixed_pct" else session["state"][request.target_mode]*target_value
            if sd is None or td is None:
                counts["unavailable_exit_statistic"] += 1
                break
            outcome = execute(path, side, order["trigger"], sd, td, request)
            if outcome["status"] == "invalid_levels":
                counts["invalid_levels"] += 1
                break
            counts["filled"] += 1
            if outcome["status"] != "evaluated":
                counts[outcome["status"]] += 1
                if issues is not None:
                    issues.append((first["end_time"], outcome["status"]))
                busy_until = horizon
                break
            outcome.update(reference_time=session["opening"], reference_price=order["reference_price"],
                           regime=session["regime"], volatility_regime=session["volatility_regime"],
                           conditional_sample_size=len(order["conditional"]))
            trades.append(outcome)
            qty = min(equity*request.risk_pct/100/sd, equity/entry) if request.sizing == "risk" else equity*request.allocation_pct/100/entry
            equity += qty*outcome["unit_pnl"]
            busy_until = outcome["exit_time"]
            after = (busy_until-session["opening"])//step
            if equity <= 0:
                break
    return trades, dict(counts)


def partition(trades, left, right):
    # Purge trades crossing either split boundary; no overlapping train/test PnL.
    return [t for t in trades if t["entry_time"] >= left and t["exit_time"] <= right]


def optimize(request, reference, execution, start, end):
    period = INTERVAL_MS[request.reference_interval]
    anchor = 4*DAY if request.reference_interval == "1w" else 0
    split = ((int(start+(end-start)*request.train_ratio)-anchor)//period)*period+anchor
    candidates = []
    for entry in request.entry_values:
        planning_issues = []
        sessions, skips = make_sessions(request, reference, execution, start, end, entry, planning_issues)
        for stop, target in product(request.stop_values, request.target_values):
            issues = planning_issues.copy()
            trades, counts = simulate(request, sessions, execution, stop, target, issues)
            overall, _ = metrics(trades, request)
            train, _ = metrics(partition(trades, start, split), request)
            test, _ = metrics(partition(trades, split, end), request)
            candidates.append({"id": len(candidates), "entry": entry, "stop": stop, "target": target,
                               "counts": {**skips, **counts}, "overall": overall, "train": train, "test": test,
                               "_trades": trades, "_issues": issues,
                               "train_quality_exclusions": sum(time <= split for time, _ in issues)})
    def neighbours(candidate):
        grids = [request.entry_values, request.stop_values, request.target_values]
        return [other for other in candidates if all(abs(grid.index(candidate[key])-grid.index(other[key])) <= 1 for grid, key in zip(grids, ("entry", "stop", "target")))]
    for candidate in candidates:
        group = [v["train"] for v in neighbours(candidate) if v["train"]["sufficient_sample"] and v["train_quality_exclusions"] == 0]
        candidate["neighbourhood"] = {"sampled_cells": len(group), "median_train_ev_r": float(np.median([v["average_r"] for v in group])) if group else None,
                                      "positive_fraction": sum(v["average_r"] > 0 for v in group)/len(group) if group else None}
    # Data/order exclusions invalidate automatic selection (statistics remain
    # visible). Evaluate quality from TRAIN only, never from holdout outcomes.
    def eligible_metrics(m):
        return m["sufficient_sample"] and m["max_drawdown_pct"] <= request.max_drawdown_pct
    eligible = [c for c in candidates if eligible_metrics(c["train"]) and c["train_quality_exclusions"] == 0]
    eligible.sort(key=lambda c: (c["neighbourhood"]["median_train_ev_r"], c["train"]["average_r"], -c["id"]), reverse=True)
    selected = eligible[0]["id"] if eligible else None
    # Expanding, chronological walk-forward; test outcomes never select a cell.
    folds = []
    boundaries = sorted(set([start, split] + [((int(split+(end-split)*i/3)-anchor)//period)*period+anchor for i in (1, 2)] + [end]))
    for left, right in zip(boundaries[1:-1], boundaries[2:]):
        scored = [(metrics(partition(c["_trades"], start, left), request)[0], c) for c in candidates]
        eligible_fold = [(m, c) for m, c in scored if eligible_metrics(m) and not any(time <= left for time, _ in c["_issues"])]
        winner = max(eligible_fold, key=lambda pair: (pair[0]["average_r"], -pair[1]["id"]))[1] if eligible_fold else None
        folds.append({"train_end": left, "test_end": right, "candidate_id": winner["id"] if winner else None,
                      "test": metrics(partition(winner["_trades"], left, right), request)[0] if winner else None})
    for c in candidates:
        trades = c.pop("_trades")
        c.pop("_issues")
        c["trades"] = metrics(trades, request)[1]
        c["groups"] = {}
        for key in ("year", "regime", "volatility_regime"):
            groups = {}
            for t in trades:
                group = str(datetime.fromtimestamp(t["entry_time"]/1000, timezone.utc).year) if key == "year" else t[key]
                groups.setdefault(group, []).append(t)
            c["groups"][key] = {name: metrics(rows, request)[0] for name, rows in groups.items()}
        c["excursions"] = {key: describe([t[key] for t in trades], histogram=True) for key in ("mae_upper_pct", "mfe_upper_pct")}
    return {"split_time": split, "selected_id": selected, "candidates": candidates, "walk_forward": folds}


def breakout_distribution(reference, execution, interval, start, end):
    """Descriptive completed-period overshoot; NOT an entry stop probability."""
    duration = INTERVAL_MS[interval]
    records, times = execution.to_dict("records"), execution.open_time.to_numpy()
    execution_step = int(execution.iloc[0].end_time-execution.iloc[0].open_time)
    output = {}
    for side in ("Short", "Long"):
        depths, returns, minutes, unknown = [], 0, [], 0
        for i in range(1, len(reference)):
            bar, prior = reference.iloc[i], reference.iloc[i-1]
            if bar.open_time < start or bar.end_time > end or bar.open_time-prior.open_time != duration:
                continue
            level = float(prior.high if side == "Short" else prior.low)
            depth = (bar.high-level)/level*100 if side == "Short" else (level-bar.low)/level*100
            if depth <= 0:
                continue
            depths.append(depth)
            path = records[int(np.searchsorted(times, bar.open_time)):int(np.searchsorted(times, bar.end_time))]
            if not path or len(path)*execution_step != duration or any(b["open_time"] != bar.open_time+j*execution_step for j, b in enumerate(path)):
                unknown += 1
                continue
            index = next((j for j, b in enumerate(path) if (b["high"] > level if side == "Short" else b["low"] < level)), None)
            if index is None:
                unknown += 1
                continue
            # Same-bar return only established by close after a breakout.
            returned = next((j for j in range(index, len(path)) if ((path[j]["close"] <= level if side == "Short" else path[j]["close"] >= level) if j == index else (path[j]["low"] <= level if side == "Short" else path[j]["high"] >= level))), None)
            if returned is not None:
                returns += 1
                minutes.append((path[returned]["end_time"]-path[index]["open_time"])/60000)
            elif path[index]["low"] <= level <= path[index]["high"]:
                unknown += 1
        output[side] = {"depth_pct": describe(depths, histogram=True), "returns_confirmed": returns,
                        "order_or_coverage_unknown": unknown,
                        "return_rate_lower_pct": returns/len(depths)*100 if depths else None,
                        "return_minutes_upper_bound": describe(minutes)}
    return output
