"""
전략 관련 공통 유틸리티, 상수 및 Context 객체 정의
"""

import pandas as pd
import numpy as np
import sys
import os
import logging
from pathlib import Path
from scipy import stats as scipy_stats
from typing import Dict, Any, Optional, Tuple, List
import hashlib
import json

# 현재 파일의 부모 디렉토리 (backend)를 sys.path에 추가
backend_path = str(Path(__file__).parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 로깅 설정
logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv('DEBUG_STREAK_ANALYSIS', 'False').lower() in ('true', '1', 'yes')

# data_service import (중복 제거)
from data_service import fetch_live_data, load_csv_data

# ========== 상수 정의 ==========
DEFAULT_RSI = 50.0
RSI_THRESHOLD_DEFAULT = 60.0
RSI_OVERBOUGHT = 80
MAX_RETRACEMENT_DEFAULT = 50.0
CONFIDENCE_LEVEL = 0.95
MIN_SAMPLE_SIZE_RELIABLE = 30
MIN_SAMPLE_SIZE_MEDIUM = 10

# 구간 정의
DISP_BINS = [0, 90, 95, 100, 105, 110, 120, 200]
RSI_BINS = [0, 30, 40, 50, 60, 70, 80, 100]
RETRACEMENT_BINS = [0, 20, 30, 40, 50, 60, 70, 80, 100]  # 되돌림 비율 구간 (%)


# ========== JSON 직렬화 안전 헬퍼 ==========
def safe_float(val) -> Optional[float]:
    """
    NaN, Infinity를 None으로 변환하여 JSON 직렬화 안전성 확보
    
    Args:
        val: 변환할 값
        
    Returns:
        안전한 float 값 또는 None
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


def safe_round(val, digits: int = 2) -> Optional[float]:
    """
    안전하게 반올림 (NaN/Infinity 처리 포함)
    
    Args:
        val: 반올림할 값
        digits: 소수점 자릿수
        
    Returns:
        반올림된 값 또는 None
    """
    safe_val = safe_float(val)
    if safe_val is None:
        return None
    return round(safe_val, digits)


def sanitize_for_json(obj):
    """
    JSON 직렬화 전에 NaN/Infinity 값을 None으로 변환
    재귀적으로 딕셔너리와 리스트를 처리
    
    Args:
        obj: 변환할 객체
        
    Returns:
        JSON 안전한 객체
    """
    try:
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [sanitize_for_json(item) for item in obj]
        elif isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        elif isinstance(obj, np.floating):
            f = float(obj)
            if np.isnan(f) or np.isinf(f):
                return None
            return f
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return sanitize_for_json(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            return sanitize_for_json(obj.to_dict() if isinstance(obj, pd.Series) else obj.to_dict('records'))
        elif obj is None:
            return None
        elif isinstance(obj, (str, int, bool)):
            return obj
        else:
            # 알 수 없는 타입은 문자열로 변환 시도
            try:
                return str(obj)
            except:
                return None
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"sanitize_for_json error for type {type(obj)}: {e}")
        return None


# ========== Context Object Pattern ==========
# Context는 strategy.context로 분리 (재사용성 향상)
# 하위 호환성을 위해 re-export
from strategy.context import (
    AnalysisContext,
    VALID_INTERVALS,
    WEEKDAY_NAMES_KO,
    WEEKDAY_NAMES_EN,
)
# AnalysisContext를 re-export (기존 코드 호환성 유지)
__all__ = ['AnalysisContext', 'VALID_INTERVALS', 'WEEKDAY_NAMES_KO', 'WEEKDAY_NAMES_EN']

# ========== 데이터 캐싱 ==========
# DataCache는 utils.cache로 분리 (재사용성 향상)
from utils.cache import DataCache

# 전역 캐시 인스턴스 (TTL 5분)
data_cache = DataCache(ttl_minutes=5)

# 분석 결과 캐시 인스턴스 (TTL 10분 - 분석 결과는 더 오래 캐싱)
analysis_cache = DataCache(ttl_minutes=10)


def normalize_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame 인덱스를 DatetimeIndex로 강제 정규화
    
    처리 우선순위:
    1. 이미 DatetimeIndex면 그대로 반환
    2. open_dt 컬럼이 있으면 인덱스로 설정
    3. open_time 컬럼이 있으면 변환 후 인덱스로 설정
    4. 변환 불가능하면 경고 로그 후 원본 반환
    
    Args:
        df: 원본 DataFrame
    
    Returns:
        DatetimeIndex가 설정된 DataFrame
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # 1. 이미 DatetimeIndex면 그대로 반환
    if isinstance(df.index, pd.DatetimeIndex):
        return df
    
    # 2. open_dt 컬럼이 있으면 인덱스로 설정
    if 'open_dt' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['open_dt']):
            df['open_dt'] = pd.to_datetime(df['open_dt'])
        df = df.set_index('open_dt')
        logger.debug("DatetimeIndex 설정 완료 (open_dt 컬럼 사용)")
        return df
    
    # 3. open_time 컬럼이 있으면 변환 후 인덱스로 설정
    if 'open_time' in df.columns:
        ot = df['open_time']
        # 숫자형 타임스탬프인 경우 (밀리초/마이크로초/나노초 처리)
        if pd.api.types.is_numeric_dtype(ot):
            # 값이 너무 크면 밀리초 이상의 단위로 판단
            max_val = ot.max()
            if max_val > 2_000_000_000_000:  # 나노초 or 마이크로초
                ot = ot // 1000 if max_val > 2_000_000_000_000_000 else ot
            df['open_dt'] = pd.to_datetime(ot, unit='ms')
        else:
            df['open_dt'] = pd.to_datetime(ot)
        df = df.set_index('open_dt')
        logger.debug("DatetimeIndex 설정 완료 (open_time 컬럼 변환)")
        return df
    
    # 4. 변환 불가능
    logger.warning(f"DatetimeIndex 설정 실패: open_dt, open_time 컬럼 없음 (columns: {df.columns.tolist()})")
    return df


def load_data(coin: str, interval: str) -> Tuple[Optional[pd.DataFrame], bool]:
    """
    데이터 로드 (캐시 우선, 없으면 로드)
    
    Returns:
        (df, from_cache) 튜플
        
    Note:
        로드된 데이터는 자동으로 DatetimeIndex로 정규화됨
    """
    cache_key = f"{coin}_{interval}"
    
    # 캐시 확인
    cached = data_cache.get(cache_key)
    if cached is not None:
        return cached, True  # (df, from_cache)
    
    # 캐시 미스 - 데이터 로드
    df, _ = load_csv_data(coin, interval)
    if df is None or df.empty:
        # interval에 따른 최적 봉 개수 설정
        candle_counts = {
            '4h': 3000,
            '1w': 500,
        }
        total_candles = candle_counts.get(interval, 2000)
        df = fetch_live_data(f"{coin}/USDT", interval, total_candles=total_candles)
    
    # 인덱스 강제 정규화 (DatetimeIndex 보장)
    if df is not None and not df.empty:
        df = normalize_datetime_index(df)
        data_cache.set(cache_key, df)
    
    return df, False


def prepare_dataframe(df: pd.DataFrame, direction: str) -> pd.DataFrame:
    """
    DataFrame 준비 (파생 컬럼 계산)
    
    Args:
        df: 원본 DataFrame (DatetimeIndex 보장됨)
        direction: 'green' 또는 'red'
    
    Returns:
        준비된 DataFrame
        
    Note:
        load_data()에서 이미 DatetimeIndex로 정규화되므로
        여기서는 추가 인덱스 변환 불필요
    """
    df = df.copy()
    
    # 안전장치: 혹시 DatetimeIndex가 아니면 정규화
    if not isinstance(df.index, pd.DatetimeIndex):
        df = normalize_datetime_index(df)
    
    df['is_green'] = df['close'] > df['open']
    df['is_red'] = df['close'] < df['open']
    
    is_bullish = direction == "green"
    
    if is_bullish:
        df['target_bit'] = df['is_green']
        df['body_pct'] = (df['close'] - df['open']) / df['open'] * 100
    else:
        df['target_bit'] = df['is_red']
        df['body_pct'] = (df['open'] - df['close']) / df['open'] * 100
    
    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """기술적 지표 계산 (RSI, ATR, Disparity 등)"""
    df = df.copy()
    
    # ATR 계산
    df['prev_close'] = df['close'].shift(1)
    df['tr'] = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['prev_close']).abs(),
        (df['low'] - df['prev_close']).abs()
    ], axis=1).max(axis=1)
    df['atr_14'] = df['tr'].rolling(14).mean()
    df['atr_pct'] = df['atr_14'] / df['close'] * 100
    
    # RSI 계산
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Disparity 계산
    df['vol_change'] = df['volume'].pct_change() * 100
    df['ma20'] = df['close'].rolling(20).mean()
    df['disparity'] = (df['close'] / df['ma20']) * 100
    
    return df


def normalize_single_index(idx: Any, df_index: pd.Index) -> Optional[Tuple[Any, int]]:
    """
    단일 인덱스를 DataFrame 인덱스 타입으로 정규화하고 위치를 찾기
    
    Args:
        idx: 정규화할 인덱스 값
        df_index: DataFrame의 인덱스
    
    Returns:
        (정규화된 인덱스, 위치) 튜플 또는 None (실패 시)
        
    Example:
        normalized_idx, pos = normalize_single_index(idx, df.index)
        if normalized_idx is not None:
            # 정규화 성공, pos는 위치
            pass
    """
    try:
        # 먼저 직접 시도 (이미 올바른 타입인 경우)
        pos = df_index.get_loc(idx)
        return idx, pos
    except (KeyError, TypeError):
        # 타입 변환 후 재시도
        try:
            if isinstance(df_index, pd.DatetimeIndex):
                # DatetimeIndex인 경우 Timestamp로 변환
                if isinstance(idx, pd.Timestamp):
                    idx_normalized = idx
                elif isinstance(idx, str):
                    idx_normalized = pd.to_datetime(idx)
                else:
                    idx_normalized = pd.Timestamp(idx) if not isinstance(idx, pd.Timestamp) else idx
            elif isinstance(idx, str):
                # 문자열인 경우 DatetimeIndex로 변환 시도
                idx_normalized = pd.to_datetime(idx) if isinstance(df_index, pd.DatetimeIndex) else idx
            else:
                idx_normalized = idx
            
            # 정규화된 인덱스로 위치 찾기
            pos = df_index.get_loc(idx_normalized)
            return idx_normalized, pos
        except (KeyError, TypeError, ValueError, pd.errors.ParserError):
            if DEBUG_MODE:
                logger.debug(f"Failed to normalize index: {idx} (type: {type(idx).__name__})")
            return None


def normalize_indices(indices: List[Any], df: pd.DataFrame) -> List[Any]:
    """
    인덱스 타입 통일 (Timestamp로 변환)
    
    Args:
        indices: 원본 인덱스 리스트
        df: DataFrame
    
    Returns:
        정규화된 인덱스 리스트
    """
    normalized = []
    
    for idx in indices:
        try:
            # 정수 인덱스인 경우 그대로 사용 (RangeIndex 등)
            if isinstance(idx, (int, np.integer)):
                if idx in df.index:
                    normalized.append(idx)
            # 문자열인 경우 Timestamp로 변환
            elif isinstance(idx, str):
                idx_converted = pd.to_datetime(idx)
                if idx_converted in df.index:
                    normalized.append(idx_converted)
            # 이미 Timestamp인 경우
            elif isinstance(idx, pd.Timestamp):
                if idx in df.index:
                    normalized.append(idx)
            # 기타 타입은 시도해보되 실패하면 스킵
            else:
                try:
                    idx_converted = pd.to_datetime(idx)
                    if idx_converted in df.index:
                        normalized.append(idx_converted)
                except (ValueError, TypeError, pd.errors.ParserError):
                    pass
        except (ValueError, TypeError, pd.errors.ParserError) as e:
            if DEBUG_MODE:
                logger.warning(f"Failed to normalize index: {idx} (type: {type(idx).__name__}), error: {e}")
            continue
    
    return normalized


def extract_c1_indices(
    df: pd.DataFrame, 
    pattern_indices: pd.Index, 
    filter_green: Optional[bool] = None
) -> List[Any]:
    """
    패턴 완성 인덱스의 다음 봉(C1) 인덱스 추출
    
    Args:
        df: DataFrame
        pattern_indices: 패턴 완성 시점의 인덱스들
        filter_green: True=양봉만, False=음봉만, None=모두
    
    Returns:
        C1 인덱스 리스트
        
    Example:
        # 모든 C1 추출
        c1_indices = extract_c1_indices(df, target_cases.index)
        
        # 양봉인 C1만 추출
        c1_green_indices = extract_c1_indices(df, target_cases.index, filter_green=True)
        
        # 음봉인 C1만 추출
        c1_red_indices = extract_c1_indices(df, target_cases.index, filter_green=False)
    """
    c1_indices = []
    
    for idx in pattern_indices:
        try:
            # 패턴 완성 시점의 위치 찾기
            pos = df.index.get_loc(idx)
            
            # 다음 봉(C1)이 존재하는지 확인
            if pos + 1 < len(df):
                c1_idx = df.index[pos + 1]
                
                # 필터 적용 (선택적)
                if filter_green is not None:
                    c1_is_green = df.loc[c1_idx, 'is_green']
                    if c1_is_green != filter_green:
                        continue
                
                c1_indices.append(c1_idx)
        except (KeyError, IndexError, TypeError):
            # 인덱스 오류 발생 시 스킵
            continue
    
    return c1_indices


def extract_c1_dates_from_chart_data(
    chart_data: List[Dict[str, Any]], 
    filter_green: Optional[bool] = None
) -> List[pd.Timestamp]:
    """
    chart_data에서 C1 날짜 추출 (필터링된 패턴 기반)
    
    Args:
        chart_data: 필터링된 패턴의 차트 데이터 리스트
        filter_green: True=양봉만, False=음봉만, None=모두
    
    Returns:
        C1 날짜 리스트 (pd.Timestamp)
        
    Example:
        # 모든 C1 날짜 추출
        c1_dates = extract_c1_dates_from_chart_data(chart_data)
        
        # 양봉인 C1 날짜만 추출
        c1_green_dates = extract_c1_dates_from_chart_data(chart_data, filter_green=True)
        
        # 음봉인 C1 날짜만 추출
        c1_red_dates = extract_c1_dates_from_chart_data(chart_data, filter_green=False)
    """
    c1_dates = []
    
    for c in chart_data:
        c1_data = c.get('c1')
        if not c1_data:
            continue
        
        # 필터 적용 (선택적): filter_green=True면 양봉(1)만, False면 음봉(-1)만
        if filter_green is not None:
            c1_color = c1_data.get('color')
            expected_color = 1 if filter_green else -1
            if c1_color != expected_color:
                continue
        
        # C1 날짜 추출 및 변환
        c1_date_str = c1_data.get('date')
        if not c1_date_str:
            continue
        
        try:
            c1_date = pd.to_datetime(c1_date_str)
            c1_dates.append(c1_date)
        except (ValueError, TypeError, pd.errors.ParserError) as e:
            if DEBUG_MODE:
                logger.debug(f"Failed to parse C1 date '{c1_date_str}': {e}")
            continue
    
    return c1_dates


def generate_analysis_cache_key(context: 'AnalysisContext') -> str:
    """
    분석 결과 캐시 키 생성
    
    Args:
        context: AnalysisContext 객체
    
    Returns:
        캐시 키 문자열 (coin_interval_n_streak_direction_complex_pattern_hash)
    """
    base_key = f"{context.coin}_{context.interval}_{context.n_streak}_{context.direction}"
    
    # complex_pattern이 있으면 해시값 포함
    if context.use_complex_pattern and context.complex_pattern:
        # 패턴을 JSON 문자열로 변환 후 해시
        pattern_str = json.dumps(context.complex_pattern, sort_keys=True)
        pattern_hash = hashlib.md5(pattern_str.encode()).hexdigest()[:8]  # 8자리 해시
        return f"{base_key}_complex_{pattern_hash}"
    
    # RSI threshold도 키에 포함 (다른 임계값이면 다른 결과)
    rsi_key = f"_rsi{int(context.rsi_threshold)}"
    
    return f"{base_key}{rsi_key}"


def get_cache_stats() -> Dict[str, Any]:
    """캐시 상태 확인 (데이터 캐시 + 분석 결과 캐시)"""
    data_stats = data_cache.stats()
    analysis_stats = analysis_cache.stats()
    
    return {
        "data_cache": data_stats,
        "analysis_cache": analysis_stats,
        "total_cached_items": data_stats["cached_items"] + analysis_stats["cached_items"],
        "total_hit_rate": round(
            (data_stats["hits"] + analysis_stats["hits"]) / 
            max(data_stats["total_requests"] + analysis_stats["total_requests"], 1) * 100,
            2
        )
    }


def clear_cache() -> Dict[str, Any]:
    """캐시 초기화 (데이터 캐시 + 분석 결과 캐시)"""
    data_cache.clear()
    analysis_cache.clear()
    return {"success": True, "message": "All caches cleared"}


# ========== 통계 함수 ==========
# 통계 함수는 statistics.py로 이동 (하위 호환성을 위해 재export)
from strategy.streak.statistics import (
    calculate_intraday_distribution,
    calculate_weekly_distribution,
    wilson_confidence_interval,
    trimmed_stats,
)


def bonferroni_correction(p_value: float, num_tests: int) -> dict:
    """Bonferroni 보정 - 다중비교 시 False Positive 감소"""
    adjusted_alpha = 0.05 / num_tests
    is_significant = bool(p_value < adjusted_alpha) if p_value else False
    
    return {
        "original_p": float(round(p_value, 4)) if p_value else None,
        "adjusted_alpha": float(round(adjusted_alpha, 4)),
        "num_tests": int(num_tests),
        "is_significant_after_correction": bool(is_significant),
        "warning": f"다중비교 보정 적용: {num_tests}개 테스트 중 하나" if num_tests > 1 else None
    }


def calculate_binomial_pvalue(successes: int, total: int, null_prob: float = 0.5) -> float:
    """이항검정 p-value 계산"""
    if total == 0:
        return 1.0
    
    # Two-tailed binomial test
    result = scipy_stats.binomtest(successes, total, null_prob, alternative='two-sided')
    return result.pvalue


def safe_get_rsi(df: pd.DataFrame, idx: Any, default: float = DEFAULT_RSI) -> float:
    """DataFrame에서 RSI 값을 안전하게 가져오기"""
    if 'rsi' not in df.columns:
        return default
    try:
        val = df.loc[idx, 'rsi']
        return float(val) if pd.notna(val) else default
    except (KeyError, IndexError, TypeError):
        return default


# analyze_interval_statistics는 statistics.py로 이동
# 하지만 이 함수는 다른 시그니처를 가지고 있으므로 common.py에 유지
# (data_series, target_series를 받는 버전)
def analyze_interval_statistics(
    data_series: pd.Series,
    target_series: pd.Series,
    bins: List[float],
    confidence: float = CONFIDENCE_LEVEL
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """구간별 통계 분석 공통 함수 (RSI/Disparity 등)"""
    interval_dict = {}
    high_prob_dict = {}
    
    if len(data_series) == 0:
        return interval_dict, high_prob_dict
    
    num_bins = len(bins) - 1
    data_bin = pd.cut(data_series, bins=bins)
    
    analysis = pd.DataFrame({
        'bin': data_bin,
        'target': target_series
    }).groupby('bin', observed=False)['target'].agg(['sum', 'count'])
    
    for interval, row in analysis.iterrows():
        successes = int(row['sum']) if pd.notna(row['sum']) else 0
        count = int(row['count'])
        
        if count >= 1:
            ci_data = wilson_confidence_interval(successes, count, confidence)
            if ci_data is None or ci_data.get("rate") is None:
                continue
            
            pvalue = calculate_binomial_pvalue(successes, count, 0.5)
            correction = bonferroni_correction(pvalue, num_bins)
            
            # 신뢰도 판단
            if count >= MIN_SAMPLE_SIZE_RELIABLE:
                reliability = 'high'
                is_reliable = True
            elif count >= MIN_SAMPLE_SIZE_MEDIUM:
                reliability = 'medium'
                is_reliable = True
            else:
                reliability = 'low'
                is_reliable = False
            
            interval_dict[str(interval)] = {
                **ci_data,
                "sample_size": count,  # 프론트엔드에서 사용하는 필드명
                "is_reliable": is_reliable,
                "reliability": reliability,
                "p_value": float(round(pvalue, 4)),
                "is_significant": bool(pvalue < 0.05),
                "bonferroni": correction
            }
            
            if ci_data["rate"] >= 60 and count >= 3:
                high_prob_dict[str(interval)] = {
                    **ci_data,
                    "sample_size": count,
                    "is_reliable": is_reliable,
                    "reliability": reliability,
                    "p_value": float(round(pvalue, 4)),
                    "bonferroni_significant": bool(correction["is_significant_after_correction"])
                }
    
    return interval_dict, high_prob_dict


# trimmed_stats는 statistics.py로 이동 (하위 호환성을 위해 재export)
# 실제 구현은 statistics.py에 있음


# ========== Complex Pattern 유틸리티 ==========
def find_complex_pattern(df: pd.DataFrame, pattern: list = [1, 1, 1, 1, 1, -1, -1]):
    """복합 패턴 매칭 (예: 5양-2음)"""
    df = df.copy()
    df['color'] = np.where(
        df['close'] > df['open'], 1,  # 양봉
        np.where(df['close'] < df['open'], -1, 0)  # 음봉, Doji는 0
    )
    
    pattern_len = len(pattern)
    if pattern_len == 0:
        return pd.DataFrame()
    
    condition = pd.Series([True] * len(df), index=df.index)
    for i, val in enumerate(pattern):
        condition &= (df['color'].shift(pattern_len - i - 1) == val)
    
    matched = df[condition].copy()
    return matched


def analyze_pullback_quality(
    df: pd.DataFrame, 
    pattern_indices: pd.Index, 
    rise_len: int = 5, 
    drop_len: int = 2
) -> List[Dict[str, Any]]:
    """조정 구간의 품질 분석 (되돌림, 거래량)"""
    results = []
    
    for idx in pattern_indices:
        try:
            pos_idx = df.index.get_loc(idx)
            
            # 범위 체크
            start_pos = pos_idx - (rise_len + drop_len) + 1
            if start_pos < 0:
                continue
            
            # 상승 구간 데이터
            rise_segment = df.iloc[start_pos : pos_idx - drop_len + 1]
            # 조정 구간 데이터 (drop_len개의 음봉, pos_idx까지 포함)
            drop_segment = df.iloc[pos_idx - drop_len + 1 : pos_idx + 1]
            
            if len(rise_segment) == 0 or len(drop_segment) == 0:
                continue
            
            # 되돌림 비율 계산
            # 상승 구간: 첫 양봉의 open ~ 상승 구간 최고 high
            # 조정 구간: 상승 최고 high ~ 마지막 음봉의 close
            rise_start_price = rise_segment['open'].iloc[0]
            rise_high = rise_segment['high'].max()
            drop_end_price = drop_segment['close'].iloc[-1]
            
            rise_range = rise_high - rise_start_price
            drop_range = rise_high - drop_end_price
            
            # 되돌림 비율 = 하락 폭 / 상승 폭 * 100
            # 단, 100% 이상인 경우 (조정 종료가가 상승 시작가 아래)는 100%로 제한
            retracement = (drop_range / rise_range * 100) if rise_range > 0 else 0
            retracement = min(retracement, 100.0)  # 최대 100%로 제한
            
            # 거래량 강도 비율 계산
            if 'volume' not in rise_segment.columns or 'volume' not in drop_segment.columns:
                vol_ratio = 1.0
            else:
                vol_rise = rise_segment['volume'].mean()
                vol_drop = drop_segment['volume'].mean()
                vol_ratio = (vol_drop / vol_rise) if vol_rise > 0 else 1.0
            
            results.append({
                'index': idx,
                'retracement_pct': round(retracement, 2),
                'vol_ratio': round(vol_ratio, 2)
            })
        except (KeyError, IndexError):
            continue
    
    return results


def calculate_signal_score(retracement_pct: float, vol_ratio: float, rsi: float) -> dict:
    """최종 시그널 점수화 (Confidence Score)"""
    score = 0
    reasons = []
    
    # 가격 지지 강도 (되돌림이 작을수록 좋음)
    if retracement_pct < 30:
        score += 40
        reasons.append("강력한 지지 (되돌림 < 30%)")
    elif retracement_pct < 50:
        score += 30
        reasons.append("양호한 지지 (되돌림 < 50%)")
    elif retracement_pct < 70:
        score += 15
        reasons.append("보통 지지 (되돌림 < 70%)")
    else:
        reasons.append("약한 지지 (되돌림 >= 70%)")
    
    # 거래량 건강도 (조정 시 거래량 감소가 좋음)
    if vol_ratio < 0.7:
        score += 30
        reasons.append("건강한 조정 (거래량 감소)")
    elif vol_ratio < 1.0:
        score += 20
        reasons.append("양호한 조정 (거래량 유지)")
    elif vol_ratio < 1.5:
        score += 10
        reasons.append("보통 조정 (거래량 증가)")
    else:
        reasons.append("불안한 조정 (거래량 급증)")
    
    # 추세 강도 (RSI)
    if rsi > 70:
        score += 30
        reasons.append("강한 추세 (RSI > 70)")
    elif rsi > 65:
        score += 25
        reasons.append("양호한 추세 (RSI > 65)")
    elif rsi > 60:
        score += 15
        reasons.append("보통 추세 (RSI > 60)")
    else:
        reasons.append("약한 추세 (RSI <= 60)")
    
    # 신뢰도 판단
    if score >= 80:
        confidence = "high"
    elif score >= 60:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "score": score,
        "confidence": confidence,
        "max_score": 100,
        "reasons": reasons,
        "retracement_pct": retracement_pct,
        "vol_ratio": vol_ratio,
        "rsi": rsi
    }


