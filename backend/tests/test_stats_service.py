from __future__ import annotations

import pandas as pd

from modules.stats import service as stats_service


def test_run_bb_mid_analysis_builds_excursions_without_quartile_calculation(monkeypatch):
    monkeypatch.setattr(
        stats_service,
        "_load_data_for_analysis",
        lambda coin, interval, use_csv, total_candles=2000: pd.DataFrame({"close": [1.0]}),
    )
    monkeypatch.setattr(stats_service, "add_bb_indicators", lambda df: df)
    monkeypatch.setattr(
        stats_service,
        "analyze_bb_mid_touch",
        lambda **kwargs: {
            "events": 2,
            "success": 1,
            "success_rate": 50.0,
            "avg_bars_to_mid": 3.0,
        },
    )
    monkeypatch.setattr(
        stats_service,
        "collect_event_returns",
        lambda **kwargs: {"mfe": [2.0, 4.0], "mae": [-1.0, -3.0], "end": [1.5, 2.5]},
    )

    result = stats_service.run_bb_mid_analysis(
        coin="BTC",
        intervals=["4h"],
        start_side="lower",
        max_bars=7,
        regime=None,
        use_csv=False,
    )

    assert result["success"] is True
    assert result["data"] == [
        {
            "interval": "4h",
            "events": 2,
            "success": 1,
            "success_rate": 50.0,
            "avg_bars_to_mid": 3.0,
        }
    ]
    assert result["excursions"] == {
        "4h": {
            "avg_mfe": 3.0,
            "avg_mae": -2.0,
            "avg_end": 2.0,
        }
    }
