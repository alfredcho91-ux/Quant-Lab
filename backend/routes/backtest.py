# routes/backtest.py
"""백테스트 API 엔드포인트"""

from fastapi import APIRouter
import sys
from pathlib import Path

# Add parent path for importing core modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.request import BacktestParams, AdvancedBacktestParams
from services.backtest_logic import calculate_advanced_stats, run_monte_carlo
from utils.data_loader import load_data_for_analysis
from utils.decorators import handle_api_errors
from core.indicators import prepare_strategy_data
from core.backtest import run_backtest
from core.strategies import STRATS
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api", tags=["backtest"])


@router.post("/backtest")
@handle_api_errors(include_traceback=True)
async def api_backtest(params: BacktestParams):
    """Run backtest with given parameters"""
    # Load data using common loader
    df, _ = load_data_for_analysis(
        params.coin,
        params.interval,
        params.use_csv,
        total_candles=3000
    )
    
    # Prepare strategy data with indicators
    df = prepare_strategy_data(
        df,
        rsi_ob_level=params.rsi_ob,
        rsi2_ob_level=params.rsi2_ob,
        ema_len=params.ema_len,
        sma1_len=params.sma1_len,
        sma2_len=params.sma2_len,
        adx_threshold=params.adx_thr,
        donch_lookback=params.donch,
        bb_length=params.bb_length,
        bb_std_mult=params.bb_std_mult,
        atr_length=params.atr_length,
        kc_mult=params.kc_mult,
        vol_ma_length=params.vol_ma_length,
        vol_spike_k=params.vol_spike_k,
        macd_fast=params.macd_fast,
        macd_slow=params.macd_slow,
        macd_signal=params.macd_signal,
    )
    
    # Find strategy
    strat = next((s for s in STRATS if s["id"] == params.strategy_id), None)
    if strat is None:
        return {"success": False, "error": f"Strategy {params.strategy_id} not found"}
    
    sig_col = f"{strat['prefix']}_{params.direction}"
    
    # Warmup bars removal
    warmup_bars = max(params.ema_len, params.sma2_len) + 100
    if len(df) > warmup_bars:
        df_bt = df.iloc[warmup_bars:].copy()
    else:
        df_bt = df.copy()
    
    # Run backtest
    res = run_backtest(
        df_bt,
        sig_col,
        direction=params.direction,
        strategy_type=strat["logic"],
        tp_pct=params.tp_pct / 100.0,
        sl_pct=params.sl_pct / 100.0,
        max_bars=params.max_bars,
        leverage=params.leverage,
        fee_entry_rate=params.entry_fee_pct / 100.0,
        fee_exit_rate=params.exit_fee_pct / 100.0,
    )
    
    # Prepare chart data
    df["open_dt"] = df["open_dt"].astype(str)
    chart_cols = ["open_dt", "open", "high", "low", "close", "volume",
                  "RSI", "EMA_main", "SMA_1", "SMA_2", "BB_Up", "BB_Low", "BB_Mid",
                  "ADX", "Regime", "MACD", "MACD_signal", "MACD_hist"]
    chart_cols = [c for c in chart_cols if c in df.columns]
    chart_data = df[chart_cols].tail(800).to_dict(orient="records")
    
    # Prepare trades data
    trades_data = []
    summary = {"n_trades": 0, "win_rate": 0, "total_pnl": 0, "liq_count": 0}
    
    if not res.empty:
        res["Entry Time"] = res["Entry Time"].astype(str)
        res["Exit Time"] = res["Exit Time"].astype(str)
        trades_data = res.to_dict(orient="records")
        
        wins = res[res["PnL"] > 0]
        summary = {
            "n_trades": len(res),
            "win_rate": (len(wins) / len(res) * 100) if len(res) > 0 else 0,
            "total_pnl": res["PnL"].sum() * 100,
            "liq_count": int((res["Outcome"] == "💀 Liquidation").sum()),
            "avg_pnl": res["PnL"].mean() * 100,
        }
        
        # Regime performance
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
    
    return {
        "success": True,
        "chart_data": chart_data,
        "trades": trades_data,
        "summary": summary,
    }


