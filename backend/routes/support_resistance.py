# routes/support_resistance.py
"""Support/Resistance API 엔드포인트"""

from fastapi import APIRouter
from data_service import fetch_live_data
from core.support_resistance import (
    build_sr_levels_from_swings,
    compute_daily_pivots,
    compute_htf_sr_levels,
)
from utils.decorators import handle_api_errors
from utils.response_builder import success_response
from utils.validators import validate_coin_symbol, validate_timeframe, validate_ohlcv_dataframe
from utils.error_handler import DataLoadError
import pandas as pd

router = APIRouter(prefix="/api", tags=["support-resistance"])


@router.get("/support-resistance/{coin}/{interval}")
@handle_api_errors()
async def api_support_resistance(
    coin: str,
    interval: str,
    lookback: int = 3,
    tolerance_pct: float = 0.3,
    min_touches: int = 3,
    show_pivots: bool = False,
    htf_option: str = "none",
):
    """Calculate support/resistance levels"""
    # 입력 검증
    coin = validate_coin_symbol(coin)
    interval = validate_timeframe(interval)
    
    # 데이터 로딩
    df = fetch_live_data(f"{coin}/USDT", interval, total_candles=1000)
    df = validate_ohlcv_dataframe(df)
    
    frames = []
    
    # Swing-based SR levels
    sr_main = build_sr_levels_from_swings(
        df,
        lookback=lookback,
        tolerance_pct=tolerance_pct / 100.0,
        min_touches=min_touches,
        timeframe_label=interval,
    )
    if not sr_main.empty:
        frames.append(sr_main)
    
    # Daily pivots
    if show_pivots:
        pivots = compute_daily_pivots(df, last_n=1)
        if not pivots.empty:
            frames.append(pivots)
    
    # HTF levels
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
