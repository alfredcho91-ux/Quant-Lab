"""Trading Journal API router."""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from modules.journal.schemas import JournalEntry
from modules.journal.service import add_journal_service, delete_journal_service, get_journal_service
from utils.decorators import handle_api_errors

router = APIRouter(prefix="/api", tags=["journal"])


@router.get("/journal")
@handle_api_errors()
async def api_get_journal():
    """Get all journal entries."""
    return await run_in_threadpool(get_journal_service)


@router.post("/journal")
@handle_api_errors()
async def api_add_journal(entry: JournalEntry):
    """Add a journal entry."""
    return await run_in_threadpool(add_journal_service, entry.model_dump())


@router.delete("/journal/{entry_id}")
@handle_api_errors()
async def api_delete_journal(entry_id: int):
    """Delete a journal entry."""
    return await run_in_threadpool(delete_journal_service, entry_id)