@router.post("/backtest-advanced")
@handle_api_errors(include_traceback=True)
async def api_backtest_advanced(params: AdvancedBacktestParams):
    """Run advanced backtest with train/test split and statistics"""
    # Load data using common loader
    df, _ = load_data_for_analysis(
        params.coin,
        params.interval,
        params.use_csv,
        total_candles=3000
    )
    
    # Prepare strategy data
    df = prepare_strategy_data(
        df,
        rsi_ob_level=params.rsi_ob,
        rsi2_ob_level=params.rsi2_ob,
        ema_len=params.ema_len,
        sma1_len=params.sma1_len,
        sma2_len=params.sma2_len,
        adx_threshold=params.adx_thr,
        donch_lookback=params.donch,
        bb_length=params.bb_length,
        bb_std_mult=params.bb_std_mult,
        atr_length=params.atr_length,
        kc_mult=params.kc_mult,
        vol_ma_length=params.vol_ma_length,
        vol_spike_k=params.vol_spike_k,
        macd_fast=params.macd_fast,
        macd_slow=params.macd_slow,
        macd_signal=params.macd_signal,
    )
    
    strat = next((s for s in STRATS if s["id"] == params.strategy_id), None)
    if strat is None:
        return {"success": False, "error": f"Strategy {params.strategy_id} not found"}
    
    sig_col = f"{strat['prefix']}_{params.direction}"
    
    # Warmup removal
    warmup_bars = max(params.ema_len, params.sma2_len) + 100
    if len(df) > warmup_bars:
        df_bt = df.iloc[warmup_bars:].copy()
    else:
        df_bt = df.copy()
    
    # Split into train/test
    split_idx = int(len(df_bt) * params.train_ratio)
    df_train = df_bt.iloc[:split_idx].copy()
    df_test = df_bt.iloc[split_idx:].copy()
    
    # Helper function to run backtest and get summary
    def run_and_summarize(data):
        res = run_backtest(
            data,
            sig_col,
            direction=params.direction,
            strategy_type=strat["logic"],
            tp_pct=params.tp_pct / 100.0,
            sl_pct=params.sl_pct / 100.0,
            max_bars=params.max_bars,
            leverage=params.leverage,
            fee_entry_rate=params.entry_fee_pct / 100.0,
            fee_exit_rate=params.exit_fee_pct / 100.0,
        )
        
        if res.empty:
            return res, {
                "n_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
            }
        
        wins = res[res["PnL"] > 0]
        summary = {
            "n_trades": len(res),
            "win_rate": (len(wins) / len(res) * 100) if len(res) > 0 else 0,
            "total_pnl": res["PnL"].sum() * 100,
            "avg_pnl": res["PnL"].mean() * 100,
        }
        return res, summary
    
    # Run on train set (In-Sample)
    train_res, train_summary = run_and_summarize(df_train)
    train_stats = calculate_advanced_stats(train_res)
    
    # Run on test set (Out-of-Sample)
    test_res, test_summary = run_and_summarize(df_test)
    test_stats = calculate_advanced_stats(test_res)
    
    # Run on full data for overall view
    full_res, full_summary = run_and_summarize(df_bt)
    full_stats = calculate_advanced_stats(full_res)
    
    # Monte Carlo simulation on test results
    monte_carlo = {}
    if not test_res.empty:
        monte_carlo = run_monte_carlo(test_res["PnL"].values, params.monte_carlo_runs)
    
    # Prepare chart data
    df["open_dt"] = df["open_dt"].astype(str)
    chart_cols = ["open_dt", "open", "high", "low", "close", "volume", "RSI", "ADX", "Regime"]
    chart_cols = [c for c in chart_cols if c in df.columns]
    chart_data = df[chart_cols].tail(500).to_dict(orient="records")
    
    # Prepare trades data
    trades_data = []
    if not full_res.empty:
        full_res["Entry Time"] = full_res["Entry Time"].astype(str)
        full_res["Exit Time"] = full_res["Exit Time"].astype(str)
        trades_data = full_res.to_dict(orient="records")
    
    # Data info
    train_start = str(df_train["open_dt"].iloc[0]) if not df_train.empty else None
    train_end = str(df_train["open_dt"].iloc[-1]) if not df_train.empty else None
    test_start = str(df_test["open_dt"].iloc[0]) if not df_test.empty else None
    test_end = str(df_test["open_dt"].iloc[-1]) if not df_test.empty else None
    
    return {
        "success": True,
        "chart_data": chart_data,
        "trades": trades_data,
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
