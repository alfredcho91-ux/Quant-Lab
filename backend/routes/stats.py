# routes/stats.py
"""통계 분석 API 엔드포인트 (얇은 레이어) - 비즈니스 로직은 strategy/ 패키지로 분리"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# Add parent path for importing core modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.data_loader import load_data_for_analysis
from utils.decorators import handle_api_errors

# Import strategy modules
from strategy.bb_mid import (
    add_bb_indicators,
    analyze_bb_mid_touch,
    collect_event_returns,
    quartile_reach_stats,
)
from strategy.combo_filter import analyze_combo_filter, add_combo_indicators
from strategy.squeeze import analyze_multi_tf_squeeze
from strategy.weekly_pattern import analyze_weekly_pattern, analyze_weekly_pattern_manual
from strategy.weekly_pattern.backtest import run_weekly_pattern_backtest

router = APIRouter(prefix="/api", tags=["stats"])


# ========== Pydantic Models ==========

class BBMidParams(BaseModel):
    coin: str = "BTC"
    intervals: List[str] = ["1h", "4h"]
    start_side: str = "lower"
    max_bars: int = 7
    rsi_min: float = 0  # 기본값: 필터 없음
    rsi_max: float = 100  # 기본값: 필터 없음
    regime: Optional[str] = None
    use_csv: bool = False


class ComboFilterParams(BaseModel):
    coin: str = "BTC"
    interval: str = "1h"
    direction: str = "long"
    tp_pct: float = 1.0
    horizon: int = 5
    rsi_min: float = 40
    rsi_max: float = 60
    sma_short: int = 5
    sma_long: int = 20
    filter1_type: str = "none"
    filter1_params: Dict[str, Any] = {}
    filter2_type: str = "none"
    filter2_params: Dict[str, Any] = {}
    filter3_type: str = "none"
    filter3_params: Dict[str, Any] = {}
    use_csv: bool = False


class MultiTFSqueezeParams(BaseModel):
    coin: str = "BTC"
    high_tf: str = "2h"
    low_tf: str = "15m"
    squeeze_thr_high: float = 0.02
    squeeze_thr_low: float = 0.02
    lower_lookback_bars: int = 2
    rsi_min: float = 40
    rsi_max: float = 60
    require_above_mid: bool = True


class WeeklyPatternParams(BaseModel):
    coin: str = "ETH"
    interval: str = "1d"  # 주간 분석이므로 1d 필수
    direction: Optional[str] = None  # "down" (하락) 또는 "up" (상승), None이면 임계값으로 자동 판단
    deep_drop_threshold: float = -0.05  # 깊은 하락 임계값 (-5%)
    deep_rise_threshold: float = 0.05  # 깊은 상승 임계값 (+5%)
    rsi_threshold: float = 40  # 과매도/과매수 임계값 (하락: RSI < threshold, 상승: RSI > 100-threshold)


class WeeklyPatternManualParams(BaseModel):
    """주간 패턴 수동 입력 백테스트 파라미터"""
    coin: str = "ETH"
    monday_open: float  # 월요일 시가
    tuesday_close: float  # 화요일 종가
    wednesday_date: str  # 수요일 날짜 (YYYY-MM-DD 형식)


class WeeklyPatternBacktestParams(BaseModel):
    """주간 패턴 분석 기반 백테스트 파라미터"""
    coin: str = "ETH"
    interval: str = "1d"  # 주간 분석이므로 1d 필수
    direction: str = "down"  # "down" (하락) 또는 "up" (상승)
    deep_drop_threshold: float = -0.05  # 깊은 하락 임계값 (-5%)
    deep_rise_threshold: float = 0.05  # 깊은 상승 임계값 (+5%)
    rsi_threshold: float = 40  # 과매도/과매수 임계값
    leverage: int = 1  # 레버리지
    fee_entry_rate: float = 0.0005  # 진입 수수료율
    fee_exit_rate: float = 0.0005  # 청산 수수료율


# ========== Utility Functions ==========

def _load_data_for_analysis(coin: str, interval: str, use_csv: bool, total_candles: int = 2000):
    """Common data loading wrapper."""
    try:
        df, _ = load_data_for_analysis(coin, interval, use_csv, total_candles=total_candles)
        return df
    except ValueError:
        return None


def _get_optimal_candle_count(interval: str) -> int:
    """Get optimal candle count for interval."""
    counts = {
        "15m": 3000, "30m": 2500, "1h": 2000, "2h": 1500,
        "4h": 1000, "8h": 750, "12h": 500, "1d": 1000,
        "3d": 500, "1w": 500, "1M": 200,
    }
    return counts.get(interval, 2000)


# ========== API Endpoints ==========

@router.post("/bb-mid")
@handle_api_errors(include_traceback=True)
async def api_bb_mid(params: BBMidParams):
    """Calculate BB Mid Touch statistics"""
    results = []
    excursions = {}
    
    for interval in params.intervals:
        candle_count = _get_optimal_candle_count(interval)
        df = _load_data_for_analysis(params.coin, interval, params.use_csv, candle_count)
        
        if df is None or df.empty:
            results.append({
                "interval": interval,
                "events": 0,
                "success": 0,
                "success_rate": None,
                "error": "No data"
            })
            continue
        
        df = add_bb_indicators(df)
        
        stats = analyze_bb_mid_touch(
            df=df,
            start_side=params.start_side,
            max_bars=params.max_bars,
            rsi_range=(params.rsi_min, params.rsi_max),
            regime=params.regime,
        )
        
        event_returns = {}
        quartile_stats = {}
        if stats["events"] > 0:
            event_returns = collect_event_returns(
                df=df,
                start_side=params.start_side,
                max_bars=params.max_bars,
                rsi_range=(params.rsi_min, params.rsi_max),
                regime=params.regime,
            )
            quartile_stats = quartile_reach_stats(
                df=df,
                start_side=params.start_side,
                max_bars=params.max_bars,
                rsi_range=(params.rsi_min, params.rsi_max),
                regime=params.regime,
            )
            
            # Calculate averages for excursions
            mfe_list = event_returns.get("mfe", [])
            mae_list = event_returns.get("mae", [])
            end_list = event_returns.get("end", [])
            
            if mfe_list and mae_list and end_list:
                import numpy as np
                excursions[interval] = {
                    "avg_mfe": float(np.mean(mfe_list)),  # Already in percentage from logic.py
                    "avg_mae": float(np.mean(mae_list)),  # Already in percentage from logic.py
                    "avg_end": float(np.mean(end_list)),  # Already in percentage from logic.py
                }
        
        results.append({
            "interval": interval,
            "events": stats["events"],
            "success": stats["success"],
            "success_rate": stats["success_rate"],
            "avg_bars_to_mid": stats.get("avg_bars_to_mid"),
        })
    
    return {
        "success": True,
        "data": results,
        "excursions": excursions,
        "start_side": params.start_side,
    }


@router.post("/combo-filter")
@handle_api_errors(include_traceback=True)
async def api_combo_filter(params: ComboFilterParams):
    """Run combo filter backtest"""
    df = _load_data_for_analysis(params.coin, params.interval, params.use_csv)
    if df is None:
        return {"success": False, "error": "Failed to load data"}
    
    stats = analyze_combo_filter(params.model_dump(), df)
    
    return {"success": True, "data": stats}


@router.post("/multi-tf-squeeze")
@handle_api_errors(include_traceback=True)
async def api_multi_tf_squeeze(params: MultiTFSqueezeParams):
    """Multi-TF Squeeze analysis"""
    try:
        high_df, _ = load_data_for_analysis(params.coin, params.high_tf, False, total_candles=1500)
        low_df, _ = load_data_for_analysis(params.coin, params.low_tf, False, total_candles=1500)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    
    result = analyze_multi_tf_squeeze(high_df, low_df, params.model_dump())
    
    return {"success": True, "data": result}


@router.post("/weekly-pattern")
@handle_api_errors(include_traceback=True)
async def api_weekly_pattern(params: WeeklyPatternParams):
    """주간 패턴 분석 (Weekly Pattern & Mean Reversion)"""
    import traceback
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if params.interval != "1d":
            return {"success": False, "error": "주간 패턴 분석은 일봉(1d)만 지원합니다"}
        
        # direction이 없으면 임계값으로 자동 판단
        direction = params.direction
        if not direction:
            # 하락 임계값이 음수면 하락, 상승 임계값이 양수면 상승
            if params.deep_drop_threshold < 0:
                direction = "down"
            elif params.deep_rise_threshold > 0:
                direction = "up"
            else:
                direction = "down"  # 기본값
        
        logger.info(f"Weekly pattern analysis started: coin={params.coin}, direction={direction}, deep_drop={params.deep_drop_threshold}, deep_rise={params.deep_rise_threshold}, rsi={params.rsi_threshold}")
        
        # 항상 API로 2000개 불러오기
        df = _load_data_for_analysis(params.coin, params.interval, use_csv=False, total_candles=2000)
        if df is None or df.empty:
            logger.warning(f"Failed to load data for {params.coin}/{params.interval}")
            return {"success": False, "error": "Failed to load data"}
        
        logger.info(f"Data loaded: {len(df)} rows, columns: {list(df.columns)}")
        
        result = analyze_weekly_pattern(
            df=df,
            coin=params.coin,
            direction=direction,
            deep_drop_threshold=params.deep_drop_threshold,
            deep_rise_threshold=params.deep_rise_threshold,
            rsi_threshold=params.rsi_threshold,
            use_csv=False
        )
        
        logger.info(f"Analysis completed: success={result.get('success', False)}")
        
        # analyze_weekly_pattern이 이미 dict를 반환하므로 그대로 반환
        if isinstance(result, dict):
            return result
        else:
            logger.error(f"Unexpected result type: {type(result)}")
            return {"success": False, "error": f"Unexpected result type: {type(result)}"}
            
    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"Weekly pattern analysis error: {error_msg}", exc_info=True)
        logger.error(f"Traceback: {error_traceback}")
        return {
            "success": False,
            "error": error_msg,
            "error_type": type(e).__name__,
            "traceback": error_traceback
        }


@router.post("/weekly-pattern-manual")
@handle_api_errors(include_traceback=True)
async def api_weekly_pattern_manual(params: WeeklyPatternManualParams):
    """
    주간 패턴 수동 입력 백테스트
    
    사용자가 월요일 시가와 화요일 종가를 직접 입력하여
    해당 주의 수요일 시가 ~ 일요일 종가 수익률을 계산
    """
    # 항상 API로 2000개 불러오기
    df = _load_data_for_analysis(params.coin, "1d", use_csv=False, total_candles=2000)
    if df is None or df.empty:
        return {"success": False, "error": "Failed to load data"}
    
    result = analyze_weekly_pattern_manual(
        df=df,
        coin=params.coin,
        monday_open=params.monday_open,
        tuesday_close=params.tuesday_close,
        wednesday_date=params.wednesday_date,
        use_csv=False
    )
    
    return result


@router.post("/weekly-pattern-backtest")
@handle_api_errors(include_traceback=True)
async def api_weekly_pattern_backtest(params: WeeklyPatternBacktestParams):
    """
    주간 패턴 분석 기반 백테스트
    
    주 초반(월-화) 깊은 하락 후 수요일 시가 진입, 일요일 종가 청산 전략
    """
    if params.interval != "1d":
        return {"success": False, "error": "주간 패턴 분석은 일봉(1d)만 지원합니다"}
    
    # 항상 API로 2000개 불러오기
    df = _load_data_for_analysis(params.coin, params.interval, use_csv=False, total_candles=2000)
    if df is None or df.empty:
        return {"success": False, "error": "Failed to load data"}
    
    result = run_weekly_pattern_backtest(
        df=df,
        coin=params.coin,
        direction=params.direction,
        deep_drop_threshold=params.deep_drop_threshold,
        deep_rise_threshold=params.deep_rise_threshold,
        rsi_threshold=params.rsi_threshold,
        use_csv=False,
        leverage=params.leverage,
        fee_entry_rate=params.fee_entry_rate,
        fee_exit_rate=params.fee_exit_rate,
    )
    
    return result
