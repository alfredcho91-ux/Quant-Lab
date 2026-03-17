"""Search-space and candidate generation helpers for AI optimization."""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List

from models.request import BacktestParams


def build_float_candidates(
    value: float,
    *,
    minimum: float,
    maximum: float,
    precision: int,
) -> List[float]:
    multipliers = (0.7, 0.85, 1.0, 1.15, 1.35)
    values = {
        round(min(max(value * mult, minimum), maximum), precision)
        for mult in multipliers
    }
    values.add(round(min(max(value, minimum), maximum), precision))
    return sorted(values)


def build_int_candidates(
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> List[int]:
    multipliers = (0.7, 0.85, 1.0, 1.15, 1.35)
    values = {
        max(minimum, min(maximum, int(round(value * mult))))
        for mult in multipliers
    }
    values.add(max(minimum, min(maximum, int(value))))
    return sorted(values)


def build_optimization_space(base: BacktestParams) -> Dict[str, List[Any]]:
    return {
        "tp_pct": build_float_candidates(base.tp_pct, minimum=0.1, maximum=8.0, precision=2),
        "sl_pct": build_float_candidates(base.sl_pct, minimum=0.1, maximum=6.0, precision=2),
        "max_bars": build_int_candidates(base.max_bars, minimum=4, maximum=800),
        "rsi_ob": build_int_candidates(base.rsi_ob, minimum=50, maximum=90),
        "sma1_len": build_int_candidates(base.sma1_len, minimum=3, maximum=400),
        "sma2_len": build_int_candidates(base.sma2_len, minimum=5, maximum=1200),
        "adx_thr": build_int_candidates(base.adx_thr, minimum=5, maximum=60),
        "bb_length": build_int_candidates(base.bb_length, minimum=5, maximum=120),
        "bb_std_mult": build_float_candidates(base.bb_std_mult, minimum=0.5, maximum=4.0, precision=2),
        "atr_length": build_int_candidates(base.atr_length, minimum=5, maximum=120),
        "kc_mult": build_float_candidates(base.kc_mult, minimum=0.5, maximum=4.0, precision=2),
        "vol_spike_k": build_float_candidates(base.vol_spike_k, minimum=0.5, maximum=10.0, precision=2),
        "macd_fast": build_int_candidates(base.macd_fast, minimum=4, maximum=40),
        "macd_slow": build_int_candidates(base.macd_slow, minimum=8, maximum=80),
        "macd_signal": build_int_candidates(base.macd_signal, minimum=3, maximum=30),
    }


def optimization_signature(params: BacktestParams) -> tuple:
    return (
        params.tp_pct,
        params.sl_pct,
        params.max_bars,
        params.rsi_ob,
        params.sma1_len,
        params.sma2_len,
        params.adx_thr,
        params.bb_length,
        params.bb_std_mult,
        params.atr_length,
        params.kc_mult,
        params.vol_spike_k,
        params.macd_fast,
        params.macd_slow,
        params.macd_signal,
    )


def build_optimization_rng(prompt: str, base_params: BacktestParams) -> random.Random:
    seed_material = (
        f"{prompt}|{base_params.coin}|{base_params.interval}|"
        f"{base_params.strategy_id}|{base_params.direction}"
    )
    seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:16], 16)
    return random.Random(seed)


def _build_candidate_payload(
    *,
    base_payload: Dict[str, Any],
    space: Dict[str, List[Any]],
    rng: random.Random,
) -> Dict[str, Any] | None:
    payload = dict(base_payload)
    payload["tp_pct"] = rng.choice(space["tp_pct"])
    payload["sl_pct"] = rng.choice(space["sl_pct"])
    payload["max_bars"] = rng.choice(space["max_bars"])
    payload["rsi_ob"] = rng.choice(space["rsi_ob"])
    payload["adx_thr"] = rng.choice(space["adx_thr"])
    payload["bb_length"] = rng.choice(space["bb_length"])
    payload["bb_std_mult"] = rng.choice(space["bb_std_mult"])
    payload["atr_length"] = rng.choice(space["atr_length"])
    payload["kc_mult"] = rng.choice(space["kc_mult"])
    payload["vol_spike_k"] = rng.choice(space["vol_spike_k"])

    sma1 = rng.choice(space["sma1_len"])
    sma2_choices = [value for value in space["sma2_len"] if value >= sma1]
    if not sma2_choices:
        return None
    payload["sma1_len"] = sma1
    payload["sma2_len"] = rng.choice(sma2_choices)

    macd_fast = rng.choice(space["macd_fast"])
    macd_slow_choices = [value for value in space["macd_slow"] if value > macd_fast]
    if not macd_slow_choices:
        return None
    macd_slow = rng.choice(macd_slow_choices)
    macd_signal_choices = [value for value in space["macd_signal"] if value < macd_slow]
    if not macd_signal_choices:
        return None
    payload["macd_fast"] = macd_fast
    payload["macd_slow"] = macd_slow
    payload["macd_signal"] = rng.choice(macd_signal_choices)
    return payload


def generate_optimization_candidates(
    *,
    base_params: BacktestParams,
    prompt: str,
    optimization_trials: int,
) -> List[BacktestParams]:
    rng = build_optimization_rng(prompt, base_params)
    space = build_optimization_space(base_params)
    base_payload = base_params.model_dump()

    candidates: List[BacktestParams] = [base_params]
    signatures = {optimization_signature(base_params)}
    attempts = 0
    max_attempts = max(40, optimization_trials * 30)

    while len(candidates) < optimization_trials and attempts < max_attempts:
        attempts += 1
        payload = _build_candidate_payload(
            base_payload=base_payload,
            space=space,
            rng=rng,
        )
        if payload is None:
            continue

        try:
            candidate = BacktestParams(**payload)
        except Exception:
            continue

        signature = optimization_signature(candidate)
        if signature in signatures:
            continue
        signatures.add(signature)
        candidates.append(candidate)

    return candidates


__all__ = [
    "build_float_candidates",
    "build_int_candidates",
    "build_optimization_rng",
    "build_optimization_space",
    "generate_optimization_candidates",
    "optimization_signature",
]
