from __future__ import annotations

import pandas as pd
import pytest

from modules.journal import repository as journal_repository
from modules.journal.service import (
    add_journal_service,
    delete_journal_service,
    get_journal_service,
)


@pytest.fixture
def isolated_journal_store(monkeypatch, tmp_path):
    journal_dir = tmp_path / "journal-store"
    db_path = journal_dir / "trade_journal.db"
    csv_path = journal_dir / "trade_journal.csv"

    monkeypatch.setattr(journal_repository, "JOURNAL_DB_PATH", db_path)
    monkeypatch.setattr(journal_repository, "JOURNAL_CSV_PATH", csv_path)

    return db_path, csv_path


def test_journal_service_uses_sqlite_storage(isolated_journal_store):
    db_path, _ = isolated_journal_store

    created = add_journal_service(
        {
            "symbol": "BTC/USDT",
            "timeframe": "4h",
            "direction": "Long",
            "entry_price": 100.0,
            "exit_price": 110.0,
            "pnl_pct": 10.0,
            "outcome": "Win",
        }
    )

    assert created["success"] is True
    assert created["data"]["id"] == 1
    assert db_path.exists()

    fetched = get_journal_service()
    assert fetched["success"] is True
    assert len(fetched["data"]) == 1
    assert fetched["data"][0]["symbol"] == "BTC/USDT"

    deleted = delete_journal_service(1)
    assert deleted == {"success": True, "message": "Entry deleted"}

    after_delete = get_journal_service()
    assert after_delete["data"] == []


def test_journal_service_migrates_legacy_csv_and_is_cwd_independent(
    isolated_journal_store,
    monkeypatch,
    tmp_path,
):
    db_path, csv_path = isolated_journal_store
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {
                "id": 1,
                "datetime": "2026-03-01T00:00:00+00:00",
                "symbol": "ETH/USDT",
                "timeframe": "1h",
                "direction": "Long",
                "strategy_id": "A1",
                "size": 1.0,
                "entry_price": 2000.0,
                "exit_price": 2100.0,
                "pnl_pct": 5.0,
                "r_multiple": 1.5,
                "outcome": "Win",
                "emotion": "Calm",
                "tags": "breakout",
                "mistakes": "",
                "notes": "legacy row",
                "created_at": "2026-03-01T01:00:00+00:00",
            },
            {
                "id": 2,
                "datetime": "2026-03-02T00:00:00+00:00",
                "symbol": "SOL/USDT",
                "timeframe": "4h",
                "direction": "Short",
                "strategy_id": "B1",
                "size": 2.0,
                "entry_price": 150.0,
                "exit_price": 140.0,
                "pnl_pct": 6.67,
                "r_multiple": 2.0,
                "outcome": "Win",
                "emotion": "Confident",
                "tags": "trend",
                "mistakes": "",
                "notes": "legacy row 2",
                "created_at": "2026-03-02T01:00:00+00:00",
            },
        ]
    ).to_csv(csv_path, index=False)

    other_cwd = tmp_path / "elsewhere"
    other_cwd.mkdir()
    monkeypatch.chdir(other_cwd)

    fetched = get_journal_service()
    assert fetched["success"] is True
    assert [row["id"] for row in fetched["data"]] == [1, 2]
    assert db_path.exists()

    created = add_journal_service({"symbol": "XRP/USDT", "outcome": "Loss"})
    assert created["success"] is True
    assert created["data"]["id"] == 3

    fetched_again = get_journal_service()
    assert len(fetched_again["data"]) == 3
