"""AI Lab Request/Response Schemas"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class AIResearchRequest(BaseModel):
    prompt: str
    api_key: Optional[str] = None
    provider: Literal["gemini"] = "gemini"
    model: str = "gemini-3-flash-preview"
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    history: Optional[List[Dict[str, str]]] = None  # 대화 맥락 유지를 위해

class AIResearchResponse(BaseModel):
    success: bool
    answer: str  # AI의 텍스트 답변
    backtest_params: Optional[Dict[str, Any]] = None  # 생성된 백테스트 파라미터
    backtest_result: Optional[Dict[str, Any]] = None  # 실행된 백테스트 결과
    analysis_result: Optional[Dict[str, Any]] = None  # 확률/조건부 분석 결과(차트 렌더링용)
    needs_clarification: bool = False
    clarifying_questions: Optional[List[str]] = None
    cache_hit: Optional[bool] = None
    execution_path: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

class AIAnalystRequest(BaseModel):
    prompt: str
    coin: str
    interval: str
    api_key: Optional[str] = None
    model: str = "gemini-3.0-pro-preview"
