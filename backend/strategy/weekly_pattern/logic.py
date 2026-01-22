"""
주간 패턴 분석 로직 (Weekly Pattern & Mean Reversion Analysis)

개선사항:
- Priority 1: 통계적 신뢰성 (t-test, 신뢰구간, 샘플 크기 검증, 리스크 지표)
- Priority 2: 데이터 품질 및 견고성 (데이터 검증, Look-ahead Bias 방지)
- Priority 3: 코드 품질 (함수 분리, 파라미터화, 에러 처리 강화)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
from scipy import stats as scipy_stats

from utils.data_loader import load_data_for_analysis
from utils.data_service import fetch_live_data, load_csv_data
from strategy.streak.common import sanitize_for_json, safe_float
from strategy.common import (
    calculate_sharpe_ratio_unified,
    calculate_max_drawdown_unified,
    calculate_t_test_unified,
    calculate_profit_factor,
    calculate_max_consecutive_loss,
    calculate_returns_confidence_interval,
)

logger = logging.getLogger(__name__)

# ========== 상수 정의 ==========
# 상수는 config.py로 이동 (하위 호환성을 위해 re-export)
REQUIRED_COLUMNS = ['open_time', 'open', 'high', 'low', 'close', 'volume']

# 예외 클래스와 검증 함수는 validation.py로 이동
from strategy.weekly_pattern.validation import (
    WeeklyPatternError,
    DataValidationError,
    InsufficientDataError,
    validate_dataframe,
    validate_weekly_completeness,
    detect_outliers,
)

# IndicatorConfig는 indicators.py로 이동
from strategy.weekly_pattern.indicators import (
    IndicatorConfig,
    compute_rsi,
    compute_natr,
    calculate_technical_indicators,
)

# 설정 클래스는 config.py로 이동
from strategy.weekly_pattern.config import (
    FilterConfig,
    AnalysisConfig,
    DEFAULT_DEEP_DROP_THRESHOLD,
    DEFAULT_RSI_MIN,
    DEFAULT_RSI_MAX,
    DEFAULT_RSI_PERIOD,
    DEFAULT_ATR_PERIOD,
    DEFAULT_VOL_PERIOD,
)

# 데이터 처리 함수는 data_processing.py로 이동
from strategy.weekly_pattern.data_processing import (
    load_and_prepare_data,
    extract_weekly_patterns,
    REQUIRED_DAYS,  # 하위 호환성을 위해 re-export
)

# 통계 계산 함수는 statistics.py로 이동
from strategy.weekly_pattern.statistics import (
    calculate_stats_for_subset,
    apply_filters_and_calculate_stats,
)

# ========== 데이터 검증 함수 ==========
# 검증 함수는 validation.py로 이동 (import로 사용)

def analyze_weekly_pattern(
    df: pd.DataFrame,
    coin: str,
    direction: str = "down",
    deep_drop_threshold: float = DEFAULT_DEEP_DROP_THRESHOLD,
    deep_rise_threshold: float = 0.05,
    rsi_min: float = DEFAULT_RSI_MIN,
    rsi_max: float = DEFAULT_RSI_MAX,
    use_csv: bool = False,
    rsi_period: int = DEFAULT_RSI_PERIOD,
    atr_period: int = DEFAULT_ATR_PERIOD,
    vol_period: int = DEFAULT_VOL_PERIOD,
    start_day: int = 0,
    end_day: int = 1
) -> Dict[str, Any]:
    """
    주간 패턴 분석 (월-화 vs 수-일) - 개선 버전
    
    Args:
        df: 일봉 DataFrame
        coin: 코인 심볼
        deep_drop_threshold: 깊은 하락 임계값 (기본값: -5%)
        rsi_threshold: 과매도 임계값 (기본값: 40)
        use_csv: CSV 사용 여부 (현재는 사용하지 않지만 호환성 유지)
        rsi_period: RSI 기간 (기본값: 14)
        atr_period: ATR 기간 (기본값: 14)
        vol_period: 거래량 이동평균 기간 (기본값: 20)
    
    Returns:
        분석 결과 딕셔너리
        
    Raises:
        DataValidationError: 데이터 검증 실패 시
        InsufficientDataError: 데이터 부족 시
        WeeklyPatternError: 기타 분석 오류 시
    """
    # 설정 객체 생성 및 검증
    try:
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
        # direction과 deep_rise_threshold를 동적으로 추가
        config.direction = direction
        config.deep_rise_threshold = deep_rise_threshold
    except ValueError as e:
        logger.error(f"설정 검증 실패: {e}")
        return {
            "success": False,
            "error": f"Invalid configuration: {str(e)}"
        }
    
    try:
        # 1. 데이터 준비 및 검증
        df_prepared = load_and_prepare_data(df)
        
        # 2. 기술적 지표 계산
        indicator_config = config.indicator_config
        df_with_indicators = calculate_technical_indicators(df_prepared, indicator_config)
        
        # 3. 주간 패턴 추출 (사용자 지정 요일 범위)
        df_w, warnings = extract_weekly_patterns(df_with_indicators, start_day=start_day, end_day=end_day)
        
        # 4. 필터별 성과 분석
        filter_config = config.filter_config
        results = apply_filters_and_calculate_stats(df_w, filter_config)
        
        # 5. 결과 구성
        try:
            filters_dict = {
                "deep_drop_threshold": config.deep_drop_threshold,
                "rsi_min": config.rsi_min,
                "rsi_max": config.rsi_max,
                "rsi_period": config.rsi_period,
                "atr_period": config.atr_period,
                "vol_period": config.vol_period
            }
            # 상승 케이스인 경우 deep_rise_threshold 추가
            if config.direction == "up":
                filters_dict["deep_rise_threshold"] = config.deep_rise_threshold
            
            result = {
                "success": True,
                "coin": config.coin,
                "total_weeks": len(df_w),
                "warnings": warnings,
                "filters": filters_dict,
                "results": results
            }
            
            # JSON 직렬화 안전성 확보
            sanitized_result = sanitize_for_json(result)
            return sanitized_result
        except Exception as e:
            logger.error(f"결과 구성 중 오류: {e}", exc_info=True)
            raise WeeklyPatternError(f"결과 구성 실패: {e}")
        
    except (DataValidationError, InsufficientDataError) as e:
        logger.warning(f"분석 실패 (예상 가능한 오류): {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    except WeeklyPatternError as e:
        logger.error(f"분석 중 오류 발생: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
        import traceback
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc() if logger.level <= logging.DEBUG else None
        }

def analyze_weekly_pattern_manual(
    df: pd.DataFrame,
    coin: str,
    monday_open: float,
    tuesday_close: float,
    wednesday_date: str,
    use_csv: bool = False
) -> Dict[str, Any]:
    """
    주간 패턴 수동 입력 백테스트
    
    사용자가 월요일 시가와 화요일 종가를 직접 입력하여
    해당 주의 수요일 시가 ~ 일요일 종가 수익률을 계산
    
    Args:
        df: 일봉 DataFrame
        coin: 코인 심볼
        monday_open: 월요일 시가 (사용자 입력)
        tuesday_close: 화요일 종가 (사용자 입력)
        wednesday_date: 수요일 날짜 (YYYY-MM-DD 형식)
        use_csv: CSV 사용 여부
    
    Returns:
        백테스트 결과 딕셔너리
    """
    try:
        # 데이터 준비
        df_prepared = load_and_prepare_data(df)
        
        # 수요일 날짜 파싱
        try:
            wed_date = pd.to_datetime(wednesday_date)
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid date format: {wednesday_date}. Use YYYY-MM-DD format."
            }
        
        # 수요일 데이터 찾기
        wed_data = df_prepared[df_prepared.index.date == wed_date.date()]
        
        if len(wed_data) == 0:
            return {
                "success": False,
                "error": f"수요일 데이터를 찾을 수 없습니다: {wednesday_date}"
            }
        
        wed = wed_data.iloc[0]
        
        # 해당 주의 일요일 찾기 (수요일과 같은 주)
        year = wed_date.isocalendar().year
        week = wed_date.isocalendar().week
        
        week_data = df_prepared[
            (df_prepared['year'] == year) & 
            (df_prepared['week'] == week)
        ]
        
        sun_data = week_data[week_data['day_of_week'] == 6]  # 일요일
        
        if len(sun_data) == 0:
            return {
                "success": False,
                "error": f"일요일 데이터를 찾을 수 없습니다 (주: {year}-W{week:02d})"
            }
        
        sun = sun_data.iloc[0]
        
        # 주 초반 수익률 계산 (사용자 입력값 사용)
        ret_early = (tuesday_close / monday_open) - 1
        
        # 주 후반 수익률 계산 (수요일 시가 ~ 일요일 종가)
        wed_open = wed['open']
        sun_close = sun['close']
        ret_mid_late = (sun_close / wed_open) - 1
        
        # 결과 구성
        result = {
            "success": True,
            "coin": coin,
            "input": {
                "monday_open": monday_open,
                "tuesday_close": tuesday_close,
                "wednesday_date": str(wed_date.date()),
                "ret_early": float(ret_early * 100)  # 백분율
            },
            "output": {
                "wednesday_open": float(wed_open),
                "sunday_close": float(sun_close),
                "ret_mid_late": float(ret_mid_late * 100),  # 백분율
                "wednesday_date": str(wed.name.date()) if hasattr(wed.name, 'date') else str(wed_date.date()),
                "sunday_date": str(sun.name.date()) if hasattr(sun.name, 'date') else None
            },
            "backtest": {
                "entry_price": float(wed_open),
                "exit_price": float(sun_close),
                "return_pct": float(ret_mid_late * 100),
                "is_profitable": ret_mid_late > 0,
                "entry_date": str(wed.name.date()) if hasattr(wed.name, 'date') else str(wed_date.date()),
                "exit_date": str(sun.name.date()) if hasattr(sun.name, 'date') else None
            }
        }
        
        return sanitize_for_json(result)
        
    except (DataValidationError, InsufficientDataError) as e:
        logger.warning(f"수동 백테스트 실패 (예상 가능한 오류): {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    except WeeklyPatternError as e:
        logger.error(f"수동 백테스트 중 오류 발생: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
        import traceback
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc() if logger.level <= logging.DEBUG else None
        }
