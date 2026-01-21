# routes/scanner.py
"""스캐너 API 엔드포인트"""

from fastapi import APIRouter
import sys
from pathlib import Path

# Add parent path for importing core modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.request import PatternScanParams, ScannerParams
from services.pattern_logic import detect_patterns, compute_pattern_stats
from utils.data_loader import load_data_for_analysis
from utils.decorators import handle_api_errors
from core.indicators import prepare_strategy_data
from core.strategies import STRATS
from core.presets import load_presets
import pandas as pd

router = APIRouter(prefix="/api", tags=["scanner"])


@router.post("/pattern-scanner")
@handle_api_errors(include_traceback=True)
async def api_pattern_scanner(params: PatternScanParams):
    """Run pattern scanner"""
    tf_stats = {}
    
    for interval in params.intervals:
        # Load data using common loader
        try:
            df, _ = load_data_for_analysis(
                params.coin,
                interval,
                params.use_csv,
                total_candles=500
            )
        except ValueError:
            continue
        
        patterns = detect_patterns(df)
        stats = compute_pattern_stats(
            df, patterns, params.horizon, params.tp_pct / 100.0,
            params.mode, params.position
        )
        tf_stats[interval] = stats
    
    return {
        "success": True,
        "data": tf_stats,
        "mode": params.mode,
        "position": params.position,
    }


@router.post("/scanner")
@handle_api_errors(include_traceback=True)
async def api_scanner(params: ScannerParams):
    """Scan multiple strategies for current signals"""
    # Load data using common loader
    df, _ = load_data_for_analysis(
        params.coin,
        params.interval,
        params.use_csv,
        total_candles=600
    )
    
    # Prepare with default parameters
    df = prepare_strategy_data(df)
    
    last_row = df.iloc[-1]
    
    # Get signals for all strategies
    signals = []
    target_strats = params.strategies if params.strategies else [s["id"] for s in STRATS]
    
    for strat in STRATS:
        if strat["id"] not in target_strats:
            continue
        
        prefix = strat["prefix"]
        long_sig = bool(last_row.get(f"{prefix}_Long", False))
        short_sig = bool(last_row.get(f"{prefix}_Short", False))
        
        signals.append({
            "id": strat["id"],
            "name_ko": strat["name_ko"],
            "name_en": strat["name_en"],
            "long_signal": long_sig,
            "short_signal": short_sig,
        })
    
    # Market context
    market_context = {
        "last_time": str(last_row["open_dt"]),
        "last_close": float(last_row["close"]),
        "regime": str(last_row.get("Regime", "Unknown")),
        "adx": float(last_row.get("ADX", 0)),
        "rsi": float(last_row.get("RSI", 50)),
        "rsi2": float(last_row.get("RSI_2", 50)) if "RSI_2" in last_row else None,
    }
    
    # Load presets and scan them too
    presets = load_presets()
    preset_signals = []
    
    for name, cfg in presets.items():
        p = cfg.get("params", {})
        
        # Recompute with preset parameters
        df_preset = prepare_strategy_data(
            df,
            rsi_ob_level=p.get("rsi_ob", 70),
            rsi2_ob_level=p.get("rsi2_ob", 80),
            ema_len=p.get("ema_len", 200),
            sma1_len=p.get("sma1_len", 20),
            sma2_len=p.get("sma2_len", 60),
            adx_threshold=p.get("adx_thr", 25),
            donch_lookback=p.get("donch", 20),
            bb_length=p.get("bb_length", 20),
            bb_std_mult=p.get("bb_std_mult", 2.0),
            atr_length=p.get("atr_length", 20),
            kc_mult=p.get("kc_mult", 1.5),
            vol_ma_length=p.get("vol_ma_len", 20),
            vol_spike_k=p.get("vol_spike_k", 2.0),
            macd_fast=p.get("macd_fast", 12),
            macd_slow=p.get("macd_slow", 26),
            macd_signal=p.get("macd_signal", 9),
        )
        
        last_preset = df_preset.iloc[-1]
        strat_id = cfg.get("strat_id")
        strat_info = next((s for s in STRATS if s["id"] == strat_id), None)
        
        if strat_info:
            prefix = strat_info["prefix"]
            long_sig = bool(last_preset.get(f"{prefix}_Long", False))
            short_sig = bool(last_preset.get(f"{prefix}_Short", False))
            
            preset_signals.append({
                "name": name,
                "strategy_id": strat_id,
                "long_signal": long_sig,
                "short_signal": short_sig,
            })
    
    return {
        "success": True,
        "signals": signals,
        "preset_signals": preset_signals,
        "market_context": market_context,
    }
