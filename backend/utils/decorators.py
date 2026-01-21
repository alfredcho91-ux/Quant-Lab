# utils/decorators.py
"""공통 데코레이터 함수"""

from functools import wraps
from typing import Callable, Any
import sys
from utils.error_handler import APIError, handle_error
from utils.response_builder import wrap_response


def handle_api_errors(include_traceback: bool = False):
    """
    API 엔드포인트의 공통 에러 처리 데코레이터
    
    Args:
        include_traceback: traceback 포함 여부 (기본값: False, 개발 환경용)
    
    Usage:
        @router.post("/endpoint")
        @handle_api_errors()
        async def api_endpoint(params: Params):
            # 로직
            return {"success": True, "data": result}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> dict[str, Any]:
            try:
                result = await func(*args, **kwargs)
                # 표준 응답 형식으로 래핑
                return wrap_response(result)
            except APIError as e:
                # APIError는 그대로 처리
                return handle_error(e, include_traceback=include_traceback)
            except Exception as e:
                # 기타 예외는 표준 형식으로 변환
                return handle_error(e, include_traceback=include_traceback)
        return wrapper
    return decorator
