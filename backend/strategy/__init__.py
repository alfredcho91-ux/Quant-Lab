"""전략 패키지 - 모든 전략 모듈의 진입점"""

# Streak 분석 (연속봉 분석)
from strategy.streak import (
    analyze_streak_pattern,
    get_cache_stats,
    clear_cache
)

# BB Mid Touch (볼린저 밴드 중단 터치)
from strategy.bb_mid import (
    add_bb_indicators,
    analyze_bb_mid_touch,
    collect_event_returns,
    quartile_reach_stats,
)

# Combo Filter (통합 필터)
from strategy.combo_filter import (
    analyze_combo_filter,
    add_combo_indicators,
    build_ma_filter,
    build_bb_filter,
    build_pattern_filter,
    run_tp_backtest,
)

# Multi-TF Squeeze (멀티 타임프레임 스퀴즈)
from strategy.squeeze import (
    analyze_multi_tf_squeeze,
    add_squeeze_indicators,
    find_squeeze_breakouts,
)

# Hybrid Strategy (하이브리드 전략)
from strategy.hybrid import (
    analyze_hybrid_strategy,
    run_hybrid_backtest,
)

# Hybrid Strategy (하이브리드 전략)
from strategy.hybrid import (
    analyze_hybrid_strategy,
    run_hybrid_backtest,
)

__all__ = [
    # Streak
    'analyze_streak_pattern',
    'get_cache_stats',
    'clear_cache',
    # BB Mid
    'add_bb_indicators',
    'analyze_bb_mid_touch',
    'collect_event_returns',
    'quartile_reach_stats',
    # Combo Filter
    'analyze_combo_filter',
    'add_combo_indicators',
    'build_ma_filter',
    'build_bb_filter',
    'build_pattern_filter',
    'run_tp_backtest',
    # Squeeze
    'analyze_multi_tf_squeeze',
    'add_squeeze_indicators',
    'find_squeeze_breakouts',
    # Hybrid
    'analyze_hybrid_strategy',
    'run_hybrid_backtest',
]
