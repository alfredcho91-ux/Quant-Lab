"""
전략 관련 공통 유틸리티 Facade
(기존 코드를 위한 호환성 유지)
"""
import logging
import os

# 로깅 및 디버그 설정
logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv('DEBUG_STREAK_ANALYSIS', 'False').lower() in ('true', '1', 'yes')

# ========== 상수 정의 ==========
DEFAULT_RSI = 50.0
RSI_THRESHOLD_DEFAULT = 60.0
RSI_OVERBOUGHT = 80
MAX_RETRACEMENT_DEFAULT = 50.0
CONFIDENCE_LEVEL = 0.95

# 구간 정의
DISP_BINS = [0, 90, 95, 100, 105, 110, 120, 200]
RSI_BINS = [0, 30, 40, 50, 60, 70, 80, 100]
RETRACEMENT_BINS = [0, 20, 30, 40, 50, 60, 70, 80, 100]
ATR_BINS = [0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0]

# ========== Context & Data Service (Re-exports) ==========
from strategy.context import (
    AnalysisContext,
    VALID_INTERVALS,
    WEEKDAY_NAMES_KO,
    WEEKDAY_NAMES_EN,
)
from utils.data_service import fetch_live_data, load_csv_data
from utils.cache import DataCache

# ========== 모듈별 기능 Re-exports (Facade) ==========
from .json_utils import (
    safe_round,
    sanitize_for_json
)

from .cache_ops import (
    data_cache,
    analysis_cache,
    indicators_cache,
    generate_analysis_cache_key,
    get_cache_stats,
    clear_cache
)

from .data_ops import (
    normalize_datetime_index,
    load_data,
    prepare_dataframe,
    calculate_indicators,
    get_or_calculate_indicators,
    normalize_single_index,
    normalize_indices,
    safe_get_rsi
)

from .pattern_ops import (
    find_complex_pattern,
    analyze_pullback_quality,
    extract_c1_indices,
    extract_c1_dates_from_chart_data,
    calculate_signal_score
)

__all__ = [
    'AnalysisContext', 'VALID_INTERVALS', 'WEEKDAY_NAMES_KO', 'WEEKDAY_NAMES_EN',
    'fetch_live_data', 'load_csv_data', 'DataCache',
    'safe_round', 'sanitize_for_json',
    'data_cache', 'analysis_cache', 'indicators_cache', 'generate_analysis_cache_key', 'get_cache_stats', 'clear_cache',
    'normalize_datetime_index', 'load_data', 'prepare_dataframe', 'calculate_indicators', 'get_or_calculate_indicators',
    'normalize_single_index', 'normalize_indices', 'safe_get_rsi',
    'find_complex_pattern', 'analyze_pullback_quality', 'extract_c1_indices', 'extract_c1_dates_from_chart_data', 'calculate_signal_score',
    'DEFAULT_RSI', 'RSI_THRESHOLD_DEFAULT', 'RSI_OVERBOUGHT', 'MAX_RETRACEMENT_DEFAULT',
    'CONFIDENCE_LEVEL',
    'DISP_BINS', 'RSI_BINS', 'RETRACEMENT_BINS', 'ATR_BINS'
]
