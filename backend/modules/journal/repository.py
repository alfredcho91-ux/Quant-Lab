"""SQLite-backed persistence helpers for the trading journal."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from config.settings import JOURNAL_COLUMNS, JOURNAL_CSV_PATH, JOURNAL_DB_PATH

TABLE_NAME = "journal_entries"
INSERTABLE_COLUMNS = [col for col in JOURNAL_COLUMNS if col != "id"]


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if pd.isna(value):
        return None
    return value


def _resolve_db_path(db_path: Optional[Path] = None) -> Path:
    return db_path or JOURNAL_DB_PATH


def _resolve_csv_path(csv_path: Optional[Path] = None) -> Path:
    return csv_path or JOURNAL_CSV_PATH


def _connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = _resolve_db_path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT,
            symbol TEXT,
            timeframe TEXT,
            direction TEXT,
            strategy_id TEXT,
            size REAL,
            entry_price REAL,
            exit_price REAL,
            pnl_pct REAL,
            r_multiple REAL,
            outcome TEXT,
            emotion TEXT,
            tags TEXT,
            mistakes TEXT,
            notes TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()


def _table_has_rows(conn: sqlite3.Connection) -> bool:
    row = conn.execute(f"SELECT 1 FROM {TABLE_NAME} LIMIT 1").fetchone()
    return row is not None


def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for column in JOURNAL_COLUMNS:
        normalized[column] = _clean_value(record.get(column))
    return normalized


def _migrate_legacy_csv_if_needed(
    conn: sqlite3.Connection,
    *,
    csv_path: Optional[Path] = None,
) -> int:
    csv_path = _resolve_csv_path(csv_path)
    if _table_has_rows(conn) or not csv_path.exists():
        return 0

    df = pd.read_csv(csv_path)
    if df.empty:
        return 0

    records = []
    for raw in df.to_dict(orient="records"):
        normalized = _normalize_record(raw)
        records.append(tuple(normalized[column] for column in JOURNAL_COLUMNS))

    placeholders = ", ".join(["?"] * len(JOURNAL_COLUMNS))
    conn.executemany(
        f"""
        INSERT OR IGNORE INTO {TABLE_NAME} ({", ".join(JOURNAL_COLUMNS)})
        VALUES ({placeholders})
        """,
        records,
    )
    conn.commit()
    return len(records)


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _fetch_entry_by_id(conn: sqlite3.Connection, entry_id: int) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        f"""
        SELECT {", ".join(JOURNAL_COLUMNS)}
        FROM {TABLE_NAME}
        WHERE id = ?
        """,
        (entry_id,),
    ).fetchone()
    return _row_to_dict(row) if row is not None else None


def list_entries(
    *,
    db_path: Optional[Path] = None,
    csv_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        _ensure_schema(conn)
        _migrate_legacy_csv_if_needed(conn, csv_path=csv_path)
        rows = conn.execute(
            f"""
            SELECT {", ".join(JOURNAL_COLUMNS)}
            FROM {TABLE_NAME}
            ORDER BY id ASC
            """
        ).fetchall()
        return [_row_to_dict(row) for row in rows]


def add_entry(
    entry_data: Dict[str, Any],
    *,
    db_path: Optional[Path] = None,
    csv_path: Optional[Path] = None,
) -> Dict[str, Any]:
    payload = {
        column: _clean_value(entry_data.get(column))
        for column in INSERTABLE_COLUMNS
    }

    with _connect(db_path) as conn:
        _ensure_schema(conn)
        _migrate_legacy_csv_if_needed(conn, csv_path=csv_path)
        placeholders = ", ".join(["?"] * len(INSERTABLE_COLUMNS))
        conn.execute(
            f"""
            INSERT INTO {TABLE_NAME} ({", ".join(INSERTABLE_COLUMNS)})
            VALUES ({placeholders})
            """,
            tuple(payload[column] for column in INSERTABLE_COLUMNS),
        )
        entry_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        conn.commit()
        entry = _fetch_entry_by_id(conn, entry_id)
        if entry is None:
            raise RuntimeError("Failed to fetch newly inserted journal entry")
        return entry


def delete_entry(
    entry_id: int,
    *,
    db_path: Optional[Path] = None,
    csv_path: Optional[Path] = None,
) -> bool:
    with _connect(db_path) as conn:
        _ensure_schema(conn)
        _migrate_legacy_csv_if_needed(conn, csv_path=csv_path)
        cursor = conn.execute(
            f"DELETE FROM {TABLE_NAME} WHERE id = ?",
            (entry_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


__all__ = ["add_entry", "delete_entry", "list_entries"]
