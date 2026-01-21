# config/settings.py
"""Application settings and configuration"""

from pathlib import Path
from typing import List

# CORS settings
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "*"
]

# Journal settings
JOURNAL_DIR = Path("journal")
JOURNAL_PATH = JOURNAL_DIR / "trade_journal.csv"
JOURNAL_COLUMNS = [
    "id", "datetime", "symbol", "timeframe", "direction", "strategy_id",
    "size", "entry_price", "exit_price", "pnl_pct", "r_multiple",
    "outcome", "emotion", "tags", "mistakes", "notes", "created_at"
]

# Timeframe to minutes mapping
TIMEFRAME_TO_MINUTES = {
    "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "1h": 60,
    "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720, "1d": 1440,
}
