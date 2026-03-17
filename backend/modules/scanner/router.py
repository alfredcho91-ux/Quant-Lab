"""Scanner domain router."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from modules.scanner.schemas import PatternScanParams, ScannerParams
from modules.scanner.service import run_pattern_scanner_service, run_scanner_service
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["scanner"])


@router.post("/pattern-scanner")
@handle_api_errors(include_traceback=False)
async def api_pattern_scanner(params: PatternScanParams):
    """Run pattern scanner."""
    return await run_in_threadpool(run_pattern_scanner_service, params)


@router.post("/scanner")
@handle_api_errors(include_traceback=False)
async def api_scanner(params: ScannerParams):
    """Scan multiple strategies for current signals."""
    return await run_in_threadpool(run_scanner_service, params)

