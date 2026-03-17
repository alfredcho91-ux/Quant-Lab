"""Journal domain schemas."""

from typing import Optional

from pydantic import BaseModel


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


__all__ = ["JournalEntry"]

