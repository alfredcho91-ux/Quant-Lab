from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from .schemas import LabRequest, StatisticsRequest
from .service import analyze, candle_statistics

router = APIRouter(prefix="/api/stop-loss-lab", tags=["stop-loss-lab"])


@router.post("/statistics")
async def statistics(request: StatisticsRequest):
    try:
        return {"success": True, "data": await run_in_threadpool(candle_statistics, request)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analyze")
async def analyze_lab(request: LabRequest):
    try:
        return {"success": True, "data": await run_in_threadpool(analyze, request)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
