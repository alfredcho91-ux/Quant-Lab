"""Support resistance service layer."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from core.support_resistance import (
    build_sr_levels_from_swings,
    compute_daily_pivots,
    compute_htf_sr_levels,
)
from utils.data_service import fetch_live_data
from utils.response_builder import success_response
from utils.validators import validate_coin_symbol, validate_ohlcv_dataframe, validate_timeframe


def run_support_resistance_service(
    coin: str,
    interval: str,
    lookback: int,
    tolerance_pct: float,
    min_touches: int,
    show_pivots: bool,
    htf_option: str,
) -> Dict[str, Any]:
    """Calculate support/resistance levels."""
    coin = validate_coin_symbol(coin)
    interval = validate_timeframe(interval)

    df = fetch_live_data(f"{coin}/USDT", interval, total_candles=1000)
    df = validate_ohlcv_dataframe(df)

    frames = []

    sr_main = build_sr_levels_from_swings(
        df,
        lookback=lookback,
        tolerance_pct=tolerance_pct / 100.0,
        min_touches=min_touches,
        timeframe_label=interval,
    )
    if not sr_main.empty:
        frames.append(sr_main)

    if show_pivots:
        pivots = compute_daily_pivots(df, last_n=1)
        if not pivots.empty:
            frames.append(pivots)

    if htf_option != "none":
        rule = "4H" if htf_option == "4H" else "1D"
        htf_levels = compute_htf_sr_levels(
            df,
            rule=rule,
            lookback=lookback,
            tolerance_pct=tolerance_pct / 100.0,
            min_touches=min_touches,
        )
        if not htf_levels.empty:
            frames.append(htf_levels)

    if frames:
        all_levels = pd.concat(frames, ignore_index=True)
        return success_response(data=all_levels.to_dict(orient="records"))

    return success_response(data=[])

