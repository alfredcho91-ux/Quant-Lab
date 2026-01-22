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


def extract_weekly_patterns(
    df: pd.DataFrame, 
    required_days: List[int] = REQUIRED_DAYS,
    start_day: int = 0,
    end_day: int = 1
) -> Tuple[pd.DataFrame, List[str]]:
    """
    주간 패턴 추출 (사용자 지정 요일 범위)
    
    Args:
        df: 기술적 지표가 포함된 DataFrame
        required_days: 필수 요일 리스트 [0=월, 1=화, 2=수, 6=일]
        start_day: 분석 시작 요일 (0=월요일, 1=화요일, ..., 6=일요일)
        end_day: 분석 종료 요일 (0=월요일, 1=화요일, ..., 6=일요일)
    
    Returns:
        (weekly_df, warnings)
    
    Note: 
        - start_day부터 end_day까지의 수익률을 계산 (ret_period)
        - end_day 다음 날부터 주말까지의 수익률을 계산 (ret_after)
        - end_day 종가 시점의 RSI를 사용하여 다음 날 시가 진입 결정
        - 이는 실제 거래 가능한 시점의 정보만 사용하므로 Look-ahead Bias 없음
    
    Raises:
        InsufficientDataError: 주간 패턴이 하나도 추출되지 않을 때
    """
    try:
        # 요일 범위 검증
        if not (0 <= start_day <= 6) or not (0 <= end_day <= 6):
            raise ValueError(f"요일은 0(월)~6(일) 사이여야 합니다: start_day={start_day}, end_day={end_day}")
        if start_day > end_day:
            raise ValueError(f"시작 요일은 종료 요일보다 작거나 같아야 합니다: start_day={start_day}, end_day={end_day}")
        
        # end_day 다음 날 계산 (다음 요일부터 주말까지 분석)
        next_day = (end_day + 1) % 7  # 다음 요일 (일요일 다음은 월요일)
        
        weekly_records = []
        warnings = []
        skipped_weeks = 0
        
        weeks = df.groupby(['year', 'week'])
        
        for (year, week), group in weeks:
            # 주간 완전성 검증 (필요한 모든 요일이 있는지 확인)
            needed_days = list(range(start_day, end_day + 1)) + [next_day]
            # 주말(일요일)까지 포함해야 하므로 일요일도 필요
            if 6 not in needed_days:
                needed_days.append(6)
            
            is_valid, error_msg = validate_weekly_completeness(group, needed_days)
            
            if not is_valid:
                skipped_weeks += 1
                if skipped_weeks <= 5:  # 처음 5개만 경고
                    warnings.append(f"Week {year}-W{week:02d}: {error_msg} (스킵)")
                continue
            
            # 시작 요일과 종료 요일 데이터 추출
            start_day_data = group[group['day_of_week'] == start_day].iloc[0]
            end_day_data = group[group['day_of_week'] == end_day].iloc[0]
            
            # 지정된 기간의 수익률 계산 (start_day 시가 ~ end_day 종가)
            ret_period = (end_day_data['close'] / start_day_data['open']) - 1
            
            # end_day 다음 날부터 일요일까지의 수익률 계산
            # next_day가 0(월요일)이면 다음 주로 넘어감 (end_day가 일요일인 경우)
            if next_day == 0:
                # end_day가 일요일이면 다음 주 월요일부터 분석해야 하는데,
                # 같은 주 내에서만 분석하므로 이 경우는 스킵하거나 NaN 처리
                ret_after = np.nan
                rsi_at_end = end_day_data.get('rsi', np.nan)
                rel_vol_at_end = end_day_data.get('rel_vol', np.nan)
                natr_at_end = end_day_data.get('natr', np.nan)
            else:
                # 같은 주 내에서 분석 (next_day부터 일요일까지)
                next_day_data = group[group['day_of_week'] == next_day].iloc[0] if len(group[group['day_of_week'] == next_day]) > 0 else None
                sun_data = group[group['day_of_week'] == 6].iloc[0] if len(group[group['day_of_week'] == 6]) > 0 else None
                
                if next_day_data is not None and sun_data is not None:
                    # next_day 시가 ~ 일요일 종가
                    ret_after = (sun_data['close'] / next_day_data['open']) - 1
                    rsi_at_end = end_day_data.get('rsi', np.nan)  # end_day 종가 시점 RSI
                    rel_vol_at_end = end_day_data.get('rel_vol', np.nan)
                    natr_at_end = end_day_data.get('natr', np.nan)
                else:
                    # next_day 또는 일요일 데이터가 없으면 NaN 처리
                    ret_after = np.nan
                    rsi_at_end = end_day_data.get('rsi', np.nan)
                    rel_vol_at_end = end_day_data.get('rel_vol', np.nan)
                    natr_at_end = end_day_data.get('natr', np.nan)
            
            # 하위 호환성을 위해 ret_early, ret_mid_late도 유지
            # (기존 코드가 ret_early를 사용하는 경우 대비)
            mon = group[group['day_of_week'] == 0].iloc[0] if len(group[group['day_of_week'] == 0]) > 0 else None
            tue = group[group['day_of_week'] == 1].iloc[0] if len(group[group['day_of_week'] == 1]) > 0 else None
            wed = group[group['day_of_week'] == 2].iloc[0] if len(group[group['day_of_week'] == 2]) > 0 else None
            sun = group[group['day_of_week'] == 6].iloc[0] if len(group[group['day_of_week'] == 6]) > 0 else None
            
            ret_early = (tue['close'] / mon['open']) - 1 if mon is not None and tue is not None else np.nan
            ret_mid_late = (sun['close'] / wed['open']) - 1 if wed is not None and sun is not None else np.nan
            
            weekly_records.append({
                'year': year,
                'week': week,
                'ret_period': ret_period,  # 사용자 지정 기간 수익률
                'ret_after': ret_after,  # 다음 기간 수익률
                'ret_early': ret_early,  # 하위 호환성 (월-화)
                'ret_mid_late': ret_mid_late,  # 하위 호환성 (수-일)
                'rsi_at_end': rsi_at_end,  # end_day 종가 시점 RSI
                'rsi_tue': tue.get('rsi', np.nan) if tue is not None else np.nan,  # 하위 호환성
                'rel_vol_at_end': rel_vol_at_end,
                'rel_vol_tue': tue.get('rel_vol', np.nan) if tue is not None else np.nan,  # 하위 호환성
                'natr_at_end': natr_at_end,
                'natr_tue': tue.get('natr', np.nan) if tue is not None else np.nan,  # 하위 호환성
                'date_start': start_day_data.name,  # 디버깅용
                'date_end': end_day_data.name,
                'date_mon': mon.name if mon is not None else None,  # 하위 호환성
                'date_tue': tue.name if tue is not None else None,
                'date_wed': wed.name if wed is not None else None,
                'date_sun': sun.name if sun is not None else None
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
