"""Strategy info service layer."""

from __future__ import annotations

from typing import Any, Dict

from config.metadata_loader import get_strategy_explainer
from utils.error_handler import NotFoundError
from utils.response_builder import success_response
from utils.validators import validate_numeric_range


def run_strategy_info_service(
    strategy_id: str,
    lang: str,
    rsi_ob: int,
    sma_main_len: int,
    sma1_len: int,
    sma2_len: int,
) -> Dict[str, Any]:
    """Get strategy explanation by strategy id and parameters."""
    validate_numeric_range(rsi_ob, min_value=0, max_value=100, field_name="rsi_ob")
    validate_numeric_range(sma_main_len, min_value=1, field_name="sma_main_len")
    validate_numeric_range(sma1_len, min_value=1, field_name="sma1_len")
    validate_numeric_range(sma2_len, min_value=1, field_name="sma2_len")

    normalized_lang = lang if lang in ("ko", "en") else "ko"
    explainer = get_strategy_explainer(
        strategy_id,
        normalized_lang,
        rsi_ob,
        sma_main_len,
        sma1_len,
        sma2_len,
    )
    if not explainer:
        raise NotFoundError("Strategy", strategy_id)
    return success_response(data=explainer)

