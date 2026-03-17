"""Journal API service layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from modules.journal.repository import add_entry, delete_entry, list_entries


def get_journal_service() -> Dict[str, Any]:
    """Get all journal entries."""
    try:
        return {"success": True, "data": list_entries()}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def add_journal_service(entry_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add one journal entry."""
    try:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        row = {
            "datetime": entry_data.get("datetime") or now,
            "symbol": entry_data.get("symbol"),
            "timeframe": entry_data.get("timeframe"),
            "direction": entry_data.get("direction"),
            "strategy_id": entry_data.get("strategy_id"),
            "size": entry_data.get("size"),
            "entry_price": entry_data.get("entry_price"),
            "exit_price": entry_data.get("exit_price"),
            "pnl_pct": entry_data.get("pnl_pct"),
            "r_multiple": entry_data.get("r_multiple"),
            "outcome": entry_data.get("outcome"),
            "emotion": entry_data.get("emotion"),
            "tags": entry_data.get("tags"),
            "mistakes": entry_data.get("mistakes"),
            "notes": entry_data.get("notes"),
            "created_at": now,
        }
        return {"success": True, "data": add_entry(row)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def delete_journal_service(entry_id: int) -> Dict[str, Any]:
    """Delete one journal entry by id."""
    try:
        deleted = delete_entry(entry_id)
        if not deleted:
            return {"success": False, "error": "Journal entry not found"}
        return {"success": True, "message": "Entry deleted"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
