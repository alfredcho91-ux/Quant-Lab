"""
통계 로직 단위 테스트

목적: 핵심 통계 함수들의 정확성을 검증
위치: backend/strategy/streak/statistics.py (SSOT)

⚠️ 핵심 제약 조건: 이 테스트들은 통계적 정확성의 핵심이므로 반드시 통과해야 함
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

# Import statistics functions
from strategy.streak.statistics import (
    analyze_2d_interval_heatmap,
    analyze_interval_statistics,
    bonferroni_correction,
    calculate_binomial_pvalue,
    wilson_confidence_interval,
    calculate_intraday_distribution,
)


class TestWilsonConfidenceInterval:
    """Wilson Score 신뢰구간 계산 검증"""
    
    def test_wilson_ci_basic_calculation(self):
        """기본 Wilson Score Interval 계산 검증"""
        # Given: 100번 중 60번 성공 (60% 성공률)
        result = wilson_confidence_interval(successes=60, total=100, confidence=0.95)
        
        # Then: 결과가 올바른 구조를 가져야 함
        assert "rate" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert "ci_width" in result
        
        # 성공률이 60%에 가까워야 함
        assert abs(result["rate"] - 60.0) < 1.0, f"성공률이 60%에 가까워야 함 (실제: {result['rate']}%)"
        
        # 신뢰구간이 0-100 사이여야 함
        assert 0 <= result["ci_lower"] <= 100, f"하한이 0-100 사이여야 함 (실제: {result['ci_lower']})"
        assert 0 <= result["ci_upper"] <= 100, f"상한이 0-100 사이여야 함 (실제: {result['ci_upper']})"
        
        # 하한 < 성공률 < 상한
        assert result["ci_lower"] < result["rate"] < result["ci_upper"], \
            f"신뢰구간이 성공률을 포함해야 함 (하한: {result['ci_lower']}, 성공률: {result['rate']}, 상한: {result['ci_upper']})"
    
    def test_wilson_ci_zero_total(self):
        """total이 0인 경우 처리 검증"""
        result = wilson_confidence_interval(successes=0, total=0, confidence=0.95)
        
        assert result["rate"] is None
        assert result["ci_lower"] is None
        assert result["ci_upper"] is None
        assert result["ci_width"] is None
    
    def test_wilson_ci_all_successes(self):
        """모든 시도가 성공한 경우 (100% 성공률)"""
        result = wilson_confidence_interval(successes=100, total=100, confidence=0.95)
        
        assert result["rate"] == 100.0
        assert result["ci_lower"] < 100.0  # 100%는 신뢰구간 상한이 될 수 없음
        assert result["ci_upper"] == 100.0
    
    def test_wilson_ci_all_failures(self):
        """모든 시도가 실패한 경우 (0% 성공률)"""
        result = wilson_confidence_interval(successes=0, total=100, confidence=0.95)
        
        assert result["rate"] == 0.0
        # 부동소수점 오차 허용 (매우 작은 값은 0으로 간주)
        assert abs(result["ci_lower"]) < 1e-10 or result["ci_lower"] == 0.0
        assert result["ci_upper"] > 0.0  # 0%는 신뢰구간 하한이 될 수 없음
    
    def test_wilson_ci_small_sample(self):
        """작은 샘플 크기 (N < 10) 검증"""
        # Given: 5번 중 3번 성공 (60% 성공률, 작은 샘플)
        result = wilson_confidence_interval(successes=3, total=5, confidence=0.95)
        
        # Then: 신뢰구간이 넓어야 함 (작은 샘플은 불확실성이 큼)
        assert result["ci_width"] > 20, f"작은 샘플은 넓은 신뢰구간을 가져야 함 (실제: {result['ci_width']})"
        
        # 신뢰구간이 0-100 사이여야 함
        assert 0 <= result["ci_lower"] <= 100
        assert 0 <= result["ci_upper"] <= 100
    
    def test_wilson_ci_confidence_level_95(self):
        """95% 신뢰수준 검증 (z = 1.96)"""
        # Given: 100번 중 50번 성공
        result = wilson_confidence_interval(successes=50, total=100, confidence=0.95)
        
        # Then: 신뢰구간이 대략 40-60% 사이여야 함 (대칭 분포)
        # 실제로는 약 40.2-59.8% 정도
        assert 35 < result["ci_lower"] < 45, f"하한이 예상 범위 내여야 함 (실제: {result['ci_lower']})"
        assert 55 < result["ci_upper"] < 65, f"상한이 예상 범위 내여야 함 (실제: {result['ci_upper']})"
    
    def test_wilson_ci_confidence_level_99(self):
        """99% 신뢰수준 검증 (z = 2.576)"""
        # Given: 100번 중 50번 성공, 99% 신뢰수준
        result = wilson_confidence_interval(successes=50, total=100, confidence=0.99)
        
        # Then: 99% 신뢰구간이 95% 신뢰구간보다 넓어야 함
        result_95 = wilson_confidence_interval(successes=50, total=100, confidence=0.95)
        
        assert result["ci_width"] > result_95["ci_width"], \
            f"99% 신뢰구간이 95% 신뢰구간보다 넓어야 함 (99%: {result['ci_width']}, 95%: {result_95['ci_width']})"


class TestBonferroniCorrection:
    """Bonferroni 보정 검증"""
    
    def test_bonferroni_correction_single_test(self):
        """단일 테스트 (보정 불필요)"""
        result = bonferroni_correction(p_value=0.03, num_tests=1)
        
        assert result["adjusted_alpha"] == 0.05
        assert result["num_tests"] == 1
        assert result["is_significant_after_correction"] == True  # 0.03 < 0.05
    
    def test_bonferroni_correction_multiple_tests(self):
        """다중 테스트 보정 (8개 구간)"""
        # Given: 8개 구간 분석, p-value = 0.04
        result = bonferroni_correction(p_value=0.04, num_tests=8)
        
        # Then: adjusted_alpha = 0.05 / 8 = 0.00625
        assert abs(result["adjusted_alpha"] - 0.00625) < 0.0001, \
            f"adjusted_alpha가 0.00625여야 함 (실제: {result['adjusted_alpha']})"
        
        # 0.04 > 0.00625이므로 유의하지 않음
        assert result["is_significant_after_correction"] == False
    
    def test_bonferroni_correction_significant_after_correction(self):
        """보정 후에도 유의한 경우"""
        # Given: 매우 작은 p-value (0.001), 8개 구간
        result = bonferroni_correction(p_value=0.001, num_tests=8)
        
        # Then: 0.001 < 0.00625이므로 유의함
        assert result["is_significant_after_correction"] == True
    
    def test_bonferroni_correction_edge_case(self):
        """경계 케이스: p-value = adjusted_alpha"""
        # Given: p-value가 adjusted_alpha와 정확히 같음
        result = bonferroni_correction(p_value=0.00625, num_tests=8)
        
        # Then: p-value < adjusted_alpha이므로 유의함 (엄격한 부등호)
        assert result["is_significant_after_correction"] == False  # 0.00625 < 0.00625는 False

    def test_bonferroni_correction_zero_pvalue_floor_behavior(self):
        """극소 p-value(0 포함)는 floor로 안정화하되 유의성은 유지"""
        result = bonferroni_correction(p_value=0.0, num_tests=8)

        assert result["is_significant_after_correction"] is True
        assert result["original_p"] == 0.0
        assert result["p_value_floor"] is not None
        assert result["p_value_display"] is not None


class TestBinomialPValue:
    """이항검정 p-value 계산 검증"""
    
    def test_binomial_pvalue_fair_coin(self):
        """공정한 동전 (null_prob = 0.5)"""
        # Given: 100번 중 50번 성공 (정확히 50%)
        pvalue = calculate_binomial_pvalue(successes=50, total=100, null_prob=0.5)
        
        # Then: p-value가 1.0에 가까워야 함 (공정한 동전과 차이 없음)
        assert pvalue > 0.5, f"공정한 동전은 높은 p-value를 가져야 함 (실제: {pvalue})"
    
    def test_binomial_pvalue_biased_coin(self):
        """편향된 동전 (null_prob = 0.5, 실제 70% 성공)"""
        # Given: 100번 중 70번 성공 (70% 성공률)
        pvalue = calculate_binomial_pvalue(successes=70, total=100, null_prob=0.5)
        
        # Then: p-value가 매우 작아야 함 (공정한 동전과 유의한 차이)
        assert pvalue < 0.05, f"편향된 동전은 낮은 p-value를 가져야 함 (실제: {pvalue})"
    
    def test_binomial_pvalue_zero_total(self):
        """total이 0인 경우"""
        pvalue = calculate_binomial_pvalue(successes=0, total=0, null_prob=0.5)
        
        assert pvalue == 1.0
    
    def test_binomial_pvalue_extreme_cases(self):
        """극단적인 케이스"""
        # 모든 성공
        pvalue_all = calculate_binomial_pvalue(successes=100, total=100, null_prob=0.5)
        assert pvalue_all < 0.001, "모든 성공은 매우 낮은 p-value를 가져야 함"
        
        # 모든 실패
        pvalue_none = calculate_binomial_pvalue(successes=0, total=100, null_prob=0.5)
        assert pvalue_none < 0.001, "모든 실패는 매우 낮은 p-value를 가져야 함"


class TestAnalyzeIntervalStatistics:
    """구간별 통계 분석 검증"""
    
    def test_analyze_interval_statistics_basic(self):
        """기본 구간별 통계 분석"""
        # Given: RSI 값과 성공 여부 시리즈
        dates = pd.date_range(start='2024-01-01', periods=98, freq='D')
        rsi_values = pd.Series([25, 35, 45, 55, 65, 75, 85, 95] * 12 + [50, 50], index=dates)
        success_values = pd.Series([True, False, True, True, False, True, True, False] * 12 + [True, False], index=dates)
        
        # RSI 구간: [0, 30, 40, 50, 60, 70, 80, 100]
        bins = [0, 30, 40, 50, 60, 70, 80, 100]
        
        # When: 구간별 통계 분석
        interval_dict, high_prob_dict = analyze_interval_statistics(
            data_series=rsi_values,
            target_series=success_values,
            bins=bins,
            confidence=0.95
        )
        
        # Then: 결과가 올바른 구조를 가져야 함
        assert isinstance(interval_dict, dict)
        assert isinstance(high_prob_dict, dict)
        
        # 각 구간에 대한 통계가 있어야 함
        for interval_key in interval_dict.keys():
            interval_data = interval_dict[interval_key]
            
            # 필수 필드 확인
            assert "rate" in interval_data
            assert "ci_lower" in interval_data
            assert "ci_upper" in interval_data
            assert "sample_size" in interval_data
            assert "p_value" in interval_data
            assert "bonferroni" in interval_data
            
            # Bonferroni 보정 확인
            bonferroni_data = interval_data["bonferroni"]
            assert "adjusted_alpha" in bonferroni_data
            assert "is_significant_after_correction" in bonferroni_data
    
    def test_analyze_interval_statistics_bonferroni_correction(self):
        """Bonferroni 보정이 올바르게 적용되는지 검증"""
        # Given: 8개 구간 분석
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        rsi_values = pd.Series([50] * 100, index=dates)
        success_values = pd.Series([True] * 50 + [False] * 50, index=dates)
        
        bins = [0, 30, 40, 50, 60, 70, 80, 100]  # 8개 구간
        
        # When: 구간별 통계 분석
        interval_dict, _ = analyze_interval_statistics(
            data_series=rsi_values,
            target_series=success_values,
            bins=bins,
            confidence=0.95
        )
        
        # Then: 모든 구간에서 Bonferroni 보정이 적용되어야 함
        # 실제로는 데이터가 있는 구간만 반환되므로, num_tests는 bins 수와 일치해야 함
        expected_num_tests = len(bins) - 1  # 8개 구간
        for interval_key, interval_data in interval_dict.items():
            bonferroni = interval_data["bonferroni"]
            
            # adjusted_alpha = 0.05 / num_tests
            expected_adjusted_alpha = 0.05 / expected_num_tests
            assert abs(bonferroni["adjusted_alpha"] - expected_adjusted_alpha) < 0.0001, \
                f"구간 {interval_key}의 adjusted_alpha가 {expected_adjusted_alpha}여야 함 (실제: {bonferroni['adjusted_alpha']})"
            
            assert bonferroni["num_tests"] == expected_num_tests
    
    def test_analyze_interval_statistics_reliability(self):
        """신뢰도 판단 검증"""
        # Given: 다양한 샘플 크기
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        # 샘플 크기 < 10 (Low Reliability)
        rsi_small = pd.Series([50] * 5, index=dates[:5])
        success_small = pd.Series([True] * 3 + [False] * 2, index=dates[:5])
        
        # 샘플 크기 >= 10, < 30 (Medium Reliability)
        rsi_medium = pd.Series([50] * 20, index=dates[:20])
        success_medium = pd.Series([True] * 12 + [False] * 8, index=dates[:20])
        
        # 샘플 크기 >= 30 (High Reliability)
        rsi_large = pd.Series([50] * 50, index=dates[:50])
        success_large = pd.Series([True] * 30 + [False] * 20, index=dates[:50])
        
        bins = [0, 30, 40, 50, 60, 70, 80, 100]
        
        # When: 각 샘플 크기에 대해 분석
        _, _ = analyze_interval_statistics(rsi_small, success_small, bins, confidence=0.95)
        interval_medium, _ = analyze_interval_statistics(rsi_medium, success_medium, bins, confidence=0.95)
        interval_large, _ = analyze_interval_statistics(rsi_large, success_large, bins, confidence=0.95)
        
        # Then: 신뢰도가 올바르게 판단되어야 함
        # Medium: 10 <= sample_size < 30
        for interval_data in interval_medium.values():
            assert interval_data["reliability"] in ["low", "medium", "high"]
        
        # Large: sample_size >= 30
        for interval_data in interval_large.values():
            if interval_data["sample_size"] >= 30:
                assert interval_data["reliability"] == "high", \
                    f"샘플 크기 >= 30은 high reliability여야 함 (실제: {interval_data['reliability']})"


class TestAnalyze2DIntervalHeatmap:
    """2차원 조건부 확률(Heatmap) 계산 검증"""

    def test_heatmap_basic_structure(self):
        dates = pd.date_range(start="2024-01-01", periods=40, freq="D")
        x_values = pd.Series([25, 35, 45, 55, 65, 75, 85, 95] * 5, index=dates)
        y_values = pd.Series([0.8, 1.2, 1.8, 2.4, 3.2] * 8, index=dates)
        targets = pd.Series(([True, False, True, True, False] * 8), index=dates)

        x_bins = [0, 30, 40, 50, 60, 70, 80, 100]
        y_bins = [0, 1, 2, 3, 4]

        out = analyze_2d_interval_heatmap(
            x_series=x_values,
            y_series=y_values,
            target_series=targets,
            x_bins=x_bins,
            y_bins=y_bins,
            x_label="RSI",
            y_label="ATR%",
            confidence=0.95,
        )

        assert out["x_label"] == "RSI"
        assert out["y_label"] == "ATR%"
        assert isinstance(out["x_bins"], list)
        assert isinstance(out["y_bins"], list)
        assert isinstance(out["cells"], dict)
        assert len(out["x_bins"]) == len(x_bins) - 1
        assert len(out["y_bins"]) == len(y_bins) - 1

        first_y = out["y_bins"][0]
        first_x = out["x_bins"][0]
        first_cell = out["cells"][first_y][first_x]
        assert "rate" in first_cell
        assert "sample_size" in first_cell
        assert "ci_lower" in first_cell
        assert "ci_upper" in first_cell
        assert "is_significant" in first_cell
        assert "bonferroni_significant" in first_cell

    def test_heatmap_includes_zero_sample_cells(self):
        dates = pd.date_range(start="2024-01-01", periods=20, freq="D")
        x_values = pd.Series([22] * 20, index=dates)  # 저구간에만 집중
        y_values = pd.Series([0.7] * 20, index=dates)  # 저구간에만 집중
        targets = pd.Series([True, False] * 10, index=dates)

        x_bins = [0, 30, 40, 50, 60]
        y_bins = [0, 1, 2, 3]

        out = analyze_2d_interval_heatmap(
            x_series=x_values,
            y_series=y_values,
            target_series=targets,
            x_bins=x_bins,
            y_bins=y_bins,
            x_label="RSI",
            y_label="ATR%",
            confidence=0.95,
        )

        empty_cells = []
        for y_bin in out["y_bins"]:
            for x_bin in out["x_bins"]:
                cell = out["cells"][y_bin][x_bin]
                if cell["sample_size"] == 0:
                    empty_cells.append(cell)

        assert len(empty_cells) > 0
        for cell in empty_cells[:3]:
            assert cell["rate"] is None
            assert cell["ci_lower"] is None
            assert cell["ci_upper"] is None
            assert cell["is_significant"] is False
            assert cell["bonferroni_significant"] is False


class TestCalculateIntradayDistribution:
    """시간대별 분포 계산 검증"""
    
    def test_calculate_intraday_distribution_unsupported_interval(self):
        """지원하지 않는 타임프레임 검증"""
        # Given: 1h 타임프레임 (지원하지 않음)
        dates = [pd.Timestamp('2024-01-01')]
        
        result = calculate_intraday_distribution(
            pattern_result_dates=dates,
            interval='1h',
            coin='BTC',
            timezone_offset=-5
        )
        
        # Then: None 반환 및 메시지
        assert result["low_window"] is None
        assert result["avg_volatility"] is None
        assert "note" in result
        assert "일봉" in result["note"] or "3일봉" in result["note"]
    
    def test_calculate_intraday_distribution_empty_dates(self):
        """빈 날짜 리스트 검증"""
        result = calculate_intraday_distribution(
            pattern_result_dates=[],
            interval='1d',
            coin='BTC',
            timezone_offset=-5
        )
        
        assert result["low_window"] is None
        assert result["avg_volatility"] is None
        assert "note" in result
        assert "날짜가 없습니다" in result["note"]
    
    def test_calculate_intraday_distribution_structure(self):
        """결과 구조 검증 (실제 데이터 없이 구조만 확인)"""
        # Given: 유효한 날짜 리스트
        dates = [pd.Timestamp('2024-01-01')]
        
        # When: 시간대별 분포 계산 (실제 데이터가 없어도 구조는 반환)
        result = calculate_intraday_distribution(
            pattern_result_dates=dates,
            interval='1d',
            coin='BTC',
            timezone_offset=-5
        )
        
        # Then: 결과가 올바른 구조를 가져야 함
        assert "low_window" in result
        assert "avg_volatility" in result
        assert "hourly_low_probability" in result
        assert "hourly_high_probability" in result
        
        # hourly_low_probability와 hourly_high_probability는 딕셔너리여야 함
        assert isinstance(result["hourly_low_probability"], dict)
        assert isinstance(result["hourly_high_probability"], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
