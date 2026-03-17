# config/settings.py
"""Application settings and configuration"""

import os
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# CORS settings
_DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]

_cors_origins_env = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS: List[str] = (
    [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]
    if _cors_origins_env
    else _DEFAULT_CORS_ORIGINS
)

# Analysis timezone (DST-aware in streak distribution via pytz)
ANALYSIS_TIMEZONE = os.getenv("ANALYSIS_TIMEZONE", "America/New_York")

# Journal settings
JOURNAL_DIR = Path(os.getenv("JOURNAL_DIR", str(PROJECT_ROOT / "journal"))).expanduser()
JOURNAL_DB_PATH = Path(
    os.getenv("JOURNAL_DB_PATH", str(JOURNAL_DIR / "trade_journal.db"))
).expanduser()
JOURNAL_CSV_PATH = Path(
    os.getenv("JOURNAL_CSV_PATH", str(JOURNAL_DIR / "trade_journal.csv"))
).expanduser()
JOURNAL_PATH = JOURNAL_CSV_PATH
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

# AI Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
