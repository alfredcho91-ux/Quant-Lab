"""
Streak 분석 통계 함수 모듈
통계 계산 관련 함수들을 분리하여 재사용성과 유지보수성 향상
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats as scipy_stats
import logging

# 순환 참조 방지: safe_float를 직접 정의
def safe_float(val) -> Optional[float]:
    """
    NaN, Infinity를 None으로 변환하여 JSON 직렬화 안전성 확보
    """
    if val is None:
        return None
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None

# data_service import
try:
    from utils.data_service import load_csv_data as _load_csv_data, fetch_live_data as _fetch_live_data
except ImportError:
    # fallback
    import importlib.util
    from pathlib import Path
    backend_path = Path(__file__).parent.parent.parent
    spec = importlib.util.spec_from_file_location("data_service", backend_path / "utils" / "data_service.py")
    data_service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_service)
    _load_csv_data = data_service.load_csv_data
    _fetch_live_data = data_service.fetch_live_data

# normalize_datetime_index는 lazy import (순환 참조 방지)
def _get_normalize_datetime_index():
    """순환 참조 방지를 위한 lazy import"""
    from strategy.streak.common import normalize_datetime_index
    return normalize_datetime_index

logger = logging.getLogger(__name__)

# 상수 (common.py에서 import 가능하지만 순환 참조 방지를 위해 여기서 정의)
# Note: CONFIDENCE_LEVEL은 common.py에도 있지만, 이 모듈은 common.py를 import하지 않음
CONFIDENCE_LEVEL = 0.95
WEEKDAY_NAMES_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# DEBUG_MODE는 streak/common.py에서 가져오지 않고 여기서 정의 (필요시)
DEBUG_MODE = False


def wilson_confidence_interval(
    successes: int, 
    total: int, 
    confidence: float = CONFIDENCE_LEVEL
) -> Dict[str, Any]:
    """
    Wilson Score 신뢰구간 계산 (이항분포)
    
    Args:
        successes: 성공 횟수
        total: 전체 시도 횟수
        confidence: 신뢰수준 (기본값 0.95)
    
    Returns:
        {"rate": float, "ci_lower": float, "ci_upper": float, "ci_width": float}
    """
    if total == 0:
        return {
            "rate": None,
            "ci_lower": None,
            "ci_upper": None,
            "ci_width": None
        }
    
    p = successes / total
    z = scipy_stats.norm.ppf(1 - (1 - confidence) / 2)
    
    denominator = 1 + (z**2 / total)
    center = (p + (z**2 / (2 * total))) / denominator
    margin = (z / denominator) * np.sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))
    
    ci_lower = max(0, center - margin) * 100
    ci_upper = min(1, center + margin) * 100
    
    return {
        "rate": safe_float(p * 100),
        "ci_lower": safe_float(ci_lower),
        "ci_upper": safe_float(ci_upper),
        "ci_width": safe_float(ci_upper - ci_lower)
    }


def trimmed_stats(series: pd.Series) -> Dict[str, Any]:
    """최고/최저 1개씩 제외한 통계"""
    if len(series) < 3:
        return {
            'mean': safe_float(series.mean()) if len(series) > 0 else None,
            'std': safe_float(series.std()) if len(series) > 1 else None,
            'max': safe_float(series.max()) if len(series) > 0 else None,
            'min': safe_float(series.min()) if len(series) > 0 else None,
            'trimmed': False
        }
    
    sorted_vals = series.sort_values()
    trimmed = sorted_vals.iloc[1:-1]  # 최소/최대 1개씩 제외
    
    return {
        'mean': safe_float(trimmed.mean()) if len(trimmed) > 0 else None,
        'std': safe_float(trimmed.std()) if len(trimmed) > 1 else None,
        'max': safe_float(trimmed.max()) if len(trimmed) > 0 else None,
        'min': safe_float(trimmed.min()) if len(trimmed) > 0 else None,
        'original_max': safe_float(series.max()),
        'original_min': safe_float(series.min()),
        'trimmed': True,
        'excluded_count': 2
    }


def analyze_interval_statistics(
    series: pd.Series,
    bins: List[float],
    label_prefix: str = ""
) -> Dict[str, Dict[str, Any]]:
    """
    구간별 통계 분석 (RSI, DISP, Retracement 등)
    
    Args:
        series: 분석할 시리즈
        bins: 구간 경계값 리스트
        label_prefix: 라벨 접두사 (예: "RSI", "DISP")
    
    Returns:
        구간별 통계 딕셔너리
    """
    if len(series) == 0:
        return {}
    
    results = {}
    for i in range(len(bins) - 1):
        lower = bins[i]
        upper = bins[i + 1]
        
        mask = (series >= lower) & (series < upper) if i < len(bins) - 2 else (series >= lower) & (series <= upper)
        subset = series[mask]
        
        if len(subset) > 0:
            label = f"{label_prefix}{lower}-{upper}" if label_prefix else f"{lower}-{upper}"
            results[label] = {
                "count": len(subset),
                "mean": safe_float(subset.mean()),
                "median": safe_float(subset.median()),
                "std": safe_float(subset.std()),
                "min": safe_float(subset.min()),
                "max": safe_float(subset.max())
            }
    
    return results


def calculate_intraday_distribution(
    pattern_result_dates: List[pd.Timestamp], 
    interval: str, 
    coin: str,
    timezone_offset: int = -5
) -> Dict[str, Any]:
    """
    결과 도출일(패턴 매칭 후 반등일)의 4시간봉을 분석하여 시간대별 저점/고점 발생 확률 계산
    UTC 기준으로 계산하며, EST/EDT 시간을 보조 표기로 제공
    
    Args:
        pattern_result_dates: 결과 도출일 리스트 (패턴 다음 날 또는 패턴 매칭 날짜)
        interval: 타임프레임 ('1d', '3d'만 지원)
        coin: 코인 심볼 (4시간봉 데이터 로드용)
        timezone_offset: EST 변환을 위한 시차 (기본값 -5, 뉴욕)
                          ⚠️ Deprecated: pytz를 사용하여 DST 자동 처리하므로 이 파라미터는 무시됩니다.
                          하위 호환성을 위해 유지되지만 실제로는 사용되지 않습니다.
    
    Returns:
        dict with low_window, avg_volatility, hourly_low_probability, hourly_high_probability
        시간대 라벨 형식: "HH:MM-HH:MM UTC (HH:MM-HH:MM EST)"
    """
    import pytz
    
    # 일봉/3일봉만 지원
    if interval not in ['1d', '3d']:
        return {
            "low_window": None,
            "avg_volatility": None,
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": f"시간대별 분석은 일봉(1d) 또는 3일봉(3d)에만 적용됩니다."
        }
    
    if len(pattern_result_dates) == 0:
        return {
            "low_window": None,
            "avg_volatility": None,
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": "분석할 날짜가 없습니다"
        }
    
    try:
        # 4시간봉 데이터 로드
        df_4h, _ = _load_csv_data(coin, '4h')
        if df_4h is None or df_4h.empty:
            df_4h = _fetch_live_data(f"{coin}/USDT", '4h', total_candles=3000)
        
        if df_4h is None or df_4h.empty:
            logger.warning(f"[{interval}] 4시간봉 데이터 로드 실패")
            return {
                "low_window": None,
                "avg_volatility": None,
                "hourly_low_probability": {},
                "hourly_high_probability": {},
                "note": "4시간봉 데이터를 로드할 수 없습니다"
            }
        
        # 인덱스를 datetime으로 변환 및 UTC 타임존 통일
        if not isinstance(df_4h.index, pd.DatetimeIndex):
            # open_dt 컬럼이 있으면 우선 사용 (이미 datetime으로 변환됨)
            if 'open_dt' in df_4h.columns:
                if not pd.api.types.is_datetime64_any_dtype(df_4h['open_dt']):
                    df_4h['open_dt'] = pd.to_datetime(df_4h['open_dt'])
                df_4h.set_index('open_dt', inplace=True)
            elif 'open_time' in df_4h.columns:
                # open_time이 밀리초 타임스탬프인 경우 처리
                if pd.api.types.is_numeric_dtype(df_4h['open_time']):
                    df_4h['open_time'] = pd.to_datetime(df_4h['open_time'], unit='ms')
                else:
                    df_4h['open_time'] = pd.to_datetime(df_4h['open_time'])
                df_4h.set_index('open_time', inplace=True)
            else:
                df_4h.index = pd.to_datetime(df_4h.index)
        
        # ✅ 개선: 4시간봉 인덱스를 UTC로 통일 (타임존 일관성 보장)
        if df_4h.index.tzinfo is None:
            df_4h.index = df_4h.index.tz_localize('UTC')
        elif str(df_4h.index.tzinfo) != 'UTC':
            df_4h.index = df_4h.index.tz_convert('UTC')
        
        # 날짜 중복 제거 및 정규화 (UTC로 통일)
        unique_dates = []
        seen_dates = set()
        for date in pattern_result_dates:
            if isinstance(date, str):
                date_ts = pd.to_datetime(date)
            elif isinstance(date, pd.Timestamp):
                date_ts = date
            else:
                try:
                    date_ts = pd.to_datetime(date)
                except:
                    continue
            
            # ✅ 개선: UTC로 통일 후 날짜만 추출 (타임존 일관성 보장)
            if date_ts.tzinfo is None:
                date_ts = date_ts.tz_localize('UTC')
            elif str(date_ts.tzinfo) != 'UTC':
                date_ts = date_ts.tz_convert('UTC')
            
            date_only = date_ts.normalize()  # 날짜만 추출 (시간 제거)
            if date_only not in seen_dates:
                unique_dates.append(date_only)
                seen_dates.add(date_only)
        
        if len(unique_dates) == 0:
            return {
                "low_window": None,
                "avg_volatility": None,
                "hourly_low_probability": {},
                "hourly_high_probability": {},
                "note": "유효한 날짜가 없습니다"
            }
        
        # 시간대별 저점/고점 발생 횟수 카운트 (UTC 기준, EST 보조 표기)
        # UTC 시간 구간: 00:00-04:00, 04:00-08:00, 08:00-12:00, 12:00-16:00, 16:00-20:00, 20:00-24:00
        low_hour_counts = {i: 0 for i in range(6)}  # 0~5: UTC 시간 4시간 구간 인덱스
        high_hour_counts = {i: 0 for i in range(6)}
        volatility_sum = 0.0
        volatility_count = 0
        valid_date_count = 0  # 최저가와 최고가가 다른 4시간봉에 있는 날짜 수
        
        # UTC를 EST/EDT로 변환하는 함수 (pytz 사용, DST 자동 처리) - 보조 표기용
        ny_tz = pytz.timezone('America/New_York')
        
        def utc_to_est_hour(utc_timestamp):
            """
            UTC 타임스탬프를 EST/EDT 시간(시간)으로 변환 (DST 자동 처리)
            
            Args:
                utc_timestamp: UTC 타임스탬프 (pd.Timestamp 또는 datetime)
            
            Returns:
                EST/EDT 시간 (0-23)
            """
            # UTC 타임스탬프를 pandas Timestamp로 변환
            if isinstance(utc_timestamp, pd.Timestamp):
                utc_dt = utc_timestamp
            else:
                utc_dt = pd.to_datetime(utc_timestamp)
            
            # UTC로 명시적으로 localize (naive datetime인 경우)
            if utc_dt.tzinfo is None:
                # naive datetime을 UTC로 localize
                utc_dt = utc_dt.tz_localize('UTC')
            elif str(utc_dt.tzinfo) != 'UTC':
                # 이미 timezone이 있지만 UTC가 아닌 경우 UTC로 변환
                utc_dt = utc_dt.tz_convert('UTC')
            
            # New York 시간대로 변환 (DST 자동 처리)
            ny_dt = utc_dt.tz_convert(ny_tz)
            
            # 시간 추출
            est_hour = ny_dt.hour
            
            return est_hour
        
        def utc_hour_to_interval_index(utc_hour):
            """UTC 시간(0-23)을 4시간 구간 인덱스(0-5)로 변환"""
            # 0~3: 0, 4~7: 1, 8~11: 2, 12~15: 3, 16~19: 4, 20~23: 5
            return utc_hour // 4
        
        def get_utc_est_label(utc_interval_idx):
            """
            UTC 구간 인덱스에 대한 라벨 생성 (UTC 시간 + EST 보조 표기)
            
            Args:
                utc_interval_idx: UTC 구간 인덱스 (0-5)
            
            Returns:
                "HH:MM-HH:MM UTC (HH:MM-HH:MM EST)" 형식의 라벨
            """
            # UTC 구간 계산
            utc_start = utc_interval_idx * 4
            utc_end = (utc_interval_idx + 1) * 4
            
            # UTC 구간의 시작과 끝 시간을 EST로 변환 (대표값으로 사용)
            # 오늘 날짜를 사용하여 EST 변환 (DST 고려)
            today = pd.Timestamp.now().normalize()
            utc_start_ts = today + pd.Timedelta(hours=utc_start)
            utc_end_ts = today + pd.Timedelta(hours=utc_end)
            
            # UTC를 EST로 변환
            if utc_start_ts.tzinfo is None:
                utc_start_ts = utc_start_ts.tz_localize('UTC')
            if utc_end_ts.tzinfo is None:
                utc_end_ts = utc_end_ts.tz_localize('UTC')
            
            est_start_ts = utc_start_ts.tz_convert(ny_tz)
            est_end_ts = utc_end_ts.tz_convert(ny_tz)
            est_start = est_start_ts.hour
            est_end = est_end_ts.hour
            
            # EST가 다음날로 넘어가는 경우 처리
            if est_end < est_start:
                # 다음날로 넘어가는 경우: "23:00-03:00 EST" 형식으로 표기
                est_end_str = f"{est_end:02d}:00"
            else:
                est_end_str = f"{est_end:02d}:00"
            
            return f"{utc_start:02d}:00-{utc_end:02d}:00 UTC ({est_start:02d}:00-{est_end_str} EST)"
        
        for date in unique_dates:
            try:
                # 해당 날짜의 4시간봉 가져오기 (UTC 기준 날짜 범위)
                date_start = date
                date_end = date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                
                # 날짜 범위로 필터링 (UTC 기준)
                date_mask = (df_4h.index >= date_start) & (df_4h.index <= date_end)
                day_4h_candles = df_4h[date_mask].copy()
                
                if len(day_4h_candles) > 0:
                    # 하루 전체 최저가/최고가 찾기 (다른 시간대에 발생하는 경우가 일반적)
                    day_min_low = day_4h_candles['low'].min()
                    day_max_high = day_4h_candles['high'].max()
                    
                    # 최저가가 발생한 4시간봉 찾기 (같은 값이 여러 봉에 있을 경우 첫 번째)
                    low_candles = day_4h_candles[day_4h_candles['low'] == day_min_low]
                    high_candles = day_4h_candles[day_4h_candles['high'] == day_max_high]
                    
                    # 최저가와 최고가가 존재하는 경우만 처리
                    if len(low_candles) > 0 and len(high_candles) > 0:
                        low_idx_original = low_candles.index[0]
                        high_idx_original = high_candles.index[0]
                        
                        # UTC 시간을 직접 사용하여 시간대 구간 인덱스 계산
                        low_utc_hour = low_idx_original.hour
                        high_utc_hour = high_idx_original.hour
                        low_interval_idx = utc_hour_to_interval_index(low_utc_hour)
                        high_interval_idx = utc_hour_to_interval_index(high_utc_hour)
                        
                        # 저점과 고점이 다른 UTC 구간에 있는 경우만 valid_date_count 증가
                        # (같은 구간에 있으면 확률 계산이 왜곡됨)
                        if low_interval_idx != high_interval_idx:
                            valid_date_count += 1
                            
                            # 저점과 고점 시간대별 카운트 (UTC 기준)
                            low_hour_counts[low_interval_idx] += 1
                            high_hour_counts[high_interval_idx] += 1
                    
                    # ✅ 개선: 변동성 계산 안전성 강화 (모든 봉의 open > 0 확인)
                    valid_mask = day_4h_candles['open'] > 0
                    if valid_mask.sum() > 0:
                        candle_volatilities = (
                            (day_4h_candles.loc[valid_mask, 'high'] - day_4h_candles.loc[valid_mask, 'low']) / 
                            day_4h_candles.loc[valid_mask, 'open']
                        ) * 100
                        day_volatility = float(candle_volatilities.mean())
                    else:
                        day_volatility = 0.0
                    
                    volatility_sum += day_volatility
                    volatility_count += 1
            except Exception as e:
                logger.warning(f"날짜 {date.date()} 처리 중 에러: {e}")
                continue
        
        # 확률 계산 (유효한 날짜 수로 나누기) - UTC 기준 24시간 모두 표시
        # 최저가와 최고가가 다른 4시간봉에 있는 날짜만 유효한 데이터로 간주
        total_dates = len(unique_dates)
        hourly_low_prob = {}
        hourly_high_prob = {}
        
        # UTC 기준 4시간 구간 라벨 생성 (EST 보조 표기 포함)
        # 0: 00:00-04:00 UTC, 1: 04:00-08:00 UTC, 2: 08:00-12:00 UTC, 
        # 3: 12:00-16:00 UTC, 4: 16:00-20:00 UTC, 5: 20:00-24:00 UTC
        hour_labels = [get_utc_est_label(i) for i in range(6)]
        
        # 유효한 날짜 수를 분모로 사용 (최저가와 최고가가 다른 4시간봉에 있는 경우)
        valid_total = max(valid_date_count, 1)  # 0으로 나누기 방지
        
        if valid_date_count > 0:
            # 저점 확률 (모든 6개 구간 표시, 0%도 포함)
            for idx in range(6):
                count = low_hour_counts.get(idx, 0)
                prob = (count / valid_date_count) * 100
                safe_prob = safe_float(prob)
                hourly_low_prob[hour_labels[idx]] = round(safe_prob, 2) if safe_prob is not None else 0.0
            
            # 고점 확률 (모든 6개 구간 표시, 0%도 포함)
            for idx in range(6):
                count = high_hour_counts.get(idx, 0)
                prob = (count / valid_date_count) * 100
                safe_prob = safe_float(prob)
                hourly_high_prob[hour_labels[idx]] = round(safe_prob, 2) if safe_prob is not None else 0.0
            
            # ✅ 개선: 확률 합계 검증 (반올림 오차 감지)
            low_prob_sum = sum(hourly_low_prob.values())
            high_prob_sum = sum(hourly_high_prob.values())
            # 오차 확인 (반올림 오차 ±1% 허용)
            if abs(low_prob_sum - 100.0) > 1.0:
                logger.warning(f"[{interval}] 저점 확률 합계 이상: {low_prob_sum:.2f}% (기대: 100%)")
            if abs(high_prob_sum - 100.0) > 1.0:
                logger.warning(f"[{interval}] 고점 확률 합계 이상: {high_prob_sum:.2f}% (기대: 100%)")
            
            # 평균 변동성
            avg_volatility = safe_float(volatility_sum / volatility_count) if volatility_count > 0 else None
            if avg_volatility is not None:
                avg_volatility = round(avg_volatility, 2)
            
            # 저점 윈도우 찾기 (가장 많이 발생한 시간대 - UTC 기준)
            max_low_count = max(low_hour_counts.values()) if low_hour_counts.values() else 0
            if max_low_count > 0:
                max_low_idx = max(low_hour_counts.items(), key=lambda x: x[1])[0]
                low_window_str = hour_labels[max_low_idx]
            else:
                low_window_str = None
            
            logger.info(
                f"[{interval}] 시간대별 확률 계산 완료 (UTC 기준): total_dates={total_dates}, "
                f"valid_dates={valid_date_count}, low_sum={low_prob_sum:.2f}%, high_sum={high_prob_sum:.2f}%"
            )
            
            note_str = f"분석 대상 날짜: {total_dates}개 (유효: {valid_date_count}개) - UTC 기준, EST 보조 표기"
            if valid_date_count < total_dates:
                note_str += f" - 같은 4시간봉에 최저가/최고가가 발생한 {total_dates - valid_date_count}개 날짜 제외"
            
            return {
                "low_window": low_window_str,
                "avg_volatility": f"{avg_volatility}%" if avg_volatility else None,
                "hourly_low_probability": hourly_low_prob,
                "hourly_high_probability": hourly_high_prob,
                "note": note_str
            }
        else:
            logger.warning(f"[{interval}] 시간대별 확률 계산 실패: total_dates={total_dates}")
            return {
                "low_window": None,
                "avg_volatility": None,
                "hourly_low_probability": {},
                "hourly_high_probability": {},
                "note": "분석할 날짜가 없습니다"
            }
            
    except Exception as e:
        logger.error(f"시간대별 확률 계산 에러: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "low_window": None,
            "avg_volatility": None,
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": f"에러 발생: {str(e)}"
        }


def calculate_weekly_distribution(
    df: pd.DataFrame,
    interval: str,
    timezone_offset: int = -5
) -> Dict[str, Any]:
    """
    주봉 데이터에서 요일별 저점/고점 발생 확률 계산
    
    Args:
        df: 일봉 DataFrame (주봉 분석 시 일봉 데이터 사용)
        interval: 타임프레임
        timezone_offset: 타임존 오프셋 (EST 기본값)
        
    Returns:
        {
            "daily_low_probability": {"Monday": 15.2, "Tuesday": 20.1, ...},
            "daily_high_probability": {"Monday": 18.5, "Tuesday": 22.3, ...},
            "note": "분석 정보"
        }
    """
    try:
        if df is None or df.empty:
            return {
                "daily_low_probability": {},
                "daily_high_probability": {},
                "note": "데이터 없음"
            }
        
        # 인덱스를 datetime으로 확보
        normalize_datetime_index = _get_normalize_datetime_index()
        if not isinstance(df.index, pd.DatetimeIndex):
            df = normalize_datetime_index(df)
        
        if not isinstance(df.index, pd.DatetimeIndex):
            return {
                "daily_low_probability": {},
                "daily_high_probability": {},
                "note": "DatetimeIndex 변환 실패"
            }
        
        # 주별로 그룹화하여 분석
        df_copy = df.copy()
        df_copy['week'] = df_copy.index.to_period('W')
        df_copy['weekday'] = df_copy.index.dayofweek  # 0=월요일, 6=일요일
        
        # 각 주에서 저점/고점이 발생한 요일 찾기
        low_day_counts = {i: 0 for i in range(7)}  # 월~일
        high_day_counts = {i: 0 for i in range(7)}
        valid_week_count = 0
        
        for week, week_df in df_copy.groupby('week'):
            if len(week_df) < 3:  # 최소 3일 이상의 데이터가 있는 주만 분석
                continue
            
            # 해당 주의 저점/고점 찾기
            low_idx = week_df['low'].idxmin()
            high_idx = week_df['high'].idxmax()
            
            if pd.isna(low_idx) or pd.isna(high_idx):
                continue
            
            low_weekday = week_df.loc[low_idx, 'weekday'] if low_idx in week_df.index else None
            high_weekday = week_df.loc[high_idx, 'weekday'] if high_idx in week_df.index else None
            
            if low_weekday is not None and high_weekday is not None:
                low_day_counts[low_weekday] += 1
                high_day_counts[high_weekday] += 1
                valid_week_count += 1
        
        # 확률 계산
        daily_low_prob = {}
        daily_high_prob = {}
        
        if valid_week_count > 0:
            for i in range(7):
                day_name = WEEKDAY_NAMES_EN[i]
                low_prob = safe_float(low_day_counts[i] / valid_week_count * 100)
                high_prob = safe_float(high_day_counts[i] / valid_week_count * 100)
                daily_low_prob[day_name] = round(low_prob, 1) if low_prob is not None else 0.0
                daily_high_prob[day_name] = round(high_prob, 1) if high_prob is not None else 0.0
            
            logger.info(f"[주봉] 요일별 확률 계산 완료: valid_weeks={valid_week_count}")
            
            return {
                "daily_low_probability": daily_low_prob,
                "daily_high_probability": daily_high_prob,
                "note": f"분석 대상 주: {valid_week_count}주"
            }
        else:
            return {
                "daily_low_probability": {},
                "daily_high_probability": {},
                "note": "분석할 주간 데이터 없음"
            }
            
    except Exception as e:
        logger.error(f"요일별 확률 계산 에러: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "daily_low_probability": {},
            "daily_high_probability": {},
            "note": f"에러 발생: {str(e)}"
        }
