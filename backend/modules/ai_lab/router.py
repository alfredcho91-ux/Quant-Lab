"""AI Lab domain router."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from modules.ai_lab.schemas import AIResearchRequest, AIResearchResponse, AIAnalystRequest
from modules.ai_lab.service import process_ai_research, run_data_analyst_agent
from utils.decorators import handle_api_errors
from config import settings

router = APIRouter(prefix="/api/ai", tags=["ai-lab"])


@router.post("/research", response_model=AIResearchResponse)
@handle_api_errors()
async def api_ai_research(request: AIResearchRequest):
    """Process natural language request -> LLM -> Backtest."""
    result = await run_in_threadpool(
        process_ai_research,
        prompt=request.prompt,
        api_key=request.api_key,
        model=request.model,
        provider=request.provider,
        history=request.history,
        temperature=request.temperature,
    )

    return {
        "success": result.get("error") is None,
        "answer": result.get("answer", ""),
        "backtest_params": result.get("backtest_params"),
        "backtest_result": result.get("backtest_result"),
        "analysis_result": result.get("analysis_result"),
        "needs_clarification": bool(result.get("needs_clarification", False)),
        "clarifying_questions": result.get("clarifying_questions"),
        "cache_hit": result.get("cache_hit"),
        "execution_path": result.get("execution_path"),
        "error": result.get("error"),
        "error_code": result.get("error_code"),
    }

@router.post("/analyst")
@handle_api_errors()
async def api_ai_analyst(request: AIAnalystRequest):
    """Process natural language request -> LLM -> Python REPL -> Answer."""
    api_key = request.api_key or settings.GEMINI_API_KEY
    
    result = await run_in_threadpool(
        run_data_analyst_agent,
        api_key=api_key,
        coin=request.coin,
        interval=request.interval,
        user_prompt=request.prompt,
        model=request.model,
    )

    return {
        "success": bool(result.get("success", False)),
        "answer": str(result.get("answer") or ""),
        "execution_path": result.get("execution_path"),
        "error": result.get("error"),
    }
