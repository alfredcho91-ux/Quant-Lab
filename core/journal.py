# core/journal.py
from pathlib import Path
import pandas as pd
from datetime import datetime

JOURNAL_DIR = Path("journal")
JOURNAL_PATH = JOURNAL_DIR / "trade_journal.csv"

JOURNAL_COLUMNS = [
    "id",
    "datetime",
    "symbol",
    "timeframe",
    "direction",
    "strategy_id",
    "size",
    "entry_price",
    "exit_price",
    "pnl_pct",
    "r_multiple",
    "outcome",
    "emotion",
    "tags",
    "mistakes",
    "notes",
    "created_at",
]


def load_journal() -> pd.DataFrame:
    """
    매매 일지 CSV를 읽어서 DataFrame으로 반환.
    없으면 컬럼만 있는 빈 DF 반환.
    """
    if not JOURNAL_PATH.exists():
        return pd.DataFrame(columns=JOURNAL_COLUMNS)

    df = pd.read_csv(JOURNAL_PATH)
    # datetime 컬럼을 날짜 형식으로 변환 (있을 때만)
    for col in ["datetime", "created_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def append_entry(entry: dict) -> pd.DataFrame:
    """
    단일 매매 일지 entry를 CSV에 추가하고, 전체 DF를 반환.
    entry는 JOURNAL_COLUMNS 중 일부만 있어도 됨.
    """
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_journal()

    # id 자동 증가
    if not df.empty and "id" in df.columns:
        next_id = int(df["id"].max()) + 1
    else:
        next_id = 1

    now = datetime.utcnow()

    row = {
        "id": next_id,
        "datetime": entry.get("datetime", now),
        "symbol": entry.get("symbol"),
        "timeframe": entry.get("timeframe"),
        "direction": entry.get("direction"),
        "strategy_id": entry.get("strategy_id"),
        "size": entry.get("size"),
        "entry_price": entry.get("entry_price"),
        "exit_price": entry.get("exit_price"),
        "pnl_pct": entry.get("pnl_pct"),
        "r_multiple": entry.get("r_multiple"),
        "outcome": entry.get("outcome"),
        "emotion": entry.get("emotion"),
        "tags": entry.get("tags"),
        "mistakes": entry.get("mistakes"),
        "notes": entry.get("notes"),
        "created_at": now,
    }

    # 누락된 컬럼이 있으면 None으로 채워서 맞춰줌
    for c in JOURNAL_COLUMNS:
        row.setdefault(c, None)

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(JOURNAL_PATH, index=False)
    return df