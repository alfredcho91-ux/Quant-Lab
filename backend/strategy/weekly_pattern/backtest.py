"""
주간 패턴 분석 기반 백테스팅 로직

주 초반(월-화) 깊은 하락 후 수요일 시가 진입, 일요일 종가 청산 전략
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add parent path for importing core modules
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

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


def run_weekly_pattern_backtest(
    df: pd.DataFrame,
    coin: str,
    direction: str = "down",
    deep_drop_threshold: float = -0.05,
    deep_rise_threshold: float = 0.05,
    rsi_threshold: float = 40.0,
    use_csv: bool = False,
    rsi_period: int = DEFAULT_RSI_PERIOD,
    atr_period: int = DEFAULT_ATR_PERIOD,
    vol_period: int = DEFAULT_VOL_PERIOD,
    leverage: int = 1,
    fee_entry_rate: float = 0.0005,
    fee_exit_rate: float = 0.0005,
) -> Dict[str, Any]:
    """
    주간 패턴 분석 기반 백테스팅
    
    전략 (하락 케이스):
    - 주 초반(월-화) 하락이 깊은 하락 임계값 이상일 때
    - 화요일 종가 시점 RSI가 임계값 미만일 때
    - 수요일 시가에 진입하여 일요일 종가에 청산
    
    전략 (상승 케이스):
    - 주 초반(월-화) 상승이 깊은 상승 임계값 이상일 때
    - 화요일 종가 시점 RSI가 (100 - 임계값) 초과일 때
    - 수요일 시가에 진입하여 일요일 종가에 청산
    
    Args:
        df: 일봉 DataFrame
        coin: 코인 심볼
        direction: "down" (하락) 또는 "up" (상승)
        deep_drop_threshold: 깊은 하락 임계값 (기본값: -5%)
        deep_rise_threshold: 깊은 상승 임계값 (기본값: +5%)
        rsi_threshold: 과매도/과매수 임계값 (기본값: 40)
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
            rsi_threshold=rsi_threshold,
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
        
        # 3. 주간 패턴 추출
        df_w, warnings = extract_weekly_patterns(df_with_indicators)
        
        # 4. 필터 조건 적용
        if direction == "down":
            # 하락 케이스: 깊은 하락 + 과매도
            early_down = df_w[df_w['ret_early'] < 0]
            deep_drop = early_down[early_down['ret_early'] < config.deep_drop_threshold]
            filtered = deep_drop[deep_drop['rsi_tue'] < config.rsi_threshold]
        else:
            # 상승 케이스: 깊은 상승 + 과매수
            early_up = df_w[df_w['ret_early'] > 0]
            deep_rise = early_up[early_up['ret_early'] > deep_rise_threshold]
            overbought_threshold = 100 - config.rsi_threshold
            filtered = deep_rise[deep_rise['rsi_tue'] > overbought_threshold]
        
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
        trades = []
        for _, row in filtered.iterrows():
            # 수요일 시가와 일요일 종가 찾기
            try:
                wed_date = pd.to_datetime(row['date_wed'])
                sun_date = pd.to_datetime(row['date_sun'])
            except:
                # date_wed, date_sun이 Timestamp인 경우
                wed_date = row['date_wed'] if isinstance(row['date_wed'], pd.Timestamp) else pd.to_datetime(row['date_wed'])
                sun_date = row['date_sun'] if isinstance(row['date_sun'], pd.Timestamp) else pd.to_datetime(row['date_sun'])
            
            # 날짜로 필터링
            wed_data = df_with_indicators[df_with_indicators.index.date == wed_date.date()]
            sun_data = df_with_indicators[df_with_indicators.index.date == sun_date.date()]
            
            if len(wed_data) == 0 or len(sun_data) == 0:
                continue
            
            wed = wed_data.iloc[0]
            sun = sun_data.iloc[0]
            
            entry_price = float(wed['open'])
            exit_price = float(sun['close'])
            
            # 수익률 계산 (레버리지 및 수수료 고려)
            gross_return = (exit_price / entry_price) - 1
            net_return = gross_return * leverage - (fee_entry_rate + fee_exit_rate) * leverage
            
            trades.append({
                "entry_date": str(wed_date.date()) if hasattr(wed_date, 'date') else str(wed_date),
                "exit_date": str(sun_date.date()) if hasattr(sun_date, 'date') else str(sun_date),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_return_pct": float(gross_return * 100),
                "net_return_pct": float(net_return * 100),
                "pnl_pct": float(net_return * 100),
                "is_win": net_return > 0,
                "ret_early": float(row['ret_early'] * 100),
                "rsi_tue": float(row['rsi_tue']),
            })
        
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
                "rsi_threshold": config.rsi_threshold,
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
