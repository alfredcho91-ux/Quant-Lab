"""Tests for streak conditional-breakdown payload fields."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd


backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

from strategy.context import AnalysisContext
from strategy.streak.simple_analyzer import calculate_simple_metrics


def _build_df(rows: int = 260) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=rows, freq="h")
    base = 100.0 + np.linspace(0, 12, rows)
    wave = np.sin(np.arange(rows) / 6.0) * 1.8
    close = base + wave
    open_ = close + np.where(np.arange(rows) % 2 == 0, -0.4, 0.4)
    high = np.maximum(open_, close) + 0.6
    low = np.minimum(open_, close) - 0.6
    volume = 1000.0 + (np.arange(rows) % 20) * 25.0

    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=idx,
    )
    df["is_green"] = df["close"] > df["open"]
    df["body_pct"] = (df["close"] - df["open"]) / df["open"] * 100
    df["rsi"] = np.linspace(25.0, 75.0, rows)
    df["atr_pct"] = 0.8 + (np.arange(rows) % 18) * 0.15
    df["disparity"] = 92.0 + (np.arange(rows) % 24)
    df["vol_change"] = np.sin(np.arange(rows) / 5.0) * 25.0
    return df


def test_simple_metrics_include_conditional_breakdown_fields():
    df = _build_df(rows=260)
    target_cases = df.iloc[20:220:5].copy()

    context = AnalysisContext(
        coin="BTC",
        interval="1h",
        n_streak=3,
        direction="green",
    )

    metrics = calculate_simple_metrics(df=df, target_cases=target_cases, context=context)

    assert "rsi_by_interval" in metrics
    assert "disp_by_interval" in metrics
    assert "atr_by_interval" in metrics
    assert "rsi_atr_heatmap" in metrics
    assert "high_prob_rsi_intervals" in metrics
    assert "high_prob_disp_intervals" in metrics
    assert "high_prob_atr_intervals" in metrics

    assert isinstance(metrics["rsi_by_interval"], dict)
    assert isinstance(metrics["disp_by_interval"], dict)
    assert isinstance(metrics["atr_by_interval"], dict)

    # 충분한 샘플에서는 각 조건 분해 테이블이 생성되어야 한다.
    assert len(metrics["rsi_by_interval"]) > 0
    assert len(metrics["disp_by_interval"]) > 0
    assert len(metrics["atr_by_interval"]) > 0

    heatmap = metrics["rsi_atr_heatmap"]
    assert isinstance(heatmap, dict)
    assert isinstance(heatmap.get("x_bins"), list)
    assert isinstance(heatmap.get("y_bins"), list)
    assert isinstance(heatmap.get("cells"), dict)
    assert len(heatmap["x_bins"]) > 0
    assert len(heatmap["y_bins"]) > 0
