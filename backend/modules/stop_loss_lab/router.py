from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from .schemas import LabRequest
from .service import analyze

router = APIRouter(prefix="/api/stop-loss-lab", tags=["stop-loss-lab"])


@router.post("/analyze")
async def analyze_lab(request: LabRequest):
    try:
        return {"success": True, "data": await run_in_threadpool(analyze, request)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
