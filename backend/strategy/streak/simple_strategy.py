"""Simple Mode 전략 (N-연속 양봉/음봉 분석)"""

import pandas as pd
from typing import Dict, Any, Optional
import logging
import traceback

from strategy.context import AnalysisContext
from strategy.streak.common import (
    normalize_indices,
    extract_c1_indices,
    wilson_confidence_interval,
    calculate_binomial_pvalue,
    trimmed_stats,
    analyze_interval_statistics,
    calculate_intraday_distribution,
    calculate_weekly_distribution,
    load_data,
    calculate_indicators,
    safe_float,
    safe_round,
    sanitize_for_json,
    RSI_BINS,
    DISP_BINS,
    CONFIDENCE_LEVEL,
    RSI_OVERBOUGHT,
    DEBUG_MODE,
)

logger = logging.getLogger(__name__)


def run_simple_analysis(df: pd.DataFrame, context: AnalysisContext, from_cache: bool = False) -> Dict[str, Any]:
    """
    Simple Mode 분석 실행
    
    Args:
        df: 준비된 DataFrame (prepare_dataframe으로 처리됨)
        context: 분석 컨텍스트
        from_cache: 캐시 사용 여부
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        n = context.n_streak
        is_bullish = context.direction == "green"
        
        # 1. 패턴 매칭
        # 패턴 완성 시점: n번째 연속 봉이 끝난 시점
        # 즉, 현재 위치에서 과거 n개 봉이 모두 target_bit==True이고,
        # 현재 봉도 target_bit==True여야 함 (패턴 완성 시점이므로)
        if DEBUG_MODE:
            logger.debug(f"[Simple Mode] Total rows: {len(df)}")
            logger.debug(f"[Simple Mode] Looking for: {n} consecutive {'green' if is_bullish else 'red'} candles")
        
        condition = pd.Series([True] * len(df), index=df.index)
        # 현재 봉도 target_bit==True여야 함 (패턴 완성 시점 = n번째 연속 봉)
        condition &= (df['target_bit'] == True)
        # 과거 n-1개 봉이 모두 target_bit==True여야 함 (현재 포함 총 n개)
        for i in range(1, n):
            condition &= (df['target_bit'].shift(i) == True)
            if DEBUG_MODE:
                logger.debug(f"[Simple Mode] After shift({i}): {condition.sum()} matches")
        
        target_indices_raw = df[condition].index.tolist()
        # normalize_indices가 이미 인덱스 정규화 및 유효성 검증을 수행
        valid_indices = normalize_indices(target_indices_raw, df)
        
        if len(valid_indices) == 0:
            return _empty_simple_result(context, from_cache)
        
        # 2. 몸통 총합 필터 적용 (선택적)
        if context.min_total_body_pct is not None and context.min_total_body_pct > 0:
            filtered_indices = []
            for idx in valid_indices:
                try:
                    pos = df.index.get_loc(idx)
                    # 과거 n개 봉의 몸통 총합 계산 (현재 포함)
                    total_body_pct = 0.0
                    for i in range(n):
                        if pos - i >= 0:
                            body_val = df.iloc[pos - i]['body_pct']
                            if pd.notna(body_val):
                                total_body_pct += body_val
                    
                    # 총합이 임계값 이상인 경우만 포함
                    if total_body_pct >= context.min_total_body_pct:
                        filtered_indices.append(idx)
                except (KeyError, IndexError, TypeError):
                    continue
            
            valid_indices = filtered_indices
            
            if DEBUG_MODE:
                logger.debug(f"[Simple Mode] 몸통 총합 필터 적용: {len(target_indices_raw)}개 → {len(valid_indices)}개 (최소 {context.min_total_body_pct}% 이상)")
        
        if len(valid_indices) == 0:
            return _empty_simple_result(context, from_cache)
        
        # 3. 중복 제거 후 target_cases 추출 (normalize_indices는 유효성만 검증, 중복 제거는 여기서 수행)
        target_indices_unique = pd.Index(valid_indices).drop_duplicates()
        target_cases = df.loc[target_indices_unique].copy()
        total_cases = len(target_cases)
        
        if total_cases == 0:
            return _empty_simple_result(context, from_cache)
        
        # 3. 기술적 지표 계산 (RSI, ATR, Disparity 등)
        df = calculate_indicators(df)
        
        # 4. 메인 통계 계산 (C1 기준으로 정정)
        # target_cases(패턴 완성 시점)의 다음 봉(C1)이 양봉/음봉인지 체크
        df['next_is_green'] = df['is_green'].shift(-1)
        
        # C1이 양봉인 경우: target_cases의 다음 봉(C1)이 양봉인 target_cases 인덱스들
        c1_green_mask = df.loc[target_cases.index, 'next_is_green'] == True
        c1_red_mask = df.loc[target_cases.index, 'next_is_green'] == False
        
        # C1 기준 continuation/reversal 계산
        # direction == "green": C1이 양봉이면 continuation, 음봉이면 reversal
        # direction == "red": C1이 음봉이면continuation, 양봉이면 reversal
        is_bullish_pattern = (context.direction == "green")
        
        if is_bullish_pattern:
            # 양봉 패턴: C1이 양봉이면 continuation
            continuation_count = int(c1_green_mask.sum())
            reversal_count = int(c1_red_mask.sum())
        else:
            # 음봉 패턴: C1이 음봉이면 continuation
            continuation_count = int(c1_red_mask.sum())
            reversal_count = int(c1_green_mask.sum())
        
        continuation_rate = float(continuation_count / total_cases * 100) if total_cases > 0 else 0
        reversal_rate = 100 - continuation_rate
        
        continuation_ci = wilson_confidence_interval(continuation_count, total_cases)
        c1_pvalue = calculate_binomial_pvalue(continuation_count, total_cases, 0.5)
        
        # 평균 body % (C1 기준)
        # C1 인덱스 추출 (direction에 따라 필터링)
        c1_continuation_indices = extract_c1_indices(df, target_cases.index, filter_green=is_bullish_pattern)
        c1_reversal_indices = extract_c1_indices(df, target_cases.index, filter_green=not is_bullish_pattern)
        
        # 지속 케이스 통계
        if len(c1_continuation_indices) > 0:
            continuations = df.loc[c1_continuation_indices]
            avg_body_pct = float(continuations['body_pct'].mean())
            max_body_pct = float(continuations['body_pct'].max())
            min_body_pct = float(continuations['body_pct'].min())
        else:
            avg_body_pct = 0
            max_body_pct = None
            min_body_pct = None
        
        # 반전 케이스 통계
        # 반전 케이스는 패턴과 반대 방향이므로, body_pct를 재계산해야 함
        if len(c1_reversal_indices) > 0:
            reversals = df.loc[c1_reversal_indices]
            # 반전 케이스는 패턴과 반대 방향이므로, body_pct를 절댓값으로 변환
            # direction="red"일 때 반전은 양봉이므로, 양봉 기준으로 재계산
            if is_bullish_pattern:
                # 양봉 패턴의 반전은 음봉이므로, 음봉 기준 body_pct 사용
                reversal_body_pct = reversals['body_pct']
            else:
                # 음봉 패턴의 반전은 양봉이므로, 양봉 기준으로 재계산
                reversal_body_pct = (reversals['close'] - reversals['open']) / reversals['open'] * 100
            
            avg_reversal_body_pct = float(reversal_body_pct.mean())
            max_reversal_body_pct = float(reversal_body_pct.max())
            min_reversal_body_pct = float(reversal_body_pct.min())
        else:
            avg_reversal_body_pct = None
            max_reversal_body_pct = None
            min_reversal_body_pct = None
        
        # C2 예측 (C1 결과 기반)
        
        c1_green_cases = target_cases[c1_green_mask]
        c1_red_cases = target_cases[c1_red_mask]
        
        c1_green_count = len(c1_green_cases)
        c1_red_count = len(c1_red_cases)
        
        c2_after_c1_green_rate = None
        c2_after_c1_red_rate = None
        c2_after_c1_green_ci = None
        c2_after_c1_red_ci = None
        
        # C1이 양봉인 경우, C1의 다음 봉(C2) 체크
        if c1_green_count > 0:
            # C1의 인덱스 추출 (target_cases의 다음 봉, 양봉만)
            c1_green_indices = extract_c1_indices(df, c1_green_cases.index, filter_green=True)
            
            if len(c1_green_indices) > 0:
                # C1의 다음 봉(C2)이 양봉인지 체크
                c2_vals = df.loc[c1_green_indices, 'next_is_green'].dropna()
                if len(c2_vals) > 0:
                    c2_green_success = int(c2_vals.sum())
                    c2_after_c1_green_rate = float(c2_vals.mean() * 100)
                    c2_after_c1_green_ci = wilson_confidence_interval(c2_green_success, len(c2_vals))
        
        # C1이 음봉인 경우, C1의 다음 봉(C2) 체크
        if c1_red_count > 0:
            # C1의 인덱스 추출 (target_cases의 다음 봉, 음봉만)
            c1_red_indices = extract_c1_indices(df, c1_red_cases.index, filter_green=False)
            
            if len(c1_red_indices) > 0:
                # C1의 다음 봉(C2)이 양봉인지 체크
                c2_vals = df.loc[c1_red_indices, 'next_is_green'].dropna()
                if len(c2_vals) > 0:
                    c2_red_success = int(c2_vals.sum())
                    c2_after_c1_red_rate = float(c2_vals.mean() * 100)
                    c2_after_c1_red_ci = wilson_confidence_interval(c2_red_success, len(c2_vals))
        
        # 5. Comparative Report (direction에 따라 동적 패턴)
        comparative_report = _calculate_comparative_report(df, n, context.direction)
        
        # 6. 변동성 통계
        target_cases['rsi'] = df.loc[target_cases.index, 'rsi']
        target_cases['disparity'] = df.loc[target_cases.index, 'disparity']
        target_cases['atr_pct'] = df.loc[target_cases.index, 'atr_pct']
        
        target_cases['max_dip'] = (target_cases['open'] - target_cases['low']) / target_cases['open'] * 100
        target_cases['max_rise'] = (target_cases['high'] - target_cases['open']) / target_cases['open'] * 100
        
        dip_stats = trimmed_stats(target_cases['max_dip'])
        rise_stats = trimmed_stats(target_cases['max_rise'])
        atr_stats = trimmed_stats(target_cases['atr_pct'].dropna())
        
        avg_dip = dip_stats['mean']
        std_dip = dip_stats['std']
        avg_rise = rise_stats['mean']
        avg_atr_pct = atr_stats['mean']
        
        # Z-Score 계산 (safe_float로 NaN/Inf 방지)
        z_score_dip = None
        current_dip = None
        if len(target_cases) > 0 and std_dip is not None and std_dip > 0:
            current_dip = safe_float(target_cases['max_dip'].iloc[-1])
            if current_dip is not None and avg_dip is not None:
                z_score_dip = safe_round((current_dip - avg_dip) / std_dip, 2)
        
        z_score_interpretation = None
        if z_score_dip is not None:
            if abs(z_score_dip) < 1:
                z_score_interpretation = "normal"
            elif abs(z_score_dip) < 2:
                z_score_interpretation = "unusual"
            else:
                z_score_interpretation = "extreme"
        
        volatility_stats = {
            "avg_dip": safe_round(avg_dip, 2),
            "avg_rise": safe_round(avg_rise, 2),
            "std_dip": safe_round(std_dip, 2),
            "avg_atr_pct": safe_round(avg_atr_pct, 2),
            "practical_max_dip": safe_round(dip_stats['max'], 2),
            "extreme_max_dip": safe_round(dip_stats.get('original_max', 0), 2),
            "current_dip": safe_round(current_dip, 2),
            "z_score_dip": z_score_dip,
            "z_score_interpretation": z_score_interpretation,
            "is_trimmed": dip_stats['trimmed'],
            "sample_count": len(target_cases),
        }
        
        # 7. Short Signal (양봉 연속일 때만)
        short_signal = None
        if context.direction == "green":
            short_signal = _calculate_short_signal(df, n, avg_rise)
        
        # 8. RSI/Disparity 구간별 분석
        # ✅ 수정: 패턴 완성 시점의 전일 지표를 기준으로, 다음 봉(C1)이 양봉인지 분석
        target_cases['prev_rsi'] = df['rsi'].shift(1).loc[target_cases.index]
        # next_is_green: 패턴 완성 후 다음 봉(C1)이 양봉인지 여부
        target_cases['next_is_green'] = df.loc[target_cases.index, 'next_is_green']
        rsi_by_interval, high_prob_rsi = analyze_interval_statistics(
            target_cases['prev_rsi'],
            target_cases['next_is_green'],
            RSI_BINS,
            CONFIDENCE_LEVEL
        )
        
        target_cases['prev_disparity'] = df['disparity'].shift(1).loc[target_cases.index]
        disp_by_interval, high_prob_disp = analyze_interval_statistics(
            target_cases['prev_disparity'],
            target_cases['next_is_green'],
            DISP_BINS,
            CONFIDENCE_LEVEL
        )
        
        # 9. NY Trading Guide (시간대별 저점/고점 분석 - 1d/3d만)
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
                # target_cases(패턴 완성 시점)의 다음 봉(C1)이 양봉인 경우, C1의 날짜 추출
                c1_green_dates = extract_c1_indices(df, target_cases.index, filter_green=True)
                
                if len(c1_green_dates) > 0:
                    intraday_result = calculate_intraday_distribution(
                        pattern_result_dates=c1_green_dates,  # C1의 날짜 전달
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
                        logger.info(f"[Simple Mode] 시간대별 분석 완료: {len(c1_green_dates)}개 C1 양봉 날짜 분석 (패턴 완성 시점: {len(target_cases)}개)")
            except Exception as e:
                logger.warning(f"[Simple Mode] 시간대별 분석 실패: {e}")
                import traceback
                logger.warning(traceback.format_exc())
                # 기본값 유지
        
        # 주봉(1w) 타임프레임인 경우: 요일별 저점/고점 발생 확률 계산
        elif context.interval == '1w':
            try:
                # 일봉 데이터 로드
                df_daily, _ = load_data(context.coin, '1d')
                if df_daily is not None and not df_daily.empty:
                    weekly_result = calculate_weekly_distribution(
                        df=df_daily,
                        interval=context.interval,
                        timezone_offset=context.timezone_offset
                    )
                    
                    # 요일별 확률로 업데이트
                    ny_trading_guide.update({
                        "entry_window": "요일별 저점/고점 확률 분석",
                        "peak_window": "주봉 기준",
                        "daily_low_probability": weekly_result.get("daily_low_probability", {}),
                        "daily_high_probability": weekly_result.get("daily_high_probability", {}),
                        "hourly_low_probability": {},  # 주봉에서는 사용 안함
                        "hourly_high_probability": {},
                        "note": weekly_result.get("note", "주봉 요일별 분석")
                    })
                    
                    if DEBUG_MODE:
                        logger.info(f"[Simple Mode] 요일별 분석 완료")
            except Exception as e:
                logger.warning(f"[Simple Mode] 요일별 분석 실패: {e}")
                import traceback
                logger.warning(traceback.format_exc())
        
        # 10. 결과 반환 (JSON 직렬화 전 NaN/Inf 정제)
        result = {
            "success": True,
            "mode": "simple",
            "filter_status": None,
            "total_cases": total_cases,
            "continuation_rate": safe_round(continuation_rate, 2),
            "reversal_rate": safe_round(reversal_rate, 2),
            "continuation_count": continuation_count,
            "reversal_count": reversal_count,
            "avg_body_pct": safe_round(avg_body_pct, 2),
            "continuation_stats": {
                "avg_body_pct": safe_round(avg_body_pct, 2) if avg_body_pct else None,
                "max_body_pct": safe_round(max_body_pct, 2) if max_body_pct is not None else None,
                "min_body_pct": safe_round(min_body_pct, 2) if min_body_pct is not None else None,
                "count": continuation_count,
            },
            "reversal_stats": {
                "avg_body_pct": safe_round(avg_reversal_body_pct, 2) if avg_reversal_body_pct is not None else None,
                "max_body_pct": safe_round(max_reversal_body_pct, 2) if max_reversal_body_pct is not None else None,
                "min_body_pct": safe_round(min_reversal_body_pct, 2) if min_reversal_body_pct is not None else None,
                "count": reversal_count,
            },
            "continuation_ci": continuation_ci,
            "c1_p_value": safe_round(c1_pvalue, 4),
            "c1_is_significant": bool(c1_pvalue < 0.05) if c1_pvalue is not None else False,
            "c2_after_c1_green_rate": safe_round(c2_after_c1_green_rate, 2),
            "c2_after_c1_red_rate": safe_round(c2_after_c1_red_rate, 2),
            "c2_after_c1_green_ci": c2_after_c1_green_ci,
            "c2_after_c1_red_ci": c2_after_c1_red_ci,
            "c1_green_count": c1_green_count,
            "c1_red_count": c1_red_count,
            "comparative_report": comparative_report,
            "short_signal": short_signal,
            "volatility_stats": volatility_stats,
            "rsi_by_interval": rsi_by_interval,
            "disp_by_interval": disp_by_interval,
            "high_prob_rsi_intervals": high_prob_rsi,
            "high_prob_disp_intervals": high_prob_disp,
            "complex_pattern_analysis": None,
            "ny_trading_guide": ny_trading_guide,
            "analysis_mode": {
                "type": "simple",
                "description": "Simple N-Streak",
                "parameters": {
                    "n_streak": n,
                    "direction": context.direction,
                }
            },
            "from_cache": from_cache,
            "coin": context.coin,
            "interval": context.interval,
            "n_streak": n,
            "direction": context.direction,
        }
        return sanitize_for_json(result)
        
    except Exception as e:
        logger.error(f"Error in run_simple_analysis: {e}\n{traceback.format_exc()}")
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc(),
            "mode": "simple"
        }


def _calculate_comparative_report(df: pd.DataFrame, n: int, direction: str) -> Optional[Dict[str, Any]]:
    """Comparative Report 계산 (direction에 따라 동적 패턴)
    
    - direction == 'green': nG + 1R 패턴 (n개 양봉 + 1개 음봉 후 다음 봉이 양봉인지)
    - direction == 'red': nR + 1G 패턴 (n개 음봉 + 1개 양봉 후 다음 봉이 음봉인지)
    """
    is_green_pattern = (direction == 'green')
    
    # 패턴 조건 구성
    streak_cond = pd.Series([True] * len(df), index=df.index)
    for i in range(2, n + 2):
        # direction에 따라 양봉 또는 음봉 연속 체크
        streak_cond &= (df['is_green'].shift(i) == is_green_pattern)
    
    # 반전 패턴 체크 (n개 연속 후 반대 방향 1개)
    reversal_pattern_cond = streak_cond & (df['is_green'].shift(1) == (not is_green_pattern))
    
    reversal_pattern_cases = df[reversal_pattern_cond].copy()
    
    # 성공/실패 케이스 정의
    # green 패턴: 다음 봉이 양봉이면 성공
    # red 패턴: 다음 봉이 음봉이면 성공
    if is_green_pattern:
        success_cases = reversal_pattern_cases[reversal_pattern_cases['is_green'] == True]
        failure_cases = reversal_pattern_cases[reversal_pattern_cases['is_green'] == False]
    else:
        success_cases = reversal_pattern_cases[reversal_pattern_cases['is_green'] == False]
        failure_cases = reversal_pattern_cases[reversal_pattern_cases['is_green'] == True]
    
    if len(reversal_pattern_cases) == 0:
        return None
    
    def safe_mean(series):
        vals = series.dropna()
        return float(vals.mean()) if len(vals) > 0 else None
    
    return {
        "pattern_total": len(reversal_pattern_cases),
        "success_count": len(success_cases),
        "failure_count": len(failure_cases),
        "success_rate": round(len(success_cases) / len(reversal_pattern_cases) * 100, 2) if len(reversal_pattern_cases) > 0 else None,
        "pattern_type": "nG + 1R" if is_green_pattern else "nR + 1G",
        "success": {
            "prev_rsi": round(safe_mean(success_cases['rsi'].shift(1)), 2) if len(success_cases) > 0 and safe_mean(success_cases['rsi'].shift(1)) else None,
            "prev_body_pct": round(safe_mean(success_cases['body_pct'].shift(1)), 2) if len(success_cases) > 0 and safe_mean(success_cases['body_pct'].shift(1)) else None,
            "prev_vol_change": round(safe_mean(success_cases['vol_change'].shift(1)), 2) if len(success_cases) > 0 and safe_mean(success_cases['vol_change'].shift(1)) else None,
            "prev_disparity": round(safe_mean(success_cases['disparity'].shift(1)), 2) if len(success_cases) > 0 and safe_mean(success_cases['disparity'].shift(1)) else None,
        },
        "failure": {
            "prev_rsi": round(safe_mean(failure_cases['rsi'].shift(1)), 2) if len(failure_cases) > 0 and safe_mean(failure_cases['rsi'].shift(1)) else None,
            "prev_body_pct": round(safe_mean(failure_cases['body_pct'].shift(1)), 2) if len(failure_cases) > 0 and safe_mean(failure_cases['body_pct'].shift(1)) else None,
            "prev_vol_change": round(safe_mean(failure_cases['vol_change'].shift(1)), 2) if len(failure_cases) > 0 and safe_mean(failure_cases['vol_change'].shift(1)) else None,
            "prev_disparity": round(safe_mean(failure_cases['disparity'].shift(1)), 2) if len(failure_cases) > 0 and safe_mean(failure_cases['disparity'].shift(1)) else None,
        },
    }


def _calculate_short_signal(df: pd.DataFrame, n: int, avg_rise: Optional[float]) -> Optional[Dict[str, Any]]:
    """Short Signal 계산 (양봉 연속일 때만)"""
    # N-연속 양봉 + 과매수 조건
    short_cond = pd.Series([True] * len(df), index=df.index)
    for i in range(1, n + 1):
        short_cond &= (df['is_green'].shift(i) == True)
    
    short_filter = short_cond & (df['rsi'].shift(1) >= RSI_OVERBOUGHT)
    short_targets = df[short_filter].copy()
    
    if len(short_targets) < 3:
        return None
    
    # 진입 타점 설정
    base_rise = avg_rise if avg_rise is not None else 0.5
    target_entry_rise = max(0.1, base_rise * 0.6)
    
    # 체결 시뮬레이션
    short_targets['entry_threshold'] = short_targets['open'] * (1 + target_entry_rise / 100)
    short_targets['is_filled'] = short_targets['high'] >= short_targets['entry_threshold']
    
    total_signals = len(short_targets)
    filled_cases = short_targets[short_targets['is_filled']].copy()
    unfilled_cases = short_targets[~short_targets['is_filled']].copy()
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
            "unfilled_cases": len(unfilled_cases),
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
            "note": "Bias Removed: All signals tracked, only filled cases analyzed"
        }
    
    return None


def _empty_simple_result(context: AnalysisContext, from_cache: bool) -> Dict[str, Any]:
    """빈 결과 반환 (패턴을 찾을 수 없을 때)"""
    return {
        "success": True,
        "mode": "simple",
        "filter_status": None,
        "total_cases": 0,
        "continuation_rate": None,
        "reversal_rate": None,
        "avg_body_pct": None,
        "c2_after_c1_green_rate": None,
        "c2_after_c1_red_rate": None,
        "c1_green_count": 0,
        "c1_red_count": 0,
        "comparative_report": None,
        "volatility_stats": None,
        "complex_pattern_analysis": None,
        "ny_trading_guide": {
            "entry_window": "03:00 - 07:00 EST (NY Pre-market)",
            "peak_window": "15:00 - 19:00 EST (NY Close)",
            "average_lower_shadow": "-1.39%",
            "average_upper_shadow": "0.97%",
            "low_window": "04:00 - 08:00 EST",
            "avg_volatility": "2.5%",
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": "No pattern matches found"
        },
        "analysis_mode": {
            "type": "simple",
            "description": "Simple N-Streak",
            "parameters": {
                "n_streak": context.n_streak,
                "direction": context.direction,
            }
        },
        "from_cache": from_cache,
        "coin": context.coin,
        "interval": context.interval,
        "n_streak": context.n_streak,
        "direction": context.direction,
    }
