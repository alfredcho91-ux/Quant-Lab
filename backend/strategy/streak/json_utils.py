"""
JSON 직렬화 및 데이터 정제 유틸리티
"""
import numpy as np
import pandas as pd
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

def safe_round(val: Any, digits: int = 2) -> Optional[float]:
    """
    안전하게 반올림 (NaN/Infinity 처리 포함)
    """
    if val is None:
        return None
    try:
        safe_val = float(val)
    except (ValueError, TypeError):
        return None
    if np.isnan(safe_val) or np.isinf(safe_val):
        return None
    return round(safe_val, digits)


def sanitize_for_json(obj: Any) -> Any:
    """
    JSON 직렬화 전에 NaN/Infinity 값을 None으로 변환
    재귀적으로 딕셔너리와 리스트를 처리
    """
    try:
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [sanitize_for_json(item) for item in obj]
        elif isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        elif isinstance(obj, np.floating):
            f = float(obj)
            if np.isnan(f) or np.isinf(f):
                return None
            return f
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return sanitize_for_json(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            return sanitize_for_json(obj.to_dict() if isinstance(obj, pd.Series) else obj.to_dict('records'))
        elif obj is None:
            return None
        elif isinstance(obj, (str, int, bool)):
            return obj
        else:
            # 알 수 없는 타입은 문자열로 변환 시도
            try:
                return str(obj)
            except:
                return None
    except Exception as e:
        logger.warning(f"sanitize_for_json error for type {type(obj)}: {e}")
        return None
