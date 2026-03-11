"""Complex Mode 전략 (복합 패턴 분석)"""

import pandas as pd
from typing import Dict, Any, List
import logging
import traceback

from strategy.context import AnalysisContext
from strategy.streak.analyzer import calculate_complex_analysis
from strategy.streak.common import (
    normalize_single_index,
    find_complex_pattern,
    analyze_pullback_quality,
    calculate_signal_score,
    safe_get_rsi,
    get_or_calculate_indicators,
    safe_round,
    sanitize_for_json,
    DEFAULT_RSI,
    DEBUG_MODE,
)
from strategy.streak.patterns import build_pattern_profile

logger = logging.getLogger(__name__)


def run_complex_analysis(df: pd.DataFrame, context: AnalysisContext, from_cache: bool = False) -> Dict[str, Any]:
    """
    Complex Mode 분석 실행
    
    Args:
        df: 준비된 DataFrame (prepare_dataframe으로 처리됨)
        context: 분석 컨텍스트
        from_cache: 캐시 사용 여부
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        # 1. 기술적 지표 계산 (RSI, ATR, Disparity 등) - 캐싱 적용
        df = get_or_calculate_indicators(context.coin, context.interval, df)
        
        # 2. 패턴/방향 메타 계산
        pattern_profile = build_pattern_profile(context.complex_pattern)
        if pattern_profile is None:
            return _empty_complex_result(context, from_cache)
        complex_pattern = pattern_profile.pattern

        # 3. 패턴 매칭
        matched_patterns = find_complex_pattern(df, complex_pattern)
        
        if len(matched_patterns) == 0:
            return _no_match_complex_result(context, complex_pattern, from_cache)
        
        # 4. 품질 분석
        quality_results = analyze_pullback_quality(
            df, matched_patterns.index,
            rise_len=pattern_profile.rise_len,
            drop_len=pattern_profile.drop_len
        )
        
        if len(quality_results) == 0:
            return {
                "success": False,
                "error": "조정 품질 분석 실패",
                "message": "패턴은 매칭되었지만 분석 가능한 데이터가 없습니다",
                "total_matches": len(matched_patterns),
                "mode": "complex",
                "pattern": complex_pattern,
                "from_cache": from_cache
            }
        
        # 5. 필터 적용 및 차트 데이터 생성
        filtered_indices, chart_data, scored_patterns = _filter_and_score_patterns(
            df,
            quality_results,
            expected_c1_direction=pattern_profile.expected_c1_direction,
            last_pattern_direction=pattern_profile.last_direction,
        )
        
        # 6. 필터 상태 정보
        total_cases = len(filtered_indices)
        filter_status = {
            "status": "success" if total_cases > 0 else "filtered_out",
            "total_matches": len(matched_patterns),
            "quality_results": len(quality_results),
            "filtered_count": total_cases
        }
        
        if total_cases == 0:
            filter_status["message"] = f"{len(matched_patterns)}개 패턴이 매칭되었지만 분석 가능한 케이스가 없습니다"
            filter_status["suggestions"] = [
                "다른 패턴을 시도해보세요"
            ]
        
        # 7. 복합 패턴 분석 (차트 데이터 기반)
        complex_pattern_analysis = calculate_complex_analysis(
            df, complex_pattern, matched_patterns, scored_patterns, chart_data, context
        )
        
        # 8. 결과 반환 (JSON 직렬화 전 NaN/Inf 정제)
        # C1 분석 데이터 추출 (프론트엔드 호환성을 위해 최상위 레벨에도 포함)
        c1_analysis = complex_pattern_analysis.get("summary", {}).get("c1_analysis", {})
        c2_analysis = complex_pattern_analysis.get("summary", {}).get("c2_analysis", {})
        
        result = {
            "success": True,
            "mode": "complex",
            "filter_status": filter_status,
            "total_cases": total_cases,
            # C1 양봉/음봉 확률 (프론트엔드 호환성)
            "continuation_rate": safe_round(c1_analysis.get("green_rate"), 2),
            "reversal_rate": safe_round(c1_analysis.get("red_rate"), 2),
            "continuation_count": c1_analysis.get("green_count", 0),
            "reversal_count": c1_analysis.get("red_count", 0),
            "avg_body_pct": None,  # Complex Mode에서는 사용하지 않음
            "continuation_ci": {
                "ci_lower": c1_analysis.get("green_confidence_interval", [None, None])[0],
                "ci_upper": c1_analysis.get("green_confidence_interval", [None, None])[1],
            } if c1_analysis.get("green_confidence_interval") else None,
            "c1_p_value": None,  # Complex Mode에서는 사용하지 않음
            "c1_is_significant": False,  # Complex Mode에서는 사용하지 않음
            # C2 분석 (C1 결과 기반)
            "c2_after_c1_green_rate": safe_round(c2_analysis.get("green_rate"), 2),
            "c2_after_c1_red_rate": safe_round(c2_analysis.get("red_rate"), 2),
            "c2_after_c1_green_ci": {
                "ci_lower": c2_analysis.get("green_confidence_interval", [None, None])[0],
                "ci_upper": c2_analysis.get("green_confidence_interval", [None, None])[1],
            } if c2_analysis.get("green_confidence_interval") else None,
            "c2_after_c1_red_ci": {
                "ci_lower": c2_analysis.get("red_confidence_interval", [None, None])[0],
                "ci_upper": c2_analysis.get("red_confidence_interval", [None, None])[1],
            } if c2_analysis.get("red_confidence_interval") else None,
            "c1_green_count": c1_analysis.get("green_count", 0),
            "c1_red_count": c1_analysis.get("red_count", 0),
            "comparative_report": complex_pattern_analysis.get("comparative_report"),
            "short_signal": complex_pattern_analysis.get("short_signal"),
            "volatility_stats": complex_pattern_analysis.get("volatility_stats"),
            "rsi_by_interval": complex_pattern_analysis.get("rsi_by_interval", {}),
            "disp_by_interval": complex_pattern_analysis.get("disp_by_interval", {}),
            "atr_by_interval": complex_pattern_analysis.get("atr_by_interval", {}),
            "rsi_atr_heatmap": complex_pattern_analysis.get("rsi_atr_heatmap"),
            "high_prob_rsi_intervals": complex_pattern_analysis.get("high_prob_rsi_intervals", {}),
            "high_prob_disp_intervals": complex_pattern_analysis.get("high_prob_disp_intervals", {}),
            "high_prob_atr_intervals": complex_pattern_analysis.get("high_prob_atr_intervals", {}),
            "complex_pattern_analysis": complex_pattern_analysis,
            "ny_trading_guide": None,
            "analysis_mode": {
                "type": "complex",
                "description": "Complex Pattern with Pullback",
                "parameters": {
                    "complex_pattern": complex_pattern,
                    "filters": {
                        "rsi_threshold": context.rsi_threshold
                    }
                }
            },
            "from_cache": from_cache,
            "coin": context.coin,
            "interval": context.interval,
            "n_streak": None,
            "direction": context.direction,
        }
        return sanitize_for_json(result)
        
    except Exception as e:
        logger.error(f"Error in run_complex_analysis: {e}\n{traceback.format_exc()}")
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc(),
            "mode": "complex"
        }


def _filter_and_score_patterns(
    df: pd.DataFrame,
    quality_results: List[Dict[str, Any]],
    expected_c1_direction: int,
    last_pattern_direction: int,
) -> tuple[List[Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """필터 적용 및 시그널 점수 계산"""
    filtered_indices = []
    chart_data = []
    scored_patterns = []

    df_len = len(df)
    index_values = df.index
    open_values = df['open'].to_numpy()
    close_values = df['close'].to_numpy()
    
    for q in quality_results:
        idx = q['index']
        try:
            # 인덱스 정규화 및 위치 찾기 (유틸리티 함수 사용)
            result = normalize_single_index(idx, df.index)
            if result is None:
                continue
            idx, pos = result
            
            # RSI 값 가져오기
            rsi_val = safe_get_rsi(df, idx, DEFAULT_RSI)
            
            # 되돌림 비율 필터 제거됨 (필터링하지 않음)
            
            # 다음 봉(C1) 데이터 추출
            c1_pos = pos + 1
            if c1_pos >= df_len:
                continue
            
            c1_idx = index_values[c1_pos]
            c1_data = None
            c2_data = None
            
            if c1_pos < df_len:
                c1_open = open_values[c1_pos]
                c1_close = close_values[c1_pos]
                base_close = close_values[pos]
                c1_color = 1 if c1_close > c1_open else -1
                c1_return = ((c1_close / base_close) - 1) * 100
                
                # ✅ 수정: 패턴 방향에 따른 성공 기준 적용 (롱/숏 모두 고려)
                # 패턴이 음봉으로 끝나면 → 반등 기대 (롱) → C1 양봉 = 성공
                # 패턴이 양봉으로 끝나면 → 조정 기대 (숏) → C1 음봉 = 성공
                c1_is_success = (c1_color == expected_c1_direction)
                
                c1_data = {
                    "date": str(c1_idx),
                    "color": c1_color,
                    "return": round(c1_return, 2),
                    "is_success": c1_is_success,
                    "expected_direction": expected_c1_direction  # 디버깅용: 기대한 방향
                }
                
                # 다음 다음 봉(C2) 데이터 추출
                c2_pos = pos + 2
                if c2_pos < df_len:
                    c2_idx = index_values[c2_pos]
                    c2_open = open_values[c2_pos]
                    c2_close = close_values[c2_pos]
                    c2_color = 1 if c2_close > c2_open else -1
                    c2_return = ((c2_close / c1_close) - 1) * 100
                    
                    # ✅ 수정: C2도 같은 방향이면 추세 지속 성공
                    # C1에서 예상 방향이 나왔다면, C2도 같은 방향이면 지속 성공
                    c2_is_success = (c2_color == expected_c1_direction)
                    
                    c2_data = {
                        "date": str(c2_idx),
                        "color": c2_color,
                        "return": round(c2_return, 2),
                        "is_success": c2_is_success,
                        "expected_direction": expected_c1_direction  # 디버깅용: 기대한 방향
                    }
            
            # 시그널 점수 계산
            score_data = calculate_signal_score(
                q['retracement_pct'],
                q['vol_ratio'],
                rsi_val
            )
            
            pattern_info = {
                "index": str(idx),
                "date": str(idx),
                "retracement_pct": q['retracement_pct'],
                "vol_ratio": q['vol_ratio'],
                "rsi": round(rsi_val, 2),
                **score_data
            }
            
            scored_patterns.append(pattern_info)
            
            # 차트 데이터 생성
            chart_data.append({
                "date": str(idx),
                "pattern_date": str(idx),
                "pattern_pos": pos,  # 하위 분석에서 재파싱 없이 바로 재사용
                "retracement": q['retracement_pct'],
                "vol_ratio": q['vol_ratio'],
                "rsi": round(rsi_val, 2),
                "score": score_data['score'],
                "confidence": score_data['confidence'],
                "c1": c1_data,
                "c2": c2_data,
                "profit_c1": c1_data['return'] if c1_data else None,
                "profit_c2": c2_data['return'] if c2_data else None,
                "is_success_c1": c1_data['is_success'] if c1_data else None,
                "is_success_c2": c2_data['is_success'] if c2_data else None,
                # ✅ 추가: 패턴 정보 (디버깅 및 분석용)
                "pattern_last_direction": last_pattern_direction,
                "expected_c1_direction": expected_c1_direction,
                "c1_direction": c1_data['color'] if c1_data else None,
                "c2_direction": c2_data['color'] if c2_data else None
            })
            
            # 필터링된 인덱스 추가 (다음 봉)
            filtered_indices.append(c1_idx)
                
        except (KeyError, IndexError, ValueError, TypeError) as e:
            if DEBUG_MODE:
                logger.debug(f"Error processing pattern at {idx}: {e}")
            continue
    
    return filtered_indices, chart_data, scored_patterns


def _empty_complex_result(context: AnalysisContext, from_cache: bool) -> Dict[str, Any]:
    """빈 복합 패턴 결과"""
    return {
        "success": False,
        "error": "복합 패턴이 비어있습니다",
        "message": "1차/2차 조건을 모두 설정해주세요",
        "mode": "complex",
        "from_cache": from_cache
    }


def _no_match_complex_result(context: AnalysisContext, complex_pattern: List[int], from_cache: bool) -> Dict[str, Any]:
    """패턴 매칭 실패 결과"""
    return {
        "success": False,
        "error": "패턴 매칭 실패",
        "message": f"{complex_pattern} 패턴을 찾을 수 없습니다",
        "suggestions": [
            "패턴을 단순화해보세요",
            "다른 타임프레임을 시도해보세요"
        ],
        "mode": "complex",
        "pattern": complex_pattern,
        "from_cache": from_cache
    }
