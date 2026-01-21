// 연속 봉패턴 분석 API

import { api } from './config';
import type { StreakAnalysisParams, StreakAnalysisResult } from '../types';

export async function runStreakAnalysis(params: StreakAnalysisParams): Promise<StreakAnalysisResult | null> {
  try {
    const res = await api.post<{
      success: boolean;
      mode?: 'simple' | 'complex';
      filter_status?: import('../types').FilterStatus | null;
      total_cases: number;
      continuation_rate: number | null;
      reversal_rate: number | null;
      continuation_count: number;
      reversal_count: number;
      avg_body_pct: number | null;
      continuation_ci?: import('../types').ConfidenceInterval | null;
      c1_p_value?: number;
      c1_is_significant?: boolean;
      c2_after_c1_green_rate: number | null;
      c2_after_c1_red_rate: number | null;
      c2_after_c1_green_ci?: import('../types').ConfidenceInterval | null;
      c2_after_c1_red_ci?: import('../types').ConfidenceInterval | null;
      c1_green_count: number;
      c1_red_count: number;
      comparative_report: import('../types').ComparativeReport | null;
      short_signal?: import('../types').ShortSignal | null;
      volatility_stats?: import('../types').VolatilityStats;
      rsi_by_interval?: Record<string, import('../types').IntervalProbability>;
      disp_by_interval?: Record<string, import('../types').IntervalProbability>;
      high_prob_rsi_intervals?: Record<string, import('../types').IntervalProbability>;
      high_prob_disp_intervals?: Record<string, import('../types').IntervalProbability>;
      complex_pattern_analysis?: import('../types').ComplexPatternAnalysis | null;
      ny_trading_guide?: import('../types').NYTradingGuide;
      analysis_mode?: {
        type: string;
        description: string;
        parameters: {
          n_streak?: number;
          direction?: string;
          complex_pattern?: number[];
          filters?: {
            rsi_threshold?: number;
            max_retracement?: number;
          };
        };
      };
      coin: string;
      interval: string;
      n_streak: number;
      direction: string;
      error?: string;
    }>('/streak-analysis', params);
    
    if (res.data.success) {
      return {
        mode: res.data.mode,
        filter_status: res.data.filter_status,
        total_cases: res.data.total_cases,
        continuation_rate: res.data.continuation_rate,
        reversal_rate: res.data.reversal_rate,
        continuation_count: res.data.continuation_count,
        reversal_count: res.data.reversal_count,
        avg_body_pct: res.data.avg_body_pct,
        continuation_ci: res.data.continuation_ci,
        c1_p_value: res.data.c1_p_value,
        c1_is_significant: res.data.c1_is_significant,
        c2_after_c1_green_rate: res.data.c2_after_c1_green_rate,
        c2_after_c1_red_rate: res.data.c2_after_c1_red_rate,
        c2_after_c1_green_ci: res.data.c2_after_c1_green_ci,
        c2_after_c1_red_ci: res.data.c2_after_c1_red_ci,
        c1_green_count: res.data.c1_green_count,
        c1_red_count: res.data.c1_red_count,
        comparative_report: res.data.comparative_report,
        short_signal: res.data.short_signal,
        volatility_stats: res.data.volatility_stats,
        rsi_by_interval: res.data.rsi_by_interval,
        disp_by_interval: res.data.disp_by_interval,
        high_prob_rsi_intervals: res.data.high_prob_rsi_intervals,
        high_prob_disp_intervals: res.data.high_prob_disp_intervals,
        complex_pattern_analysis: res.data.complex_pattern_analysis,
        ny_trading_guide: res.data.ny_trading_guide,
        analysis_mode: res.data.analysis_mode,
        coin: res.data.coin,
        interval: res.data.interval,
        n_streak: res.data.n_streak,
        direction: res.data.direction,
      };
    }
    console.error('Streak Analysis error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Streak Analysis request failed:', err);
    return null;
  }
}
