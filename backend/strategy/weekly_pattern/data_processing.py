"""
주간 패턴 데이터 처리 모듈

데이터 준비 및 주간 패턴 추출 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple
import logging

from strategy.weekly_pattern.validation import (
    WeeklyPatternError,
    DataValidationError,
    InsufficientDataError,
    validate_dataframe,
    validate_weekly_completeness,
    detect_outliers,
)

logger = logging.getLogger(__name__)

# 상수
REQUIRED_DAYS = [0, 1, 2, 6]  # 월, 화, 수, 일


def load_and_prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터 로드 및 준비 (타임스탬프 변환, 요일/주 정보 추가)
    
    Args:
        df: 원본 DataFrame
    
    Returns:
        준비된 DataFrame
    
    Raises:
        DataValidationError: 데이터 검증 실패 시
        WeeklyPatternError: 데이터 준비 중 오류 발생 시
    """
    try:
        # 데이터 검증
        validate_dataframe(df)
        
        df = df.copy()
        
        # 인덱스를 DatetimeIndex로 변환
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'open_time' in df.columns:
                # open_time이 숫자(타임스탬프)인지 문자열인지 확인
                if df['open_time'].dtype in ['int64', 'float64', 'int32', 'float32']:
                    # 밀리초 또는 초 단위 타임스탬프
                    unit = 'ms' if df['open_time'].max() > 1e10 else 's'
                    df['timestamp'] = pd.to_datetime(df['open_time'], unit=unit, errors='coerce')
                else:
                    # 문자열인 경우
                    df['timestamp'] = pd.to_datetime(df['open_time'], errors='coerce')
                df.set_index('timestamp', inplace=True)
                df.drop('open_time', axis=1, errors='ignore')
            elif 'open_dt' in df.columns:
                # open_dt 컬럼 사용
                df['timestamp'] = pd.to_datetime(df['open_dt'], errors='coerce')
                df.set_index('timestamp', inplace=True)
                df.drop('open_dt', axis=1, errors='ignore')
            else:
                # 인덱스를 직접 변환
                df.index = pd.to_datetime(df.index, errors='coerce')
        
        # NaN 인덱스 제거
        df = df[df.index.notna()]
        
        if df.empty:
            raise DataValidationError("유효한 날짜 인덱스가 없습니다")
        
        # 시간 정렬 (중요: Look-ahead Bias 방지)
        df = df.sort_index()
        
        # 요일 및 주 정보 추가
        df['day_of_week'] = df.index.dayofweek  # 0:Mon, 6:Sun
        df['year'] = df.index.isocalendar().year
        df['week'] = df.index.isocalendar().week
        
        # 이상치 탐지 및 로깅
        outliers = detect_outliers(df)
        for warning in outliers:
            logger.warning(warning)
        
        return df
    except DataValidationError:
        raise
    except Exception as e:
        logger.error(f"데이터 준비 중 오류: {e}", exc_info=True)
        raise WeeklyPatternError(f"데이터 준비 실패: {e}")


def extract_weekly_patterns(df: pd.DataFrame, required_days: List[int] = REQUIRED_DAYS) -> Tuple[pd.DataFrame, List[str]]:
    """
    주간 패턴 추출 (월-화 vs 수-일)
    
    Args:
        df: 기술적 지표가 포함된 DataFrame
        required_days: 필수 요일 리스트 [0=월, 1=화, 2=수, 6=일]
    
    Returns:
        (weekly_df, warnings)
    
    Note: 
        화요일 종가 시점의 RSI를 사용하여 수요일 시가 진입 결정
        이는 실제 거래 가능한 시점의 정보만 사용하므로 Look-ahead Bias 없음
    
    Raises:
        InsufficientDataError: 주간 패턴이 하나도 추출되지 않을 때
    """
    try:
        weekly_records = []
        warnings = []
        skipped_weeks = 0
        
        weeks = df.groupby(['year', 'week'])
        
        for (year, week), group in weeks:
            # 주간 완전성 검증
            is_valid, error_msg = validate_weekly_completeness(group, required_days)
            
            if not is_valid:
                skipped_weeks += 1
                if skipped_weeks <= 5:  # 처음 5개만 경고
                    warnings.append(f"Week {year}-W{week:02d}: {error_msg} (스킵)")
                continue
            
            # 각 요일 데이터 추출 (정확히 1개씩)
            mon = group[group['day_of_week'] == 0].iloc[0]  # 첫 번째만 사용 (중복 시)
            tue = group[group['day_of_week'] == 1].iloc[0]
            wed = group[group['day_of_week'] == 2].iloc[0]
            sun = group[group['day_of_week'] == 6].iloc[0]
            
            # 주 초반 수익률 (월 시가 ~ 화 종가)
            ret_early = (tue['close'] / mon['open']) - 1
            
            # 주 후반 수익률 (수 시가 ~ 일 종가)
            ret_mid_late = (sun['close'] / wed['open']) - 1
            
            weekly_records.append({
                'year': year,
                'week': week,
                'ret_early': ret_early,
                'ret_mid_late': ret_mid_late,
                'rsi_tue': tue.get('rsi', np.nan),  # 화요일 종가 시점 RSI
                'rel_vol_tue': tue.get('rel_vol', np.nan),
                'natr_tue': tue.get('natr', np.nan),
                'date_mon': mon.name,  # 디버깅용
                'date_tue': tue.name,
                'date_wed': wed.name,
                'date_sun': sun.name
            })
        
        if skipped_weeks > 5:
            warnings.append(f"... 외 {skipped_weeks - 5}주 스킵됨")
        
        df_w = pd.DataFrame(weekly_records)
        
        if len(df_w) == 0:
            raise InsufficientDataError("주간 패턴이 하나도 추출되지 않았습니다")
        
        # NaN 제거 (지표 계산이 완료되지 않은 초기 데이터)
        initial_nan_count = len(df_w)
        df_w = df_w.dropna(subset=['rsi_tue', 'rel_vol_tue', 'natr_tue'])
        if len(df_w) < initial_nan_count:
            warnings.append(f"지표 계산 미완료 데이터 {initial_nan_count - len(df_w)}주 제거")
        
        if len(df_w) == 0:
            raise InsufficientDataError("유효한 주간 패턴이 없습니다 (모든 데이터가 NaN)")
        
        return df_w, warnings
    except InsufficientDataError:
        raise
    except Exception as e:
        logger.error(f"주간 패턴 추출 중 오류: {e}", exc_info=True)
        raise WeeklyPatternError(f"주간 패턴 추출 실패: {e}")
