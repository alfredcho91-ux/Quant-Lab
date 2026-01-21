# routes/__init__.py
# 분리된 API 라우터 모듈들

from .streak import router as streak_router

__all__ = [
    'streak_router',
]
