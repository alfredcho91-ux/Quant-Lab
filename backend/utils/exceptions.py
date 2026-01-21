# backend/utils/exceptions.py
"""
전역 예외 처리기 (Global Exception Handler)
README.md의 표준 에러 응답 스키마를 준수하여 FE-BE 간 통신 신뢰도 향상
"""

import os
import logging
import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """
    FastAPI 앱에 전역 예외 처리기를 등록합니다.
    
    Args:
        app: FastAPI 앱 인스턴스
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Pydantic 검증 에러 처리기
        README.md 표준 에러 응답 스키마 준수
        """
        errors = exc.errors()
        error_messages = []
        
        for error in errors:
            field = ".".join(str(loc) for loc in error.get("loc", []))
            msg = error.get("msg", "Validation error")
            error_messages.append(f"{field}: {msg}")
        
        error_message = "; ".join(error_messages) if error_messages else "Invalid request parameters"
        
        response = {
            "success": False,
            "error": error_message,
            "error_code": "VALIDATION_ERROR",
        }
        
        # 개발 환경에서만 상세 정보 제공
        debug_mode = os.getenv("DEBUG_STREAK_ANALYSIS", "false").lower() == "true"
        if debug_mode:
            response["details"] = errors
        
        logger.warning(f"Validation error: {error_message}")
        return JSONResponse(status_code=200, content=response)
    
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        HTTP 예외 처리기
        README.md 표준 에러 응답 스키마 준수
        """
        response = {
            "success": False,
            "error": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
        }
        
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(status_code=200, content=response)
    
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        전역 예외 처리기
        README.md 표준 에러 응답 스키마 준수
        
        모든 처리되지 않은 예외를 표준 형식으로 변환하여 반환합니다.
        개발 환경에서만 traceback을 제공합니다.
        """
        error_message = str(exc) if exc else "An unexpected error occurred"
        
        response = {
            "success": False,
            "error": error_message,
        }
        
        # 개발 환경에서만 traceback 제공
        debug_mode = os.getenv("DEBUG_STREAK_ANALYSIS", "false").lower() == "true"
        if debug_mode:
            response["traceback"] = traceback.format_exc()
        
        # 에러 로깅
        logger.error(f"Unhandled exception: {error_message}", exc_info=True)
        
        return JSONResponse(status_code=200, content=response)
