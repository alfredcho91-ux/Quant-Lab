"""
Streak 아키텍처 계약(SSOT) 테스트.

목표:
- 통계 헬퍼는 strategy.streak.statistics 에서만 사용
- strategy.streak.common 에서 통계 헬퍼 재노출 금지
- high_prob 최소 샘플 기본값 단일 소스 유지
"""

import ast
import inspect
import sys
from pathlib import Path

import pandas as pd


backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

from strategy.streak import common as streak_common
from strategy.streak import statistics as streak_statistics
from strategy.context import AnalysisContext
from strategy.streak.cache_ops import generate_analysis_cache_key
from strategy.streak.statistics import analyze_interval_statistics
from models.request import StreakAnalysisParams


STAT_HELPER_NAMES = {
    "safe_float",
    "wilson_confidence_interval",
    "bonferroni_correction",
    "calculate_binomial_pvalue",
    "analyze_interval_statistics",
}


def test_streak_common_does_not_reexport_statistics_helpers():
    """common.py는 통계 함수의 import/re-export 레이어가 되지 않아야 한다."""
    exported_names = set(getattr(streak_common, "__all__", []))
    leaked = sorted(
        (STAT_HELPER_NAMES & exported_names)
        | {name for name in STAT_HELPER_NAMES if hasattr(streak_common, name)}
    )
    assert leaked == [], f"streak.common에서 통계 헬퍼가 노출되면 안 됩니다: {leaked}"


def test_no_module_imports_statistics_helpers_from_common():
    """호출부는 statistics.py를 직접 import해야 한다."""
    offenders = []
    backend_root = Path(__file__).resolve().parents[1]
    ignored_dirs = {"venv", ".venv", "__pycache__"}

    for py_file in backend_root.rglob("*.py"):
        if any(part in ignored_dirs for part in py_file.parts):
            continue
        code = py_file.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(py_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "strategy.streak.common":
                continue

            for alias in node.names:
                if alias.name in STAT_HELPER_NAMES:
                    rel_path = py_file.relative_to(backend_root)
                    offenders.append(f"{rel_path}:{node.lineno}:{alias.name}")

    assert offenders == [], (
        "statistics 헬퍼를 common에서 import한 모듈이 있습니다: "
        + ", ".join(offenders)
    )


def test_high_prob_min_sample_single_source_contract():
    """high_prob 최소 샘플 기본값은 statistics.py 상수와 시그니처가 일치해야 한다."""
    sig = inspect.signature(streak_statistics.analyze_interval_statistics)
    default_val = sig.parameters["high_prob_min_sample"].default

    assert streak_statistics.DEFAULT_HIGH_PROB_MIN_SAMPLE == 10
    assert streak_statistics.DEFAULT_HIGH_PROB_MIN_SAMPLE == streak_statistics.MIN_SAMPLE_SIZE_MEDIUM
    assert default_val == streak_statistics.DEFAULT_HIGH_PROB_MIN_SAMPLE


def test_high_prob_default_threshold_behavior():
    """기본 임계값(10) 기준으로 9개/10개 샘플에서 동작이 달라져야 한다."""
    bins = [0, 100]

    data_9 = pd.Series([50.0] * 9)
    target_9 = pd.Series([True] * 9)
    _, high_prob_9 = analyze_interval_statistics(data_9, target_9, bins)
    assert high_prob_9 == {}

    data_10 = pd.Series([50.0] * 10)
    target_10 = pd.Series([True] * 10)
    _, high_prob_10 = analyze_interval_statistics(data_10, target_10, bins)
    assert len(high_prob_10) == 1
    only_value = next(iter(high_prob_10.values()))
    assert only_value["sample_size"] == 10


def test_analysis_cache_key_includes_simple_mode_body_filter_threshold():
    """Simple mode 캐시 키는 min_total_body_pct 값 변화에 따라 달라져야 한다."""
    base_kwargs = {
        "coin": "BTC",
        "interval": "1h",
        "n_streak": 3,
        "direction": "green",
        "use_complex_pattern": False,
        "complex_pattern": None,
        "rsi_threshold": 60.0,
    }

    key_none = generate_analysis_cache_key(
        AnalysisContext(min_total_body_pct=None, **base_kwargs)
    )
    key_zero = generate_analysis_cache_key(
        AnalysisContext(min_total_body_pct=0.0, **base_kwargs)
    )
    key_10 = generate_analysis_cache_key(
        AnalysisContext(min_total_body_pct=10.0, **base_kwargs)
    )
    key_20 = generate_analysis_cache_key(
        AnalysisContext(min_total_body_pct=20.0, **base_kwargs)
    )

    assert "_bodynone" in key_none
    assert key_none == key_zero
    assert "_body10" in key_10
    assert "_body20" in key_20
    assert key_10 != key_20


def test_analysis_cache_key_complex_mode_ignores_simple_mode_body_filter():
    """Complex mode는 min_total_body_pct를 사용하지 않으므로 캐시 키가 동일해야 한다."""
    ctx_a = AnalysisContext(
        coin="BTC",
        interval="1h",
        n_streak=3,
        direction="green",
        use_complex_pattern=True,
        complex_pattern=[1, 1, -1],
        rsi_threshold=60.0,
        min_total_body_pct=10.0,
    )
    ctx_b = AnalysisContext(
        coin="BTC",
        interval="1h",
        n_streak=3,
        direction="green",
        use_complex_pattern=True,
        complex_pattern=[1, 1, -1],
        rsi_threshold=60.0,
        min_total_body_pct=20.0,
    )

    assert generate_analysis_cache_key(ctx_a) == generate_analysis_cache_key(ctx_b)


def test_analysis_cache_key_includes_ema_200_position_for_all_modes():
    """EMA 200 필터는 simple/complex 모두 분석 결과를 바꾸므로 캐시 키에 포함되어야 한다."""
    simple_base = {
        "coin": "BTC",
        "interval": "1h",
        "n_streak": 3,
        "direction": "green",
        "use_complex_pattern": False,
        "complex_pattern": None,
        "rsi_threshold": 60.0,
        "min_total_body_pct": None,
    }
    simple_any = generate_analysis_cache_key(
        AnalysisContext(ema_200_position=None, **simple_base)
    )
    simple_above = generate_analysis_cache_key(
        AnalysisContext(ema_200_position="above", **simple_base)
    )
    simple_below = generate_analysis_cache_key(
        AnalysisContext(ema_200_position="below", **simple_base)
    )

    assert "_emaany" in simple_any
    assert "_emaabove" in simple_above
    assert "_emabelow" in simple_below
    assert simple_above != simple_below

    complex_base = {
        "coin": "BTC",
        "interval": "1h",
        "n_streak": 3,
        "direction": "green",
        "use_complex_pattern": True,
        "complex_pattern": [1, 1, -1],
        "rsi_threshold": 60.0,
        "min_total_body_pct": None,
    }
    complex_above = generate_analysis_cache_key(
        AnalysisContext(ema_200_position="above", **complex_base)
    )
    complex_below = generate_analysis_cache_key(
        AnalysisContext(ema_200_position="below", **complex_base)
    )

    assert "_emaabove" in complex_above
    assert "_emabelow" in complex_below
    assert complex_above != complex_below


def test_timezone_offset_default_is_not_hardcoded():
    """Legacy timezone_offset 기본값은 None이어야 하며, 실분석은 pytz timezone 설정을 사용한다."""
    params = StreakAnalysisParams()
    assert params.timezone_offset is None
    assert params.ema_200_position is None

    context = AnalysisContext.from_params({})
    assert context.timezone_offset is None
    assert context.ema_200_position is None
