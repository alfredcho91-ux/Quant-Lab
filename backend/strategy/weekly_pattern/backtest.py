"""
주간 패턴 분석 기반 백테스팅 로직

주 초반(월-화) 깊은 하락 후 수요일 시가 진입, 일요일 종가 청산 전략
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List

from strategy.weekly_pattern.data_processing import (
    load_and_prepare_data,
    extract_weekly_patterns,
    REQUIRED_DAYS,
)
from strategy.weekly_pattern.indicators import (
    calculate_technical_indicators,
    IndicatorConfig,
)
from strategy.weekly_pattern.config import (
    FilterConfig,
    AnalysisConfig,
    DEFAULT_RSI_PERIOD,
    DEFAULT_ATR_PERIOD,
    DEFAULT_VOL_PERIOD,
)
from strategy.common import calculate_profit_factor
import logging

logger = logging.getLogger(__name__)


def run_weekly_pattern_backtest(
    df: pd.DataFrame,
    coin: str,
    direction: str = "down",
    deep_drop_threshold: float = -0.05,
    deep_rise_threshold: float = 0.05,
    rsi_min: float = 0.0,
    rsi_max: float = 40.0,
    use_csv: bool = False,
    rsi_period: int = DEFAULT_RSI_PERIOD,
    atr_period: int = DEFAULT_ATR_PERIOD,
    vol_period: int = DEFAULT_VOL_PERIOD,
    leverage: int = 1,
    fee_entry_rate: float = 0.0005,
    fee_exit_rate: float = 0.0005,
    start_day: int = 0,
    end_day: int = 1,
) -> Dict[str, Any]:
    """
    주간 패턴 분석 기반 백테스팅
    
    전략 (하락 케이스):
    - 주 초반(월-화) 하락이 깊은 하락 임계값 이상일 때
    - 종료일 종가 시점 RSI가 지정 범위 내일 때
    - 종료일 다음 날 시가에 진입하여 일요일 종가에 청산
    
    전략 (상승 케이스):
    - 주 초반(월-화) 상승이 깊은 상승 임계값 이상일 때
    - 종료일 종가 시점 RSI가 지정 범위 내일 때 (100 - rsi_max ~ 100 - rsi_min)
    - 종료일 다음 날 시가에 진입하여 일요일 종가에 청산
    
    Args:
        df: 일봉 DataFrame
        coin: 코인 심볼
        direction: "down" (하락) 또는 "up" (상승)
        deep_drop_threshold: 깊은 하락 임계값 (기본값: -5%)
        deep_rise_threshold: 깊은 상승 임계값 (기본값: +5%)
        rsi_min: RSI 최소값 (기본값: 0)
        rsi_max: RSI 최대값 (기본값: 40)
        use_csv: CSV 사용 여부
        rsi_period: RSI 기간
        atr_period: ATR 기간
        vol_period: 거래량 이동평균 기간
        leverage: 레버리지
        fee_entry_rate: 진입 수수료율
        fee_exit_rate: 청산 수수료율
    
    Returns:
        백테스팅 결과 딕셔너리
    """
    try:
        # 설정 객체 생성
        config = AnalysisConfig(
            coin=coin,
            deep_drop_threshold=deep_drop_threshold,
            rsi_min=rsi_min,
            rsi_max=rsi_max,
            rsi_period=rsi_period,
            atr_period=atr_period,
            vol_period=vol_period,
            use_csv=use_csv
        )
        config.direction = direction
        config.deep_rise_threshold = deep_rise_threshold
        
        # 1. 데이터 준비
        df_prepared = load_and_prepare_data(df)
        
        # 2. 기술적 지표 계산
        indicator_config = config.indicator_config
        df_with_indicators = calculate_technical_indicators(df_prepared, indicator_config)
        
        # 3. 주간 패턴 추출 (사용자 지정 요일 범위)
        df_w, warnings = extract_weekly_patterns(df_with_indicators, start_day=start_day, end_day=end_day)
        
        # 4. 필터 조건 적용 (사용자 지정 기간 사용)
        ret_col = 'ret_period' if 'ret_period' in df_w.columns else 'ret_early'
        rsi_col = 'rsi_at_end' if 'rsi_at_end' in df_w.columns else 'rsi_tue'
        
        if direction == "down":
            # 하락 케이스: 깊은 하락 + 과매도 (RSI 범위)
            period_down = df_w[df_w[ret_col] < 0]
            deep_drop = period_down[period_down[ret_col] < config.deep_drop_threshold]
            filtered = deep_drop[
                (deep_drop[rsi_col] >= config.rsi_min) & 
                (deep_drop[rsi_col] <= config.rsi_max)
            ]
        else:
            # 상승 케이스: 깊은 상승 + 과매수 (RSI 범위: 상승 케이스는 반대로 계산)
            period_up = df_w[df_w[ret_col] > 0]
            deep_rise = period_up[period_up[ret_col] > deep_rise_threshold]
            overbought_min = 100 - config.rsi_max
            overbought_max = 100 - config.rsi_min
            filtered = deep_rise[
                (deep_rise[rsi_col] >= overbought_min) & 
                (deep_rise[rsi_col] <= overbought_max)
            ]
        
        if len(filtered) == 0:
            return {
                "success": True,
                "coin": coin,
                "total_weeks": len(df_w),
                "filtered_weeks": 0,
                "trades": [],
                "summary": {
                    "n_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "avg_pnl": 0,
                    "max_pnl": 0,
                    "min_pnl": 0,
                },
                "warnings": warnings + ["필터 조건에 맞는 주가 없습니다"],
            }
        
        # 5. 백테스팅 실행
        # end_day 다음 날부터 일요일까지 진입/청산
        next_day = (end_day + 1) % 7  # 다음 요일
        
        trades = []
        for _, row in filtered.iterrows():
            # end_day 다음 날과 일요일 날짜 찾기
            try:
                # date_start, date_end 사용 (사용자 지정 기간)
                end_date = pd.to_datetime(row.get('date_end', row.get('date_tue')))
                # 같은 주의 일요일 찾기
                year = end_date.isocalendar().year
                week = end_date.isocalendar().week
                week_data = df_with_indicators[
                    (df_with_indicators['year'] == year) & 
                    (df_with_indicators['week'] == week)
                ]
                
                # end_day가 일요일이면 next_day는 월요일(다음 주)이므로 스킵
                if next_day == 0:
                    continue
                
                # end_day 다음 날 데이터 찾기
                next_day_data = week_data[week_data['day_of_week'] == next_day]
                sun_data = week_data[week_data['day_of_week'] == 6]  # 일요일
                
                if len(next_day_data) == 0 or len(sun_data) == 0:
                    continue
                
                next_day_row = next_day_data.iloc[0]
                sun_row = sun_data.iloc[0]
                
                entry_price = float(next_day_row['open'])
                exit_price = float(sun_row['close'])
                
                # 수익률 계산 (레버리지 및 수수료 고려)
                gross_return = (exit_price / entry_price) - 1
                net_return = gross_return * leverage - (fee_entry_rate + fee_exit_rate) * leverage
                
                # 하위 호환성을 위해 ret_early, rsi_tue도 포함
                ret_period_val = row.get('ret_period', row.get('ret_early', 0))
                rsi_at_end_val = row.get('rsi_at_end', row.get('rsi_tue', 0))
                
                trades.append({
                    "entry_date": str(next_day_row.name.date()) if hasattr(next_day_row.name, 'date') else str(next_day_row.name),
                    "exit_date": str(sun_row.name.date()) if hasattr(sun_row.name, 'date') else str(sun_row.name),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_return_pct": float(gross_return * 100),
                    "net_return_pct": float(net_return * 100),
                    "pnl_pct": float(net_return * 100),
                    "is_win": net_return > 0,
                    "ret_early": float(ret_period_val * 100),  # 하위 호환성
                    "rsi_tue": float(rsi_at_end_val),  # 하위 호환성
                })
            except Exception as e:
                logger.warning(f"백테스트 트레이드 생성 중 오류: {e}")
                continue
        
        if len(trades) == 0:
            return {
                "success": True,
                "coin": coin,
                "total_weeks": len(df_w),
                "filtered_weeks": len(filtered),
                "trades": [],
                "summary": {
                    "n_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "avg_pnl": 0,
                    "max_pnl": 0,
                    "min_pnl": 0,
                },
                "warnings": warnings + ["거래 데이터를 찾을 수 없습니다"],
            }
        
        # 6. 통계 계산
        trades_df = pd.DataFrame(trades)
        wins = trades_df[trades_df['is_win']]
        
        summary = {
            "n_trades": len(trades),
            "win_rate": (len(wins) / len(trades) * 100) if len(trades) > 0 else 0,
            "total_pnl": float(trades_df['pnl_pct'].sum()),
            "avg_pnl": float(trades_df['pnl_pct'].mean()),
            "max_pnl": float(trades_df['pnl_pct'].max()),
            "min_pnl": float(trades_df['pnl_pct'].min()),
            "profit_factor": calculate_profit_factor(trades_df['pnl_pct']) if len(trades_df) > 0 else None,
        }
        
        return {
            "success": True,
            "coin": coin,
            "total_weeks": len(df_w),
            "filtered_weeks": len(filtered),
            "filters": {
                "deep_drop_threshold": config.deep_drop_threshold,
                "rsi_min": config.rsi_min,
                "rsi_max": config.rsi_max,
            },
            "trades": trades,
            "summary": summary,
            "warnings": warnings,
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
