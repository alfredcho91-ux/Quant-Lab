// 연속 봉패턴 분석 API

import { api } from './config';
import type { ApiResponse } from './config';
import type { StreakAnalysisParams, StreakAnalysisResult } from '../types';

type StreakAnalysisApiPayload = Partial<StreakAnalysisResult>;

function hasCoreStreakFields(payload: StreakAnalysisApiPayload): payload is StreakAnalysisResult {
  return (
    typeof payload.total_cases === 'number' &&
    typeof payload.continuation_count === 'number' &&
    typeof payload.reversal_count === 'number' &&
    typeof payload.c1_green_count === 'number' &&
    typeof payload.c1_red_count === 'number' &&
    payload.comparative_report !== undefined &&
    payload.coin !== undefined &&
    payload.interval !== undefined &&
    payload.n_streak !== undefined &&
    payload.direction !== undefined
  );
}

function normalizePartialStreakPayload(
  payload: StreakAnalysisApiPayload,
  params: StreakAnalysisParams
): StreakAnalysisResult {
  return {
    mode: payload.mode,
    filter_status: payload.filter_status ?? null,
    total_cases: payload.total_cases ?? 0,
    continuation_rate: payload.continuation_rate ?? null,
    reversal_rate: payload.reversal_rate ?? null,
    continuation_count: payload.continuation_count ?? 0,
    reversal_count: payload.reversal_count ?? 0,
    avg_body_pct: payload.avg_body_pct ?? null,
    continuation_stats: payload.continuation_stats,
    reversal_stats: payload.reversal_stats,
    continuation_ci: payload.continuation_ci,
    c1_p_value: payload.c1_p_value,
    c1_is_significant: payload.c1_is_significant,
    c2_after_c1_green_rate: payload.c2_after_c1_green_rate ?? null,
    c2_after_c1_red_rate: payload.c2_after_c1_red_rate ?? null,
    c2_after_c1_green_ci: payload.c2_after_c1_green_ci,
    c2_after_c1_red_ci: payload.c2_after_c1_red_ci,
    c1_green_count: payload.c1_green_count ?? 0,
    c1_red_count: payload.c1_red_count ?? 0,
    c1_green_rate: payload.c1_green_rate,
    c1_red_rate: payload.c1_red_rate,
    c1_green_rate_ci: payload.c1_green_rate_ci,
    c1_red_rate_ci: payload.c1_red_rate_ci,
    comparative_report: payload.comparative_report ?? null,
    short_signal: payload.short_signal,
    volatility_stats: payload.volatility_stats,
    rsi_by_interval: payload.rsi_by_interval,
    disp_by_interval: payload.disp_by_interval,
    atr_by_interval: payload.atr_by_interval,
    rsi_atr_heatmap: payload.rsi_atr_heatmap,
    high_prob_rsi_intervals: payload.high_prob_rsi_intervals,
    high_prob_disp_intervals: payload.high_prob_disp_intervals,
    high_prob_atr_intervals: payload.high_prob_atr_intervals,
    complex_pattern_analysis: payload.complex_pattern_analysis,
    ny_trading_guide: payload.ny_trading_guide,
    analysis_mode: payload.analysis_mode,
    coin: payload.coin ?? params.coin,
    interval: payload.interval ?? params.interval,
    n_streak: payload.n_streak ?? params.n_streak,
    direction: payload.direction ?? params.direction,
  };
}

export async function runStreakAnalysis(params: StreakAnalysisParams): Promise<StreakAnalysisResult | null> {
  try {
    const res = await api.post<ApiResponse<StreakAnalysisApiPayload>>('/streak-analysis', params);
    
    if (res.data.success && res.data.data) {
      const payload = res.data.data;
      if (hasCoreStreakFields(payload)) return payload;
      console.warn('Streak Analysis partial payload detected, applying defaults.');
      return normalizePartialStreakPayload(payload, params);
    }

    if (res.data.data) {
      console.warn('Streak Analysis error response contained partial data, applying defaults.');
      return normalizePartialStreakPayload(res.data.data, params);
    }

    console.error('Streak Analysis error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Streak Analysis request failed:', err);
    return null;
  }
}
