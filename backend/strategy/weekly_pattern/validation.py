"""
주간 패턴 분석 데이터 검증 모듈
데이터 검증 및 예외 처리 로직 분리
"""

import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

# 상수
REQUIRED_COLUMNS = ['open_time', 'open', 'high', 'low', 'close', 'volume']
REQUIRED_DAYS = [0, 1, 2, 6]  # 월, 화, 수, 일


# ========== 커스텀 예외 클래스 ==========

class WeeklyPatternError(Exception):
    """주간 패턴 분석 관련 기본 예외"""
    pass


class DataValidationError(WeeklyPatternError):
    """데이터 검증 실패 예외"""
    pass


class InsufficientDataError(WeeklyPatternError):
    """데이터 부족 예외"""
    pass


# ========== 데이터 검증 함수 ==========

def validate_dataframe(df: pd.DataFrame) -> None:
    """
    DataFrame 기본 검증
    
    Raises:
        DataValidationError: 필수 컬럼이 없거나 데이터가 비어있는 경우
    """
    if df is None or df.empty:
        raise DataValidationError("DataFrame이 비어있거나 None입니다")
    
    # 필수 컬럼 확인
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f"필수 컬럼이 없습니다: {missing_cols}")
    
    # 인덱스가 DatetimeIndex인지 확인
    if not isinstance(df.index, pd.DatetimeIndex):
        # open_dt 또는 open_time 컬럼이 있는지 확인
        if 'open_dt' not in df.columns and 'open_time' not in df.columns:
            raise DataValidationError("DatetimeIndex가 아니고 날짜 컬럼도 없습니다")


def validate_weekly_completeness(group: pd.DataFrame, required_days: List[int] = REQUIRED_DAYS) -> Tuple[bool, Optional[str]]:
    """
    주간 데이터 완전성 검증 (필수 요일 확인)
    
    Args:
        group: 주별로 그룹화된 DataFrame
        required_days: 필수 요일 리스트 (0=월요일, 1=화요일, 2=수요일, 6=일요일)
    
    Returns:
        (is_valid, error_message) 튜플
    """
    if group is None or group.empty:
        return False, "그룹 데이터가 비어있습니다"
    
    # 요일 추출 (0=월요일, 6=일요일)
    weekdays = group.index.dayofweek.unique()
    
    missing_days = [day for day in required_days if day not in weekdays]
    if missing_days:
        day_names = ['월', '화', '수', '목', '금', '토', '일']
        missing_names = [day_names[day] for day in missing_days]
        return False, f"필수 요일이 없습니다: {', '.join(missing_names)}"
    
    # 중복 요일 확인
    weekday_counts = group.index.dayofweek.value_counts()
    duplicates = weekday_counts[weekday_counts > 1]
    if len(duplicates) > 0:
        day_names = ['월', '화', '수', '목', '금', '토', '일']
        for day, count in duplicates.items():
            day_name = day_names[day]
            logger.warning(f"{day_name}요일 데이터 중복: {count}개 (첫 번째 행만 사용)")
    
    return True, None


def detect_outliers(df: pd.DataFrame) -> List[str]:
    """
    이상치 탐지: 일간 수익률 > ±50%, 거래량 = 0
    
    Returns:
        경고 메시지 리스트
    """
    warnings = []
    
    # 일간 수익률 계산
    if 'close' in df.columns and 'open' in df.columns:
        daily_returns = (df['close'] / df['open']) - 1
        extreme_returns = daily_returns[abs(daily_returns) > 0.5]
        
        if len(extreme_returns) > 0:
            warnings.append(f"극단적 수익률 감지: {len(extreme_returns)}건 (절대값 > 50%)")
            for idx in extreme_returns.head(5).index:
                warnings.append(f"  - {df.index[idx]}: {daily_returns.loc[idx]*100:.2f}%")
    
    # 거래량 = 0 체크
    if 'volume' in df.columns:
        zero_volume = df[df['volume'] == 0]
        if len(zero_volume) > 0:
            warnings.append(f"거래량 0인 데이터: {len(zero_volume)}건")
    
    return warnings
