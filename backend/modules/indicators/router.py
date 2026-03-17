from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from utils.data_service import fetch_live_data
from modules.indicators.reverse_calc import get_indicator_projections

router = APIRouter(prefix="/api/indicators", tags=["indicators"])

@router.get("/projection")
async def get_projection(
    coin: str = Query(..., description="Coin symbol (e.g., BTCUSDT)"),
    interval: str = Query("1h", description="Time interval (e.g., 1h, 4h, 1d)")
) -> Dict[str, Any]:
    """
    현재 가격 기준으로 특정 지표(RSI, Stoch)에 도달하기 위한 예상 가격을 반환합니다.
    """
    try:
        symbol = coin if coin.endswith("USDT") else f"{coin}USDT"
        
        # 1. 데이터 로드 (최근 100개 캔들만 있으면 충분함)
        df = fetch_live_data(symbol, interval, limit=100, total_candles=100)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="Data not found")
            
        # 2. 역산 로직 실행
        result = get_indicator_projections(df)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return {
            "success": True,
            "coin": coin,
            "interval": interval,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
