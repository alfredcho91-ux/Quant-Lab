"""Complex Mode 전략 (복합 패턴 분석)"""

import pandas as pd
from typing import Dict, Any, Optional, List
import logging
import traceback

from strategy.context import AnalysisContext
from strategy.streak.common import (
    normalize_single_index,
    extract_c1_indices,
    extract_c1_dates_from_chart_data,
    find_complex_pattern,
    analyze_pullback_quality,
    calculate_signal_score,
    safe_get_rsi,
    wilson_confidence_interval,
    analyze_interval_statistics,
    trimmed_stats,
    calculate_intraday_distribution,
    get_or_calculate_indicators,
    safe_float,
    safe_round,
    sanitize_for_json,
    RSI_BINS,
    RETRACEMENT_BINS,
    CONFIDENCE_LEVEL,
    RSI_OVERBOUGHT,
    DEFAULT_RSI,
    DEBUG_MODE,
)

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
        
        # 2. 패턴 매칭
        complex_pattern = context.complex_pattern
        if not complex_pattern or len(complex_pattern) == 0:
            return _empty_complex_result(context, from_cache)
        
        matched_patterns = find_complex_pattern(df, complex_pattern)
        
        if len(matched_patterns) == 0:
            return _no_match_complex_result(context, complex_pattern, from_cache)
        
        # 3. 품질 분석
        # 성능 최적화: sum(1 for ...) 대신 직접 카운팅
        rise_len = complex_pattern.count(1)
        drop_len = complex_pattern.count(-1)
        
        quality_results = analyze_pullback_quality(
            df, matched_patterns.index,
            rise_len=rise_len,
            drop_len=drop_len
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
        
        # 4. 필터 적용 및 차트 데이터 생성
        filtered_indices, chart_data, scored_patterns = _filter_and_score_patterns(
            df, quality_results, context
        )
        
        # 5. 필터 상태 정보
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
        
        # 6. 복합 패턴 분석 (차트 데이터 기반)
        complex_pattern_analysis = _calculate_complex_analysis(
            df, complex_pattern, matched_patterns, scored_patterns, chart_data, context
        )
        
        # 7. 결과 반환 (JSON 직렬화 전 NaN/Inf 정제)
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
            "high_prob_rsi_intervals": complex_pattern_analysis.get("high_prob_rsi_intervals", {}),
            "complex_pattern_analysis": complex_pattern_analysis,
            "ny_trading_guide": complex_pattern_analysis.get("ny_trading_guide", {
                "entry_window": "03:00 - 07:00 EST (NY Pre-market)",
                "peak_window": "15:00 - 19:00 EST (NY Close)",
                "average_lower_shadow": "-1.39%",
                "average_upper_shadow": "0.97%",
                "low_window": "04:00 - 08:00 EST",
                "avg_volatility": "2.5%",
                "hourly_low_probability": {},
                "hourly_high_probability": {},
                "note": "뉴욕 시간대 기준 진입/피크 윈도우"
            }),
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
    context: AnalysisContext
) -> tuple[List[Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """필터 적용 및 시그널 점수 계산"""
    filtered_indices = []
    chart_data = []
    scored_patterns = []
    
    # 패턴의 마지막 방향 확인 (반등/조정 기대 방향 결정)
    complex_pattern = context.complex_pattern
    if not complex_pattern or len(complex_pattern) == 0:
        return filtered_indices, chart_data, scored_patterns
    
    # 마지막 봉의 방향 (1: 양봉, -1: 음봉)
    last_pattern_direction = complex_pattern[-1]
    
    # 반등/조정 성공 조건:
    # - 패턴이 음봉(-1)으로 끝나면 → 조정 후 반등 기대 → C1은 양봉(1)이어야 반등 성공 (롱 성공)
    # - 패턴이 양봉(1)으로 끝나면 → 강한 상승 후 조정 기대 → C1은 음봉(-1)이어야 조정 성공 (숏 성공)
    expected_c1_direction = -last_pattern_direction
    
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
            if pos + 1 >= len(df):
                continue
            
            c1_idx = df.index[pos + 1]
            c1_data = None
            c2_data = None
            
            if pos + 1 < len(df):
                c1_row = df.loc[c1_idx]
                c1_color = 1 if c1_row['close'] > c1_row['open'] else -1
                c1_return = ((c1_row['close'] / df.loc[idx, 'close']) - 1) * 100
                
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
                if pos + 2 < len(df):
                    c2_idx = df.index[pos + 2]
                    c2_row = df.loc[c2_idx]
                    c2_color = 1 if c2_row['close'] > c2_row['open'] else -1
                    c2_return = ((c2_row['close'] / c1_row['close']) - 1) * 100
                    
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
            if isinstance(c1_idx, str):
                c1_idx_converted = pd.to_datetime(c1_idx)
            else:
                c1_idx_converted = c1_idx
            if c1_idx_converted in df.index:
                filtered_indices.append(c1_idx_converted)
                
        except (KeyError, IndexError, ValueError, TypeError) as e:
            if DEBUG_MODE:
                logger.debug(f"Error processing pattern at {idx}: {e}")
            continue
    
    return filtered_indices, chart_data, scored_patterns


def _calculate_complex_analysis(
    df: pd.DataFrame,
    complex_pattern: List[int],
    matched_patterns: pd.DataFrame,
    scored_patterns: List[Dict[str, Any]],
    chart_data: List[Dict[str, Any]],
    context: AnalysisContext
) -> Dict[str, Any]:
    """복합 패턴 분석 결과 계산"""
    
    # 기본 통계
    # 성능 최적화: 한 번의 반복으로 모든 통계 계산
    if scored_patterns:
        scores = [p['score'] for p in scored_patterns]
        avg_score = sum(scores) / len(scores)
        # 성능 최적화: sum(1 for ...) 대신 직접 카운팅
        high_confidence_count = len([p for p in scored_patterns if p.get('confidence') == 'high'])
    else:
        avg_score = 0
        high_confidence_count = 0
    
    # C1/C2 방향별 통계 계산 (양봉/음봉 비율)
    # 내부적으로는 패턴 방향 기반 성공 기준 사용 (코드 명확성)
    # 표기는 양봉/음봉 비율로 제공 (사용자가 롱/숏 전략 직접 해석)
    c1_green_count = 0
    c1_red_count = 0
    c1_total_count = 0
    c2_green_count = 0
    c2_red_count = 0
    c2_total_count = 0
    profit_c1_sum = 0.0
    profit_c2_sum = 0.0
    
    # 내부 로직용: 패턴 방향 기반 성공 기준 (코드 명확성을 위해 유지)
    c1_success_count = 0  # 패턴 방향 기반 성공 (내부 계산용)
    c2_success_count = 0  # 패턴 방향 기반 성공 (내부 계산용)
    
    for c in chart_data:
        # C1 통계
        c1_direction = c.get('c1_direction')
        if c1_direction is not None:
            c1_total_count += 1
            if c1_direction == 1:
                c1_green_count += 1
            elif c1_direction == -1:
                c1_red_count += 1
            
            # 내부 로직: 패턴 방향 기반 성공 기준 (코드 명확성)
            is_success_c1 = c.get('is_success_c1')
            if is_success_c1:
                c1_success_count += 1
            
            profit_c1 = c.get('profit_c1')
            if profit_c1 is not None:
                profit_c1_sum += profit_c1
        
        # C2 통계
        c2_direction = c.get('c2_direction')
        if c2_direction is not None:
            c2_total_count += 1
            if c2_direction == 1:
                c2_green_count += 1
            elif c2_direction == -1:
                c2_red_count += 1
            
            # 내부 로직: 패턴 방향 기반 성공 기준 (코드 명확성)
            is_success_c2 = c.get('is_success_c2')
            if is_success_c2:
                c2_success_count += 1
            
            profit_c2 = c.get('profit_c2')
            if profit_c2 is not None:
                profit_c2_sum += profit_c2
    
    # 양봉/음봉 비율 계산 (표시용)
    c1_green_rate = (c1_green_count / c1_total_count * 100) if c1_total_count > 0 else 0
    c1_red_rate = (c1_red_count / c1_total_count * 100) if c1_total_count > 0 else 0
    c1_green_rate_ci = wilson_confidence_interval(c1_green_count, c1_total_count) if c1_total_count > 0 else None
    c1_red_rate_ci = wilson_confidence_interval(c1_red_count, c1_total_count) if c1_total_count > 0 else None
    
    c2_green_rate = (c2_green_count / c2_total_count * 100) if c2_total_count > 0 else 0
    c2_red_rate = (c2_red_count / c2_total_count * 100) if c2_total_count > 0 else 0
    c2_green_rate_ci = wilson_confidence_interval(c2_green_count, c2_total_count) if c2_total_count > 0 else None
    c2_red_rate_ci = wilson_confidence_interval(c2_red_count, c2_total_count) if c2_total_count > 0 else None
    
    # 내부 로직용 승률 (패턴 방향 기반, 디버깅/검증용)
    c1_win_rate = (c1_success_count / c1_total_count * 100) if c1_total_count > 0 else 0
    c1_win_rate_ci = wilson_confidence_interval(c1_success_count, c1_total_count) if c1_total_count > 0 else None
    c2_win_rate = (c2_success_count / c2_total_count * 100) if c2_total_count > 0 else 0
    c2_win_rate_ci = wilson_confidence_interval(c2_success_count, c2_total_count) if c2_total_count > 0 else None
    
    # 평균 수익률
    avg_profit_c1 = profit_c1_sum / c1_total_count if c1_total_count > 0 else 0
    avg_profit_c2 = profit_c2_sum / c2_total_count if c2_total_count > 0 else 0
    
    # 변동성 통계
    volatility_stats = _calculate_volatility_stats(df, chart_data)
    
    # Short Signal
    short_signal = _calculate_short_signal(df, complex_pattern, chart_data)
    
    # RSI/Retracement 구간 분석
    rsi_by_interval, high_prob_rsi, retracement_by_interval, high_prob_retracement = _calculate_interval_analysis(
        df, chart_data
    )
    
    # Comparative Report
    comparative_report = _calculate_comparative_report(chart_data)
    
    # NY Trading Guide (시간대별 저점/고점 분석 - 1d/3d만)
    ny_trading_guide = {
        "entry_window": "03:00 - 07:00 EST (NY Pre-market)",
        "peak_window": "15:00 - 19:00 EST (NY Close)",
        "average_lower_shadow": "-1.39%",
        "average_upper_shadow": "0.97%",
        "low_window": "04:00 - 08:00 EST",
        "avg_volatility": "2.5%",
        "hourly_low_probability": {},
        "hourly_high_probability": {},
        "note": "뉴욕 시간대 기준 진입/피크 윈도우"
    }
    
    # 1d/3d 타임프레임인 경우: 결과 도출일(C1, 패턴 다음 봉)이 양봉인 경우의 4시간봉 분석
    if context.interval in ['1d', '3d']:
        try:
            # ✅ 개선: chart_data에서 필터링된 패턴의 C1 양봉 날짜 추출 (유틸리티 함수 사용)
            # matched_patterns.index 대신 chart_data 사용하여 필터링된 패턴만 포함
            c1_green_dates = extract_c1_dates_from_chart_data(chart_data, filter_green=True)
            
            if len(c1_green_dates) > 0:
                intraday_result = calculate_intraday_distribution(
                    pattern_result_dates=c1_green_dates,
                    interval=context.interval,
                    coin=context.coin,
                    timezone_offset=context.timezone_offset
                )
                
                # 계산된 값으로 업데이트
                ny_trading_guide.update({
                    "low_window": intraday_result.get("low_window"),
                    "avg_volatility": intraday_result.get("avg_volatility"),
                    "hourly_low_probability": intraday_result.get("hourly_low_probability", {}),
                    "hourly_high_probability": intraday_result.get("hourly_high_probability", {}),
                    "note": intraday_result.get("note", "뉴욕 시간대 기준 진입/피크 윈도우")
                })
                
                if DEBUG_MODE:
                    logger.info(
                        f"[Complex Mode] 시간대별 분석 완료: {len(c1_green_dates)}개 C1 양봉 날짜 분석 "
                        f"(필터링된 패턴: {len(chart_data)}개, 전체 매칭: {len(matched_patterns)}개)"
                    )
        except Exception as e:
            logger.warning(f"[Complex Mode] 시간대별 분석 실패: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            # 기본값 유지
    
    return {
        "pattern": complex_pattern,
        "total_matches": len(matched_patterns),
        "analyzed_count": len(scored_patterns),
        "filtered_count": len(chart_data),
        "avg_score": round(avg_score, 2),
        "high_confidence_count": high_confidence_count,
        "high_confidence_rate": round(high_confidence_count / len(scored_patterns) * 100, 2) if scored_patterns else 0,
        "patterns": scored_patterns[:10],
        "ny_trading_guide": ny_trading_guide,
        "chart_data": chart_data,
        "summary": {
            "c1_analysis": {
                # 표시용: 양봉/음봉 비율 (사용자가 롱/숏 전략 직접 해석)
                "green_rate": round(c1_green_rate, 2),
                "red_rate": round(c1_red_rate, 2),
                "green_confidence_interval": [c1_green_rate_ci['ci_lower'], c1_green_rate_ci['ci_upper']] if c1_green_rate_ci else None,
                "red_confidence_interval": [c1_red_rate_ci['ci_lower'], c1_red_rate_ci['ci_upper']] if c1_red_rate_ci else None,
                "green_count": c1_green_count,
                "red_count": c1_red_count,
                "total_count": c1_total_count,
                "avg_return": round(avg_profit_c1, 2),
                # 내부 로직용: 패턴 방향 기반 승률 (디버깅/검증용, 선택적 표시)
                "pattern_based_win_rate": round(c1_win_rate, 2) if DEBUG_MODE else None,
                "pattern_based_confidence_interval": [c1_win_rate_ci['ci_lower'], c1_win_rate_ci['ci_upper']] if (c1_win_rate_ci and DEBUG_MODE) else None
            },
            "c2_analysis": {
                # 표시용: 양봉/음봉 비율 (사용자가 롱/숏 전략 직접 해석)
                "green_rate": round(c2_green_rate, 2),
                "red_rate": round(c2_red_rate, 2),
                "green_confidence_interval": [c2_green_rate_ci['ci_lower'], c2_green_rate_ci['ci_upper']] if c2_green_rate_ci else None,
                "red_confidence_interval": [c2_red_rate_ci['ci_lower'], c2_red_rate_ci['ci_upper']] if c2_red_rate_ci else None,
                "green_count": c2_green_count,
                "red_count": c2_red_count,
                "total_count": c2_total_count,
                "avg_return": round(avg_profit_c2, 2),
                # 내부 로직용: 패턴 방향 기반 승률 (디버깅/검증용, 선택적 표시)
                "pattern_based_win_rate": round(c2_win_rate, 2) if DEBUG_MODE else None,
                "pattern_based_confidence_interval": [c2_win_rate_ci['ci_lower'], c2_win_rate_ci['ci_upper']] if (c2_win_rate_ci and DEBUG_MODE) else None
            }
        },
        "filters_applied": {
            "rsi_threshold": context.rsi_threshold
        },
        "short_signal": short_signal,
        "volatility_stats": volatility_stats,
        "rsi_by_interval": rsi_by_interval,
        "retracement_by_interval": retracement_by_interval,
        "high_prob_rsi_intervals": high_prob_rsi,
        "high_prob_retracement_intervals": high_prob_retracement,
        "comparative_report": comparative_report
    }


def _calculate_volatility_stats(df: pd.DataFrame, chart_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """변동성 통계 계산"""
    if len(chart_data) == 0:
        return None
    
    # 패턴 인덱스 추출
    pattern_positions = []
    for c in chart_data:
        pattern_date_str = c.get('pattern_date')
        if not pattern_date_str:
            continue
        
        try:
            pattern_date_ts = pd.to_datetime(pattern_date_str, errors='coerce')
            if pd.isna(pattern_date_ts) or pattern_date_ts not in df.index:
                continue
            
            pos = df.index.get_loc(pattern_date_ts)
            pattern_positions.append(pos)
        except (ValueError, TypeError, KeyError, IndexError, pd.errors.ParserError):
            continue
    
    if len(pattern_positions) == 0:
        return None
    
    # C1 데이터 추출
    c1_cases = []
    for pos in pattern_positions:
        if pos + 1 < len(df):
            c1_idx = df.index[pos + 1]
            c1_row = df.loc[c1_idx]
            c1_cases.append({
                'open': c1_row['open'],
                'high': c1_row['high'],
                'low': c1_row['low'],
                'close': c1_row['close'],
                'atr_pct': c1_row.get('atr_pct', 0)
            })
    
    if len(c1_cases) == 0:
        return None
    
    c1_df = pd.DataFrame(c1_cases)
    c1_df['max_dip'] = (c1_df['open'] - c1_df['low']) / c1_df['open'] * 100
    c1_df['max_rise'] = (c1_df['high'] - c1_df['open']) / c1_df['open'] * 100
    
    dip_stats = trimmed_stats(c1_df['max_dip'])
    rise_stats = trimmed_stats(c1_df['max_rise'])
    avg_atr = safe_float(c1_df['atr_pct'].mean()) if len(c1_df) > 0 else None
    
    return {
        "avg_dip": safe_round(dip_stats['mean'], 2),
        "avg_rise": safe_round(rise_stats['mean'], 2),
        "std_dip": safe_round(dip_stats['std'], 2),
        "avg_atr_pct": safe_round(avg_atr, 2),
        "practical_max_dip": safe_round(dip_stats['max'], 2),
        "extreme_max_dip": safe_round(dip_stats.get('original_max', 0), 2),
        "is_trimmed": dip_stats['trimmed'],
        "sample_count": len(c1_cases),
    }


def _calculate_short_signal(
    df: pd.DataFrame,
    complex_pattern: List[int],
    chart_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Short Signal 계산 (양봉으로 끝나는 경우)"""
    if len(complex_pattern) == 0 or complex_pattern[-1] != 1:
        return None
    
    # RSI >= RSI_OVERBOUGHT인 케이스 필터링
    short_candidates = []
    for c in chart_data:
        if c.get('rsi') and c['rsi'] >= RSI_OVERBOUGHT:
            pattern_date_str = c.get('pattern_date')
            if not pattern_date_str:
                continue
            
            try:
                pattern_date_ts = pd.to_datetime(pattern_date_str, errors='coerce')
                if pd.isna(pattern_date_ts) or pattern_date_ts not in df.index:
                    continue
                
                pattern_pos = df.index.get_loc(pattern_date_ts)
                if pattern_pos + 1 < len(df):
                    c1_idx = df.index[pattern_pos + 1]
                    c1_row = df.loc[c1_idx]
                    short_candidates.append({
                        'open': c1_row['open'],
                        'high': c1_row['high'],
                        'close': c1_row['close'],
                        'rsi': c['rsi']
                    })
            except (ValueError, TypeError, KeyError, IndexError, pd.errors.ParserError):
                continue
    
    if len(short_candidates) < 3:
        return None
    
    short_df = pd.DataFrame(short_candidates)
    short_df['max_rise'] = (short_df['high'] - short_df['open']) / short_df['open'] * 100
    avg_rise_short = float(short_df['max_rise'].mean())
    
    target_entry_rise = max(0.1, avg_rise_short * 0.6)
    short_df['entry_threshold'] = short_df['open'] * (1 + target_entry_rise / 100)
    short_df['is_filled'] = short_df['high'] >= short_df['entry_threshold']
    
    total_signals = len(short_df)
    filled_cases = short_df[short_df['is_filled']].copy()
    fill_rate = (len(filled_cases) / total_signals * 100) if total_signals > 0 else 0
    
    if len(filled_cases) > 0:
        filled_cases['is_win'] = filled_cases['close'] < filled_cases['entry_threshold']
        short_win_count = int(filled_cases['is_win'].sum())
        short_win_rate = (short_win_count / len(filled_cases)) * 100 if len(filled_cases) > 0 else 0
        
        filled_cases['pnl_pct'] = (filled_cases['entry_threshold'] - filled_cases['close']) / filled_cases['entry_threshold'] * 100
        wins = filled_cases[filled_cases['pnl_pct'] > 0]
        avg_profit = float(wins['pnl_pct'].mean()) if len(wins) > 0 else 0
        overall_win_rate = (short_win_count / total_signals * 100) if total_signals > 0 else 0
        
        reliability = "high" if fill_rate >= 70 else "medium" if fill_rate >= 50 else "low"
        bias_warning = fill_rate < 50
        
        return {
            "enabled": short_win_rate >= 60 and fill_rate >= 50,
            "total_signals": total_signals,
            "filled_cases": len(filled_cases),
            "unfilled_cases": len(short_df) - len(filled_cases),
            "fill_rate": round(fill_rate, 2),
            "win_count": short_win_count,
            "win_rate": round(short_win_rate, 2),
            "overall_win_rate": round(overall_win_rate, 2),
            "entry_rise_pct": round(target_entry_rise, 2),
            "take_profit_pct": round(avg_profit, 2),
            "stop_loss_pct": 2.0,
            "rsi_threshold": RSI_OVERBOUGHT,
            "reliability": reliability,
            "bias_warning": bias_warning,
            "note": "Complex Pattern Based: All signals tracked, only filled cases analyzed"
        }
    
    return None


def _calculate_interval_analysis(
    df: pd.DataFrame,
    chart_data: List[Dict[str, Any]]
) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """RSI/Retracement 구간 분석"""
    if len(chart_data) == 0:
        return {}, {}, {}, {}
    
    pattern_rsi_vals = []
    pattern_retracement_vals = []
    pattern_is_green_vals = []
    
    for c in chart_data:
        pattern_date_str = c.get('pattern_date')
        if not pattern_date_str:
            continue
        
        try:
            pattern_date_ts = pd.to_datetime(pattern_date_str, errors='coerce')
            if pd.isna(pattern_date_ts) or pattern_date_ts not in df.index:
                continue
            
            pos = df.index.get_loc(pattern_date_ts)
            if pos + 1 >= len(df):
                continue
            
            c1_idx = df.index[pos + 1]
            c1_row = df.loc[c1_idx]
            
            pattern_rsi = safe_get_rsi(df, pattern_date_ts, DEFAULT_RSI)
            pattern_retracement = c.get('retracement', 50)  # chart_data에서 retracement 가져오기
            
            pattern_rsi_vals.append(pattern_rsi)
            pattern_retracement_vals.append(pattern_retracement)
            pattern_is_green_vals.append(1 if c1_row['close'] > c1_row['open'] else 0)
            
        except (KeyError, IndexError, ValueError, TypeError):
            continue
    
    if len(pattern_rsi_vals) == 0:
        return {}, {}, {}, {}
    
    # RSI 구간 분석
    rsi_by_interval, high_prob_rsi = analyze_interval_statistics(
        pd.Series(pattern_rsi_vals),
        pd.Series(pattern_is_green_vals),
        RSI_BINS,
        CONFIDENCE_LEVEL
    )
    
    # Retracement 구간 분석
    retracement_by_interval, high_prob_retracement = analyze_interval_statistics(
        pd.Series(pattern_retracement_vals),
        pd.Series(pattern_is_green_vals),
        RETRACEMENT_BINS,
        CONFIDENCE_LEVEL
    )
    
    return rsi_by_interval, high_prob_rsi, retracement_by_interval, high_prob_retracement


def _calculate_comparative_report(chart_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Comparative Report 계산"""
    if len(chart_data) == 0:
        return None
    
    success_cases = [c for c in chart_data if c.get('is_success_c1') == True]
    failure_cases = [c for c in chart_data if c.get('is_success_c1') == False]
    
    if len(success_cases) == 0 and len(failure_cases) == 0:
        return None
    
    def safe_mean_metric(cases, metric_key):
        vals = [c.get(metric_key) for c in cases if c.get(metric_key) is not None]
        return round(float(sum(vals) / len(vals)), 2) if len(vals) > 0 else None
    
    return {
        "pattern_total": len(chart_data),
        "success_count": len(success_cases),
        "failure_count": len(failure_cases),
        "success_rate": round(len(success_cases) / len(chart_data) * 100, 2) if len(chart_data) > 0 else None,
        "success": {
            "prev_rsi": safe_mean_metric(success_cases, 'rsi'),
            "prev_body_pct": None,
            "prev_vol_change": safe_mean_metric(success_cases, 'vol_ratio'),
        },
        "failure": {
            "prev_rsi": safe_mean_metric(failure_cases, 'rsi'),
            "prev_body_pct": None,
            "prev_vol_change": safe_mean_metric(failure_cases, 'vol_ratio'),
        },
    }


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
