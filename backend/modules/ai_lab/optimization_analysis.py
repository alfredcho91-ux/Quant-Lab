"""Scoring and presentation helpers for AI optimization."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from models.request import AdvancedBacktestParams, BacktestParams


def score_backtest_summary(summary: Dict[str, Any]) -> float:
    trades = int(summary.get("n_trades") or 0)
    win_rate = float(summary.get("win_rate") or 0.0)
    total_pnl = float(summary.get("total_pnl") or 0.0)
    avg_pnl = float(summary.get("avg_pnl") or 0.0)
    liq_count = int(summary.get("liq_count") or 0)

    score = (total_pnl * 0.75) + (avg_pnl * 0.45) + ((win_rate - 50.0) * 0.3) - (liq_count * 3.5)
    if trades < 10:
        score -= (10 - trades) * 0.8

    trade_weight = max(0.35, min(1.0, trades / 80.0))
    return score * trade_weight


def extract_advanced_summary(result: Dict[str, Any], section: str) -> Dict[str, Any]:
    section_payload = result.get(section)
    if isinstance(section_payload, dict):
        summary = section_payload.get("summary")
        if isinstance(summary, dict):
            return summary
    return {}


def to_advanced_params(
    candidate: BacktestParams,
    *,
    optimization_train_ratio: float,
    optimization_monte_carlo_runs: int,
) -> AdvancedBacktestParams:
    payload = candidate.model_dump()
    payload["train_ratio"] = optimization_train_ratio
    payload["monte_carlo_runs"] = optimization_monte_carlo_runs
    return AdvancedBacktestParams(**payload)


def score_advanced_backtest(advanced_result: Dict[str, Any]) -> float:
    in_summary = extract_advanced_summary(advanced_result, "in_sample")
    out_summary = extract_advanced_summary(advanced_result, "out_of_sample")
    full_summary = extract_advanced_summary(advanced_result, "full")

    if not out_summary and not full_summary:
        return float("-inf")

    focus_summary = out_summary if out_summary else full_summary
    in_score = score_backtest_summary(in_summary if in_summary else focus_summary)
    focus_score = score_backtest_summary(focus_summary)
    full_score = score_backtest_summary(full_summary if full_summary else focus_summary)

    in_win = float(in_summary.get("win_rate") or 0.0)
    focus_win = float(focus_summary.get("win_rate") or 0.0)
    in_pnl = float(in_summary.get("total_pnl") or 0.0)
    focus_pnl = float(focus_summary.get("total_pnl") or 0.0)
    in_trades = int(in_summary.get("n_trades") or 0)
    focus_trades = int(focus_summary.get("n_trades") or 0)

    stability_penalty = (
        abs(in_win - focus_win) * 0.25
        + max(0.0, in_pnl - focus_pnl) * 0.15
        + max(0, in_trades - focus_trades) * 0.03
    )
    if focus_trades < 5:
        stability_penalty += (5 - focus_trades) * 1.2

    focus_weight = 0.75 if out_summary else 0.45
    return (focus_score * focus_weight) + (full_score * (1.0 - focus_weight)) + (in_score * 0.05) - stability_penalty


def normalize_summary_for_ui(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "n_trades": int(summary.get("n_trades") or 0),
        "win_rate": float(summary.get("win_rate") or 0.0),
        "total_pnl": float(summary.get("total_pnl") or 0.0),
        "avg_pnl": float(summary.get("avg_pnl") or 0.0),
        "liq_count": int(summary.get("liq_count") or 0),
        "regime_stats": summary.get("regime_stats") if isinstance(summary.get("regime_stats"), list) else [],
    }


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _mean_optional(values: List[Optional[float]]) -> Optional[float]:
    valid = [float(value) for value in values if value is not None]
    if not valid:
        return None
    return float(sum(valid) / len(valid))


def _format_param_value(key: str, value: float) -> float:
    if key in {"tp_pct", "sl_pct", "bb_std_mult", "kc_mult", "vol_spike_k"}:
        return round(value, 2)
    return round(value, 1)


def build_optimization_characteristics(
    trial_rows: List[Dict[str, Any]],
    prompt: str,
    *,
    feature_labels: List[Tuple[str, str]],
) -> Optional[Dict[str, Any]]:
    if len(trial_rows) < 8:
        return None

    is_ko = bool(re.search(r"[가-힣]", prompt or ""))
    ordered = sorted(trial_rows, key=lambda row: float(row.get("score") or float("-inf")))
    bucket_size = max(2, len(ordered) // 4)
    bottom_rows = ordered[:bucket_size]
    top_rows = ordered[-bucket_size:]

    highlights: List[Dict[str, Any]] = []
    for key, label in feature_labels:
        all_values = [float(row["params"][key]) for row in trial_rows if key in row.get("params", {})]
        if len(all_values) < bucket_size * 2:
            continue

        min_value = min(all_values)
        max_value = max(all_values)
        span = max_value - min_value
        if span <= 1e-9:
            continue

        top_values = [float(row["params"][key]) for row in top_rows if key in row.get("params", {})]
        bottom_values = [float(row["params"][key]) for row in bottom_rows if key in row.get("params", {})]
        if not top_values or not bottom_values:
            continue

        top_mean = _mean(top_values)
        bottom_mean = _mean(bottom_values)
        effect_ratio = abs(top_mean - bottom_mean) / span
        if effect_ratio < 0.18:
            continue

        higher_is_better = top_mean > bottom_mean
        if is_ko:
            interpretation = "높을수록 성과 우세" if higher_is_better else "낮을수록 성과 우세"
        else:
            interpretation = "Higher tends to outperform" if higher_is_better else "Lower tends to outperform"

        highlights.append(
            {
                "param": key,
                "label": label,
                "direction": "higher_better" if higher_is_better else "lower_better",
                "top_mean": _format_param_value(key, top_mean),
                "bottom_mean": _format_param_value(key, bottom_mean),
                "effect_pct": round(effect_ratio * 100.0, 1),
                "interpretation": interpretation,
            }
        )

    if not highlights:
        return None

    highlights.sort(key=lambda item: float(item["effect_pct"]), reverse=True)
    highlights = highlights[:5]

    top_oos_pnl = _mean_optional([row.get("oos_total_pnl") for row in top_rows])
    bottom_oos_pnl = _mean_optional([row.get("oos_total_pnl") for row in bottom_rows])
    top_oos_win_rate = _mean_optional([row.get("oos_win_rate") for row in top_rows])
    bottom_oos_win_rate = _mean_optional([row.get("oos_win_rate") for row in bottom_rows])

    return {
        "analysis_type": "optimization_characteristics",
        "summary": {
            "trial_count": len(trial_rows),
            "bucket_size": bucket_size,
            "top_avg_oos_pnl": round(top_oos_pnl, 2) if top_oos_pnl is not None else None,
            "bottom_avg_oos_pnl": round(bottom_oos_pnl, 2) if bottom_oos_pnl is not None else None,
            "top_avg_oos_win_rate": round(top_oos_win_rate, 2) if top_oos_win_rate is not None else None,
            "bottom_avg_oos_win_rate": round(bottom_oos_win_rate, 2) if bottom_oos_win_rate is not None else None,
        },
        "highlights": highlights,
    }


def build_ui_result_from_advanced_payload(advanced_result: Dict[str, Any]) -> Dict[str, Any]:
    chart_data = advanced_result.get("chart_data") if isinstance(advanced_result.get("chart_data"), list) else []
    trades = advanced_result.get("trades") if isinstance(advanced_result.get("trades"), list) else []
    full_summary = extract_advanced_summary(advanced_result, "full")
    return {
        "success": True,
        "chart_data": chart_data,
        "trades": trades,
        "summary": normalize_summary_for_ui(full_summary),
    }


def format_optimization_summary(
    *,
    prompt: str,
    base_summary: Dict[str, Any],
    best_summary: Dict[str, Any],
    evaluated_count: int,
    best_params: BacktestParams,
) -> str:
    is_ko = bool(re.search(r"[가-힣]", prompt or ""))
    base_pnl = float(base_summary.get("total_pnl") or 0.0)
    best_pnl = float(best_summary.get("total_pnl") or 0.0)
    base_wr = float(base_summary.get("win_rate") or 0.0)
    best_wr = float(best_summary.get("win_rate") or 0.0)
    pnl_delta = best_pnl - base_pnl
    wr_delta = best_wr - base_wr

    if is_ko:
        return (
            f"[자동 최적화 완료] OOS 검증기준 탐색 {evaluated_count}회\n"
            f"- 기준(OOS): 수익률 {base_pnl:.2f}%, 승률 {base_wr:.2f}%\n"
            f"- 최적(OOS): 수익률 {best_pnl:.2f}%, 승률 {best_wr:.2f}%\n"
            f"- 개선(OOS): 수익률 {pnl_delta:+.2f}%p, 승률 {wr_delta:+.2f}%p\n"
            f"- 추천 파라미터: TP {best_params.tp_pct:.2f}% / SL {best_params.sl_pct:.2f}% / "
            f"MaxBars {best_params.max_bars} / RSI_OB {best_params.rsi_ob}"
        )

    return (
        f"[Auto Optimization Complete] OOS-focused {evaluated_count} trials\n"
        f"- Baseline (OOS): PnL {base_pnl:.2f}%, WinRate {base_wr:.2f}%\n"
        f"- Best (OOS): PnL {best_pnl:.2f}%, WinRate {best_wr:.2f}%\n"
        f"- Delta (OOS): PnL {pnl_delta:+.2f}pp, WinRate {wr_delta:+.2f}pp\n"
        f"- Suggested params: TP {best_params.tp_pct:.2f}% / SL {best_params.sl_pct:.2f}% / "
        f"MaxBars {best_params.max_bars} / RSI_OB {best_params.rsi_ob}"
    )


__all__ = [
    "build_optimization_characteristics",
    "build_ui_result_from_advanced_payload",
    "extract_advanced_summary",
    "format_optimization_summary",
    "normalize_summary_for_ui",
    "score_advanced_backtest",
    "score_backtest_summary",
    "to_advanced_params",
]
