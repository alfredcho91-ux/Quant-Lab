"""
Streak 분석 통계 함수 모듈
통계 계산 관련 함수들을 분리하여 재사용성과 유지보수성 향상
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from utils.stats import (
    CONFIDENCE_LEVEL,
    P_VALUE_FLOOR,
    safe_float,
    wilson_confidence_interval,
    calculate_binomial_pvalue,
)
from strategy.streak.distribution import (
    calculate_intraday_distribution,
    calculate_weekly_distribution,
)


def _normalize_p_value(p_value: Optional[float]) -> Tuple[Optional[float], bool]:
    """
    p-value 수치 안정화.

    Wall Street 스타일 실무 관행을 따라 극소값(언더플로우 0 포함)은
    제외하지 않고 floor로 클램프해 판정 일관성을 유지한다.
    """
    if p_value is None:
        return None, False
    try:
        p = float(p_value)
    except (ValueError, TypeError):
        return None, False

    if np.isnan(p) or np.isinf(p):
        return None, False
    if p < 0:
        p = 0.0

    if p < P_VALUE_FLOOR:
        return P_VALUE_FLOOR, True
    return p, False


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


def analyze_interval_bins_stats(
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


# 상수 (구간별 분석용)
MIN_SAMPLE_SIZE_RELIABLE = 30
MIN_SAMPLE_SIZE_MEDIUM = 10
DEFAULT_HIGH_PROB_MIN_SAMPLE = MIN_SAMPLE_SIZE_MEDIUM


def bonferroni_correction(p_value: float, num_tests: int) -> dict:
    """Bonferroni 보정 - 다중비교 시 False Positive 감소"""
    adjusted_alpha = 0.05 / max(num_tests, 1)
    normalized_p, floor_applied = _normalize_p_value(p_value)
    is_significant = bool(normalized_p is not None and normalized_p < adjusted_alpha)
    return {
        "original_p": float(round(normalized_p, 4)) if normalized_p is not None else None,
        "adjusted_alpha": float(round(adjusted_alpha, 4)),
        "num_tests": int(num_tests),
        "is_significant_after_correction": bool(is_significant),
        "warning": f"다중비교 보정 적용: {num_tests}개 테스트 중 하나" if num_tests > 1 else None,
        "p_value_floor": P_VALUE_FLOOR if floor_applied else None,
        "p_value_display": f"<{P_VALUE_FLOOR:g}" if floor_applied else None,
    }


def analyze_interval_statistics(
    data_series: pd.Series,
    target_series: pd.Series,
    bins: List[float],
    confidence: float = CONFIDENCE_LEVEL,
    high_prob_min_sample: int = DEFAULT_HIGH_PROB_MIN_SAMPLE
) -> tuple:
    """
    구간별 통계 분석 (RSI/Disparity 등) - Wilson CI, Bonferroni 보정 포함
    
    Args:
        data_series: 분석 대상 값 시리즈
        target_series: 성공/실패 타깃 시리즈
        bins: 구간 경계값
        confidence: 신뢰수준
        high_prob_min_sample: high_prob 구간 최소 샘플 수 (기본값: DEFAULT_HIGH_PROB_MIN_SAMPLE=10)
    
    Returns:
        (interval_dict, high_prob_dict)
    """
    interval_dict = {}
    high_prob_dict = {}

    if len(data_series) == 0:
        return interval_dict, high_prob_dict

    num_bins = len(bins) - 1
    data_bin = pd.cut(data_series, bins=bins)
    target_bool = target_series.fillna(False).astype(bool)
    analysis = pd.DataFrame({'bin': data_bin, 'target': target_bool}).groupby(
        'bin', observed=False
    )['target'].agg(['sum', 'count'])

    for interval, row in analysis.iterrows():
        successes = int(row['sum']) if pd.notna(row['sum']) else 0
        count = int(row['count'])
        if count < 1:
            continue

        ci_data = wilson_confidence_interval(successes, count, confidence)
        if ci_data is None or ci_data.get("rate") is None:
            continue

        raw_pvalue = calculate_binomial_pvalue(successes, count, 0.5)
        pvalue, pvalue_floor_applied = _normalize_p_value(raw_pvalue)
        if pvalue is None:
            continue
        correction = bonferroni_correction(pvalue, num_bins)

        if count >= MIN_SAMPLE_SIZE_RELIABLE:
            reliability, is_reliable = 'high', True
        elif count >= MIN_SAMPLE_SIZE_MEDIUM:
            reliability, is_reliable = 'medium', True
        else:
            reliability, is_reliable = 'low', False

        interval_dict[str(interval)] = {
            **ci_data,
            "sample_size": count,
            "is_reliable": is_reliable,
            "reliability": reliability,
            "p_value": float(round(pvalue, 4)),
            "is_significant": bool(pvalue < 0.05),
            "bonferroni": correction,
            "p_value_display": f"<{P_VALUE_FLOOR:g}" if pvalue_floor_applied else None,
        }
        # high_prob: 60% 이상 + 최소 샘플 수 조건
        # 기본값(10): 소규모 표본 과대추정 방지를 위한 보수적 기준
        if ci_data["rate"] >= 60 and count >= high_prob_min_sample:
            high_prob_dict[str(interval)] = {
                **ci_data,
                "sample_size": count,
                "is_reliable": is_reliable,
                "reliability": reliability,
                "p_value": float(round(pvalue, 4)),
                "bonferroni_significant": bool(correction["is_significant_after_correction"]),
                "p_value_display": f"<{P_VALUE_FLOOR:g}" if pvalue_floor_applied else None,
            }

    return interval_dict, high_prob_dict


def analyze_2d_interval_heatmap(
    x_series: pd.Series,
    y_series: pd.Series,
    target_series: pd.Series,
    x_bins: List[float],
    y_bins: List[float],
    x_label: str = "X",
    y_label: str = "Y",
    confidence: float = CONFIDENCE_LEVEL,
) -> Dict[str, Any]:
    """
    2차원 구간(heatmap) 조건부 확률 분석.

    Args:
        x_series: X축 값 시리즈 (예: RSI)
        y_series: Y축 값 시리즈 (예: ATR%)
        target_series: 성공/실패 타깃 시리즈 (bool 변환 가능)
        x_bins: X축 구간 경계
        y_bins: Y축 구간 경계
        x_label: X축 라벨
        y_label: Y축 라벨
        confidence: 신뢰수준

    Returns:
        heatmap payload:
        {
          x_label, y_label,
          x_bins, y_bins,
          cells: {y_bin: {x_bin: cell}},
          total_samples, tested_cells, significant_cells
        }
    """
    empty = {
        "x_label": x_label,
        "y_label": y_label,
        "x_bins": [],
        "y_bins": [],
        "cells": {},
        "total_samples": 0,
        "tested_cells": 0,
        "significant_cells": 0,
    }

    if len(x_series) == 0 or len(y_series) == 0:
        return empty

    x_cut = pd.cut(x_series, bins=x_bins, include_lowest=True)
    y_cut = pd.cut(y_series, bins=y_bins, include_lowest=True)
    target_bool = target_series.fillna(False).astype(bool)

    frame = pd.DataFrame(
        {
            "x_bin": x_cut,
            "y_bin": y_cut,
            "target": target_bool,
        }
    ).dropna(subset=["x_bin", "y_bin"])

    if frame.empty:
        return empty

    x_categories = list(frame["x_bin"].cat.categories)
    y_categories = list(frame["y_bin"].cat.categories)
    x_labels = [str(c) for c in x_categories]
    y_labels = [str(c) for c in y_categories]

    grouped = frame.groupby(["y_bin", "x_bin"], observed=False)["target"].agg(["sum", "count"])
    num_tests = max(len(x_categories) * len(y_categories), 1)

    cells: Dict[str, Dict[str, Dict[str, Any]]] = {}
    tested_cells = 0
    significant_cells = 0

    for y_cat in y_categories:
        y_key = str(y_cat)
        cells[y_key] = {}
        for x_cat in x_categories:
            x_key = str(x_cat)
            idx = (y_cat, x_cat)

            if idx not in grouped.index:
                cells[y_key][x_key] = {
                    "rate": None,
                    "sample_size": 0,
                    "ci_lower": None,
                    "ci_upper": None,
                    "is_reliable": False,
                    "reliability": "low",
                    "is_significant": False,
                    "bonferroni_significant": False,
                }
                continue

            row = grouped.loc[idx]
            count = int(row["count"]) if pd.notna(row["count"]) else 0
            successes = int(row["sum"]) if pd.notna(row["sum"]) else 0

            if count <= 0:
                cells[y_key][x_key] = {
                    "rate": None,
                    "sample_size": 0,
                    "ci_lower": None,
                    "ci_upper": None,
                    "is_reliable": False,
                    "reliability": "low",
                    "is_significant": False,
                    "bonferroni_significant": False,
                }
                continue

            tested_cells += 1
            ci_data = wilson_confidence_interval(successes, count, confidence)
            if ci_data is None or ci_data.get("rate") is None:
                cells[y_key][x_key] = {
                    "rate": None,
                    "sample_size": count,
                    "ci_lower": None,
                    "ci_upper": None,
                    "is_reliable": False,
                    "reliability": "low",
                    "is_significant": False,
                    "bonferroni_significant": False,
                }
                continue

            raw_pvalue = calculate_binomial_pvalue(successes, count, 0.5)
            pvalue, _ = _normalize_p_value(raw_pvalue)
            if pvalue is None:
                pvalue = 1.0
            correction = bonferroni_correction(pvalue, num_tests)
            bonf_sig = bool(correction["is_significant_after_correction"])
            if bonf_sig:
                significant_cells += 1

            if count >= MIN_SAMPLE_SIZE_RELIABLE:
                reliability, is_reliable = "high", True
            elif count >= MIN_SAMPLE_SIZE_MEDIUM:
                reliability, is_reliable = "medium", True
            else:
                reliability, is_reliable = "low", False

            cells[y_key][x_key] = {
                "rate": float(round(ci_data["rate"], 2)),
                "sample_size": count,
                "ci_lower": float(round(ci_data["ci_lower"], 2)),
                "ci_upper": float(round(ci_data["ci_upper"], 2)),
                "is_reliable": is_reliable,
                "reliability": reliability,
                "is_significant": bool(pvalue < 0.05),
                "bonferroni_significant": bonf_sig,
            }

    return {
        "x_label": x_label,
        "y_label": y_label,
        "x_bins": x_labels,
        "y_bins": y_labels,
        "cells": cells,
        "total_samples": int(len(frame)),
        "tested_cells": int(tested_cells),
        "significant_cells": int(significant_cells),
    }
