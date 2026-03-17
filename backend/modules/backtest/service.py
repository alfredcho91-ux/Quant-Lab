"""Backtest API service layer."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import pandas as pd

from core.backtest import run_backtest
from core.indicators import build_indicator_adapter
from core.strategies import STRATS
from models.request import AdvancedBacktestParams, BacktestParams
from services.statistics import calculate_advanced_stats, run_monte_carlo
from utils.data_loader import load_data_for_analysis


def _load_and_prepare_data(params: BacktestParams | AdvancedBacktestParams) -> pd.DataFrame:
    """Load OHLCV data and prepare strategy indicators."""
    df, _ = load_data_for_analysis(
        params.coin,
        params.interval,
        params.use_csv,
        total_candles=3000,
    )

    return build_indicator_adapter(
        df,
        mode="backtest",
        prepare_kwargs={
            "rsi_ob_level": params.rsi_ob,
            "sma_main_len": params.sma_main_len,
            "sma1_len": params.sma1_len,
            "sma2_len": params.sma2_len,
            "adx_threshold": params.adx_thr,
            "donch_lookback": params.donch,
            "bb_length": params.bb_length,
            "bb_std_mult": params.bb_std_mult,
            "atr_length": params.atr_length,
            "kc_mult": params.kc_mult,
            "vol_ma_length": params.vol_ma_length,
            "vol_spike_k": params.vol_spike_k,
            "macd_fast": params.macd_fast,
            "macd_slow": params.macd_slow,
            "macd_signal": params.macd_signal,
        },
    )


def _find_strategy(strategy_id: str) -> Dict[str, Any] | None:
    return next((s for s in STRATS if s["id"] == strategy_id), None)


def _apply_warmup(df: pd.DataFrame, sma_main_len: int, sma2_len: int) -> pd.DataFrame:
    warmup_bars = max(sma_main_len, sma2_len) + 100
    if len(df) > warmup_bars:
        return df.iloc[warmup_bars:].copy()
    return df.copy()


def _run_backtest_core(
    df_bt: pd.DataFrame,
    params: BacktestParams | AdvancedBacktestParams,
    strategy_logic: str,
    sig_col: str,
) -> pd.DataFrame:
    return run_backtest(
        df_bt,
        sig_col,
        direction=params.direction,
        strategy_type=strategy_logic,
        tp_pct=params.tp_pct / 100.0,
        sl_pct=params.sl_pct / 100.0,
        max_bars=params.max_bars,
        leverage=params.leverage,
        fee_entry_rate=params.entry_fee_pct / 100.0,
        fee_exit_rate=params.exit_fee_pct / 100.0,
    )


def _build_chart_data(df: pd.DataFrame, chart_cols: list[str], limit: int) -> list[Dict[str, Any]]:
    chart_df = df.copy()
    chart_df["open_dt"] = chart_df["open_dt"].astype(str)
    final_cols = [c for c in chart_cols if c in chart_df.columns]
    return chart_df[final_cols].tail(limit).to_dict(orient="records")


def _summarize_trades(res: pd.DataFrame, include_regime: bool = False) -> Dict[str, Any]:
    if res.empty:
        return {"n_trades": 0, "win_rate": 0, "total_pnl": 0, "liq_count": 0}

    wins = res[res["PnL"] > 0]
    summary: Dict[str, Any] = {
        "n_trades": len(res),
        "win_rate": (len(wins) / len(res) * 100) if len(res) > 0 else 0,
        "total_pnl": res["PnL"].sum() * 100,
        "avg_pnl": res["PnL"].mean() * 100,
    }
    if "Outcome" in res.columns:
        summary["liq_count"] = int((res["Outcome"] == "💀 Liquidation").sum())

    if include_regime and "Regime" in res.columns:
        regime_stats = (
            res.groupby("Regime")["PnL"]
            .agg(
                Count="count",
                WinRate=lambda x: (x > 0).mean() * 100,
                AvgPnL=lambda x: x.mean() * 100,
            )
            .reset_index()
            .to_dict(orient="records")
        )
        summary["regime_stats"] = regime_stats

    return summary


def _format_trades(res: pd.DataFrame) -> list[Dict[str, Any]]:
    if res.empty:
        return []
    trades = res.copy()
    trades["Entry Time"] = trades["Entry Time"].astype(str)
    trades["Exit Time"] = trades["Exit Time"].astype(str)
    return trades.to_dict(orient="records")


def run_backtest_service(params: BacktestParams) -> Dict[str, Any]:
    """Run standard backtest response flow."""
    df = _load_and_prepare_data(params)
    strat = _find_strategy(params.strategy_id)
    if strat is None:
        return {"success": False, "error": f"Strategy {params.strategy_id} not found"}

    sig_col = f"{strat['prefix']}_{params.direction}"
    df_bt = _apply_warmup(df, params.sma_main_len, params.sma2_len)
    res = _run_backtest_core(df_bt, params, strat["logic"], sig_col)

    chart_cols = [
        "open_dt",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "RSI",
        "SMA_main",
        "SMA_1",
        "SMA_2",
        "BB_Up",
        "BB_Low",
        "BB_Mid",
        "ADX",
        "Regime",
        "MACD",
        "MACD_signal",
        "MACD_hist",
    ]
    chart_data = _build_chart_data(df, chart_cols, limit=800)

    return {
        "success": True,
        "chart_data": chart_data,
        "trades": _format_trades(res),
        "summary": _summarize_trades(res, include_regime=True),
    }


def _run_and_summarize(
    data: pd.DataFrame,
    params: AdvancedBacktestParams,
    strategy_logic: str,
    sig_col: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    res = _run_backtest_core(data, params, strategy_logic, sig_col)
    if res.empty:
        return res, {"n_trades": 0, "win_rate": 0, "total_pnl": 0, "avg_pnl": 0}
    return res, _summarize_trades(res, include_regime=False)


def run_backtest_advanced_service(params: AdvancedBacktestParams) -> Dict[str, Any]:
    """Run advanced backtest with train/test split and statistics."""
    df = _load_and_prepare_data(params)
    strat = _find_strategy(params.strategy_id)
    if strat is None:
        return {"success": False, "error": f"Strategy {params.strategy_id} not found"}

    sig_col = f"{strat['prefix']}_{params.direction}"
    df_bt = _apply_warmup(df, params.sma_main_len, params.sma2_len)

    split_idx = int(len(df_bt) * params.train_ratio)
    df_train = df_bt.iloc[:split_idx].copy()
    df_test = df_bt.iloc[split_idx:].copy()

    train_res, train_summary = _run_and_summarize(df_train, params, strat["logic"], sig_col)
    test_res, test_summary = _run_and_summarize(df_test, params, strat["logic"], sig_col)
    full_res, full_summary = _run_and_summarize(df_bt, params, strat["logic"], sig_col)

    train_stats = calculate_advanced_stats(train_res)
    test_stats = calculate_advanced_stats(test_res)
    full_stats = calculate_advanced_stats(full_res)

    monte_carlo = {}
    if not test_res.empty:
        monte_carlo = run_monte_carlo(test_res["PnL"].values, params.monte_carlo_runs)

    chart_cols = ["open_dt", "open", "high", "low", "close", "volume", "RSI", "ADX", "Regime"]
    chart_data = _build_chart_data(df, chart_cols, limit=500)

    train_start = str(df_train["open_dt"].iloc[0]) if not df_train.empty else None
    train_end = str(df_train["open_dt"].iloc[-1]) if not df_train.empty else None
    test_start = str(df_test["open_dt"].iloc[0]) if not df_test.empty else None
    test_end = str(df_test["open_dt"].iloc[-1]) if not df_test.empty else None

    return {
        "success": True,
        "chart_data": chart_data,
        "trades": _format_trades(full_res),
        "in_sample": {
            "summary": train_summary,
            "stats": train_stats,
            "period": {"start": train_start, "end": train_end},
        },
        "out_of_sample": {
            "summary": test_summary,
            "stats": test_stats,
            "period": {"start": test_start, "end": test_end},
        },
        "full": {
            "summary": full_summary,
            "stats": full_stats,
        },
        "monte_carlo": monte_carlo,
    }
