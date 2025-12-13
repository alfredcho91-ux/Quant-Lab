# backend/main.py
"""
FastAPI Backend for WolGem's Quant Master React Application
Provides REST API endpoints for market data, indicators, backtesting, etc.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys

# Add parent path for importing core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.indicators import prepare_strategy_data, calculate_adx
from core.backtest import run_backtest, summarize_trades
from core.support_resistance import (
    build_sr_levels_from_swings,
    compute_daily_pivots,
    compute_htf_sr_levels,
)
from core.strategies import STRATS
from core.presets import load_presets, save_presets

from data_service import (
    fetch_live_data,
    load_csv_data,
    get_market_prices,
    get_fear_and_greed_index,
    discover_timeframes,
)

app = FastAPI(
    title="WolGem Quant Master API",
    description="Backend API for crypto trading analysis platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Pydantic Models ==========

class BacktestParams(BaseModel):
    coin: str = "BTC"
    interval: str = "1h"
    strategy_id: str = "Connors"
    direction: str = "Long"
    tp_pct: float = 2.0
    sl_pct: float = 1.0
    max_bars: int = 48
    leverage: int = 10
    entry_fee_pct: float = 0.04
    exit_fee_pct: float = 0.04
    rsi_ob: int = 70
    rsi2_ob: int = 80
    ema_len: int = 200
    sma1_len: int = 20
    sma2_len: int = 60
    adx_thr: int = 25
    donch: int = 20
    bb_length: int = 20
    bb_std_mult: float = 2.0
    atr_length: int = 20
    kc_mult: float = 1.5
    vol_ma_length: int = 20
    vol_spike_k: float = 2.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    use_csv: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PresetSaveRequest(BaseModel):
    name: str
    coin: str
    interval: str
    strat_id: str
    direction: str
    params: Dict[str, Any]


# ========== API Endpoints ==========

@app.get("/")
async def root():
    return {"message": "WolGem Quant Master API is running!"}


@app.get("/api/market/prices")
async def api_market_prices():
    """Get current market prices for major coins"""
    try:
        prices = get_market_prices()
        if prices is None:
            return {"success": False, "data": None, "error": "Failed to fetch prices"}
        
        result = {}
        for symbol, data in prices.items():
            coin = symbol.replace("/USDT", "")
            result[coin] = {
                "last": data.get("last", 0),
                "percentage": data.get("percentage", 0),
                "high": data.get("high", 0),
                "low": data.get("low", 0),
                "volume": data.get("quoteVolume", 0),
            }
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


@app.get("/api/market/fear-greed")
async def api_fear_greed():
    """Get Fear & Greed Index"""
    try:
        fng = get_fear_and_greed_index()
        if fng is None:
            return {"success": False, "data": None}
        return {"success": True, "data": fng}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


@app.get("/api/timeframes/{coin}")
async def api_timeframes(coin: str):
    """Get available timeframes for a coin"""
    try:
        all_tfs, binance_tfs, csv_tfs = discover_timeframes(coin)
        return {
            "success": True,
            "data": {
                "all": all_tfs,
                "binance": list(binance_tfs),
                "csv": csv_tfs,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/strategies")
async def api_strategies():
    """Get list of available strategies"""
    return {"success": True, "data": STRATS}


@app.get("/api/ohlcv/{coin}/{interval}")
async def api_ohlcv(coin: str, interval: str, use_csv: bool = False, limit: int = 3000):
    """Get OHLCV data for a coin and interval"""
    try:
        df = None
        source = "api"
        
        if use_csv:
            df, info = load_csv_data(coin, interval)
            source = "csv"
        
        if df is None:
            df = fetch_live_data(f"{coin}/USDT", interval, total_candles=limit)
            source = "api"
        
        if df is None or df.empty:
            return {"success": False, "error": "Failed to load data"}
        
        # Convert to JSON-serializable format
        df["open_dt"] = df["open_dt"].astype(str)
        data = df.to_dict(orient="records")
        
        return {
            "success": True,
            "data": data,
            "source": source,
            "count": len(data),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/backtest")
async def api_backtest(params: BacktestParams):
    """Run backtest with given parameters"""
    try:
        # Load data
        df = None
        if params.use_csv:
            df, _ = load_csv_data(params.coin, params.interval)
        
        if df is None:
            df = fetch_live_data(f"{params.coin}/USDT", params.interval, total_candles=3000)
        
        if df is None or df.empty:
            return {"success": False, "error": "Failed to load data"}
        
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
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/support-resistance/{coin}/{interval}")
async def api_support_resistance(
    coin: str,
    interval: str,
    lookback: int = 3,
    tolerance_pct: float = 0.3,
    min_touches: int = 3,
    show_pivots: bool = False,
    htf_option: str = "none",
):
    """Calculate support/resistance levels"""
    try:
        df = fetch_live_data(f"{coin}/USDT", interval, total_candles=1000)
        if df is None or df.empty:
            return {"success": False, "error": "Failed to load data"}
        
        frames = []
        
        # Swing-based SR levels
        sr_main = build_sr_levels_from_swings(
            df,
            lookback=lookback,
            tolerance_pct=tolerance_pct / 100.0,
            min_touches=min_touches,
            timeframe_label=interval,
        )
        if not sr_main.empty:
            frames.append(sr_main)
        
        # Daily pivots
        if show_pivots:
            pivots = compute_daily_pivots(df, last_n=1)
            if not pivots.empty:
                frames.append(pivots)
        
        # HTF levels
        if htf_option != "none":
            rule = "4H" if htf_option == "4H" else "1D"
            htf_levels = compute_htf_sr_levels(
                df,
                rule=rule,
                lookback=lookback,
                tolerance_pct=tolerance_pct / 100.0,
                min_touches=min_touches,
            )
            if not htf_levels.empty:
                frames.append(htf_levels)
        
        if frames:
            all_levels = pd.concat(frames, ignore_index=True)
            return {"success": True, "data": all_levels.to_dict(orient="records")}
        
        return {"success": True, "data": []}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/presets")
async def api_get_presets():
    """Get all saved presets"""
    try:
        presets = load_presets()
        return {"success": True, "data": presets}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/presets")
async def api_save_preset(request: PresetSaveRequest):
    """Save a preset"""
    try:
        presets = load_presets()
        presets[request.name] = {
            "coin": request.coin,
            "interval": request.interval,
            "strat_id": request.strat_id,
            "direction": request.direction,
            "params": request.params,
        }
        save_presets(presets)
        return {"success": True, "message": "Preset saved"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/api/presets/{name}")
async def api_delete_preset(name: str):
    """Delete a preset"""
    try:
        presets = load_presets()
        if name in presets:
            del presets[name]
            save_presets(presets)
        return {"success": True, "message": "Preset deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== Strategy Explainer ==========

@app.get("/api/strategy-info/{strategy_id}")
async def api_strategy_info(
    strategy_id: str,
    lang: str = "ko",
    rsi_ob: int = 70,
    rsi2_ob: int = 80,
    ema_len: int = 200,
    sma1_len: int = 20,
    sma2_len: int = 60,
):
    """Get strategy explanation"""
    rsi_os = 100 - rsi_ob
    rsi2_os = 100 - rsi2_ob
    
    explainers_ko = {
        "Connors": {
            "concept": "아주 짧은 RSI(2)로 극단의 과매도/과매수 구간에서 반등(되돌림)을 노리는 전략.",
            "Long": f"RSI(2) < {rsi2_os} & 가격 > EMA({ema_len}). 청산: TP/SL 또는 SMA({sma1_len}) 재돌파.",
            "Short": f"RSI(2) > {rsi2_ob} & 가격 < EMA({ema_len}). 청산: TP/SL 또는 SMA({sma1_len}) 재하향.",
            "regime": "횡보~약한 추세, 급등락 직후 기술적 반등/반납.",
        },
        "Sqz": {
            "concept": "BB가 KC 안으로 들어가는 스퀴즈 후 재확장 시 추세 시작을 탄다.",
            "Long": "직전까지 스퀴즈 ON, 현재 해제 + 종가 BB 중단선 위.",
            "Short": "직전까지 스퀴즈 ON, 현재 해제 + 종가 BB 중단선 아래.",
            "regime": "변동성 수축 직후.",
        },
        "Turtle": {
            "concept": "Donchian 고가/저가 돌파 추세 추종.",
            "Long": "종가가 Donchian High 상향 돌파 & EMA 위.",
            "Short": "종가가 Donchian Low 하향 돌파 & EMA 아래.",
            "regime": "강한 불/베어 추세에 유리, 횡보 시 휩쏘 주의.",
        },
        "MR": {
            "concept": "밴드 밖 오버슈팅 후 평균 회귀.",
            "Long": f"종가 < BB 하단 & RSI(14) < {rsi_os} & EMA 위.",
            "Short": f"종가 > BB 상단 & RSI(14) > {rsi_ob} & EMA 아래.",
            "regime": "횡보 또는 과열 직후.",
        },
        "RSI": {
            "concept": "RSI(14) 단일 임계 기반 역추세 진입.",
            "Long": f"RSI(14) < {rsi_os}.",
            "Short": f"RSI(14) > {rsi_ob}.",
            "regime": "박스권/횡보.",
        },
        "MA": {
            "concept": "SMA1/SMA2 골든·데드 크로스.",
            "Long": f"SMA({sma1_len})가 SMA({sma2_len}) 상향 교차.",
            "Short": f"SMA({sma1_len})가 SMA({sma2_len}) 하향 교차.",
            "regime": "완만한 추세 발생/전환.",
        },
        "BB": {
            "concept": "볼밴 돌파를 모멘텀 시그널로 사용.",
            "Long": "상단 밴드 상향 돌파(이전 봉은 하단).",
            "Short": "하단 밴드 하향 돌파(이전 봉은 상단).",
            "regime": "초기 모멘텀.",
        },
        "Engulf": {
            "concept": "장악형 캔들 반전 패턴.",
            "Long": "이전 음봉 + 현재 양봉, 현재 몸통이 이전 몸통 장악.",
            "Short": "이전 양봉 + 현재 음봉, 현재 몸통이 이전 몸통 장악.",
            "regime": "전환 초입 단기 반전.",
        },
    }
    
    explainers_en = {
        "Connors": {
            "concept": "Very short RSI(2) reversion to capture snapbacks after extreme moves.",
            "Long": f"RSI(2) < {rsi2_os} & price > EMA({ema_len}). Exit: TP/SL or price crosses above SMA({sma1_len}) again.",
            "Short": f"RSI(2) > {rsi2_ob} & price < EMA({ema_len}). Exit: TP/SL or price crosses below SMA({sma1_len}) again.",
            "regime": "Range to mild trend; after panic drops/pumps.",
        },
        "Sqz": {
            "concept": "Volatility contraction (BB inside KC) followed by expansion = trend ignition.",
            "Long": "Squeeze was ON and just released; close > BB mid.",
            "Short": "Squeeze was ON and just released; close < BB mid.",
            "regime": "Right after volatility squeeze.",
        },
        "Turtle": {
            "concept": "Donchian breakout trend-following.",
            "Long": "Close breaks recent Donchian High & close > EMA.",
            "Short": "Close breaks recent Donchian Low & close < EMA.",
            "regime": "Strong Bull/Bear trends; beware whipsaws in ranges.",
        },
        "MR": {
            "concept": "Mean reversion after overshoot beyond the bands.",
            "Long": f"Close < BB low & RSI(14) < {rsi_os} & close > EMA.",
            "Short": f"Close > BB upper & RSI(14) > {rsi_ob} & close < EMA.",
            "regime": "Sideways or right after volatility blow-off.",
        },
        "RSI": {
            "concept": "Simple RSI(14) reversal using a single threshold.",
            "Long": f"RSI(14) < {rsi_os}.",
            "Short": f"RSI(14) > {rsi_ob}.",
            "regime": "Ranges/boxes.",
        },
        "MA": {
            "concept": "SMA1/SMA2 golden/death cross.",
            "Long": f"SMA({sma1_len}) crosses up SMA({sma2_len}).",
            "Short": f"SMA({sma1_len}) crosses down SMA({sma2_len}).",
            "regime": "Gentle emerging trends.",
        },
        "BB": {
            "concept": "Bollinger band breakout as momentum trigger.",
            "Long": "Close breaks the upper band (was below in prior bar).",
            "Short": "Close breaks the lower band (was above in prior bar).",
            "regime": "Early momentum phases.",
        },
        "Engulf": {
            "concept": "Bullish/Bearish engulfing candlestick reversal.",
            "Long": "Prev red, current green; current body engulfs previous body.",
            "Short": "Prev green, current red; current body engulfs previous body.",
            "regime": "Short-term reversals around turning points.",
        },
    }
    
    explainers = explainers_ko if lang == "ko" else explainers_en
    
    if strategy_id not in explainers:
        return {"success": False, "error": f"Strategy {strategy_id} not found"}
    
    return {"success": True, "data": explainers[strategy_id]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

