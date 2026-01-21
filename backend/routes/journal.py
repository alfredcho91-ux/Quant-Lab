# routes/journal.py
"""Trading Journal API 엔드포인트"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import pandas as pd
from datetime import datetime as dt

router = APIRouter(prefix="/api", tags=["journal"])


JOURNAL_DIR = Path("journal")
JOURNAL_PATH = JOURNAL_DIR / "trade_journal.csv"
JOURNAL_COLUMNS = [
    "id", "datetime", "symbol", "timeframe", "direction", "strategy_id",
    "size", "entry_price", "exit_price", "pnl_pct", "r_multiple",
    "outcome", "emotion", "tags", "mistakes", "notes", "created_at"
]


class JournalEntry(BaseModel):
    datetime: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    direction: Optional[str] = None
    strategy_id: Optional[str] = None
    size: Optional[float] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    r_multiple: Optional[float] = None
    outcome: Optional[str] = None
    emotion: Optional[str] = None
    tags: Optional[str] = None
    mistakes: Optional[str] = None
    notes: Optional[str] = None


@router.get("/journal")
async def api_get_journal():
    """Get all journal entries"""
    try:
        if not JOURNAL_PATH.exists():
            return {"success": True, "data": []}
        
        df = pd.read_csv(JOURNAL_PATH)
        return {"success": True, "data": df.to_dict(orient="records")}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/journal")
async def api_add_journal(entry: JournalEntry):
    """Add a journal entry"""
    try:
        JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        
        if JOURNAL_PATH.exists():
            df = pd.read_csv(JOURNAL_PATH)
            next_id = int(df["id"].max()) + 1 if not df.empty else 1
        else:
            df = pd.DataFrame(columns=JOURNAL_COLUMNS)
            next_id = 1
        
        now = dt.utcnow()
        
        row = {
            "id": next_id,
            "datetime": entry.datetime or str(now),
            "symbol": entry.symbol,
            "timeframe": entry.timeframe,
            "direction": entry.direction,
            "strategy_id": entry.strategy_id,
            "size": entry.size,
            "entry_price": entry.entry_price,
            "exit_price": entry.exit_price,
            "pnl_pct": entry.pnl_pct,
            "r_multiple": entry.r_multiple,
            "outcome": entry.outcome,
            "emotion": entry.emotion,
            "tags": entry.tags,
            "mistakes": entry.mistakes,
            "notes": entry.notes,
            "created_at": str(now),
        }
        
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(JOURNAL_PATH, index=False)
        
        return {"success": True, "data": row}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/journal/{entry_id}")
async def api_delete_journal(entry_id: int):
    """Delete a journal entry"""
    try:
        if not JOURNAL_PATH.exists():
            return {"success": False, "error": "Journal not found"}
        
        df = pd.read_csv(JOURNAL_PATH)
        df = df[df["id"] != entry_id]
        df.to_csv(JOURNAL_PATH, index=False)
        
        return {"success": True, "message": "Entry deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}
