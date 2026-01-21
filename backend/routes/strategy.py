# routes/strategy.py
"""Strategy information API 엔드포인트"""

from fastapi import APIRouter
from config.metadata_loader import get_strategy_explainer
from utils.decorators import handle_api_errors
from utils.response_builder import success_response
from utils.validators import validate_numeric_range
from utils.error_handler import NotFoundError

router = APIRouter(prefix="/api", tags=["strategy"])


@router.get("/strategy-info/{strategy_id}")
@handle_api_errors()
async def api_strategy_info(
    strategy_id: str,
    lang: str = "ko",
    rsi_ob: int = 70,
    rsi2_ob: int = 80,
    ema_len: int = 200,
    sma1_len: int = 20,
    sma2_len: int = 60,
):
    """Get strategy explanation"""
    # 파라미터 검증
    validate_numeric_range(rsi_ob, min_value=0, max_value=100, field_name="rsi_ob")
    validate_numeric_range(rsi2_ob, min_value=0, max_value=100, field_name="rsi2_ob")
    validate_numeric_range(ema_len, min_value=1, field_name="ema_len")
    validate_numeric_range(sma1_len, min_value=1, field_name="sma1_len")
    validate_numeric_range(sma2_len, min_value=1, field_name="sma2_len")
    
    if lang not in ["ko", "en"]:
        lang = "ko"  # 기본값으로 설정
    
    explainer = get_strategy_explainer(
        strategy_id=strategy_id,
        lang=lang,
        rsi_ob=rsi_ob,
        rsi2_ob=rsi2_ob,
        ema_len=ema_len,
        sma1_len=sma1_len,
        sma2_len=sma2_len,
    )
    
    if not explainer:
        raise NotFoundError("Strategy", strategy_id)
    
    return success_response(data=explainer)
