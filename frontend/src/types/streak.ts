// 연속 봉패턴 분석 타입

export interface StreakAnalysisParams {
  coin: string;
  interval: string;
  n_streak: number;
  direction: 'green' | 'red';
  use_complex_pattern?: boolean;
  complex_pattern?: number[] | null;
  rsi_threshold?: number;
  min_total_body_pct?: number | null; // N개 연속 봉의 몸통 총합 최소값 (%)
}

export interface ComparativeMetrics {
  prev_rsi: number | null;
  prev_body_pct: number | null;
  prev_vol_change: number | null;
  prev_disparity?: number | null; // Deprecated: 제거됨 (하위 호환성을 위해 선택적 유지)
}

export interface ComparativeReport {
  pattern_total: number;
  success_count: number;
  failure_count: number;
  success_rate: number | null;
  success: ComparativeMetrics;
  failure: ComparativeMetrics;
}

export interface VolatilityStats {
  avg_dip: number | null;
  avg_rise: number | null;
  std_dip: number | null;
  avg_atr_pct: number | null;
  practical_max_dip: number | null;
  extreme_max_dip: number | null;
  current_dip: number | null;
  z_score_dip: number | null;
  z_score_interpretation: 'normal' | 'unusual' | 'extreme' | null;
  is_trimmed: boolean;
  sample_count: number;
}

export interface IntervalProbability {
  rate: number;
  ci_lower: number;
  ci_upper: number;
  ci_width: number;
  sample_size: number;
  is_reliable: boolean;
  reliability: 'high' | 'medium' | 'low';
  p_value?: number;
  is_significant?: boolean;
  bonferroni?: {
    original_p: number | null;
    adjusted_alpha: number;
    num_tests: number;
    is_significant_after_correction: boolean;
    warning: string | null;
  };
  bonferroni_significant?: boolean;
}

export interface ConfidenceInterval {
  rate: number;
  ci_lower: number;
  ci_upper: number;
  ci_width: number;
  sample_size: number;
  is_reliable: boolean;
  reliability: 'high' | 'medium' | 'low';
}

export interface CaseStats {
  avg_body_pct: number | null;
  max_body_pct: number | null;
  min_body_pct: number | null;
  count: number;
}

export interface ShortSignal {
  enabled: boolean;
  total_cases: number;
  win_count: number;
  win_rate: number;
  entry_rise_pct: number | null;
  take_profit_pct: number | null;
  stop_loss_pct: number;
  rsi_threshold: number;
}

export interface FilterStatus {
  status: 'no_pattern_match' | 'filtered_out' | 'quality_analysis_failed' | 'success';
  reason?: string;
  total_matches?: number;
  quality_results?: number;
  filtered_count?: number;
  rsi_threshold?: number;
}

export interface StreakAnalysisResult {
  mode?: 'simple' | 'complex';
  filter_status?: FilterStatus | null;
  total_cases: number;
  continuation_rate: number | null;
  reversal_rate: number | null;
  continuation_count: number;
  reversal_count: number;
  avg_body_pct: number | null;
  continuation_stats?: CaseStats;
  reversal_stats?: CaseStats;
  continuation_ci?: ConfidenceInterval | null;
  c1_p_value?: number;
  c1_is_significant?: boolean;
  c2_after_c1_green_rate: number | null;
  c2_after_c1_red_rate: number | null;
  c2_after_c1_green_ci?: ConfidenceInterval | null;
  c2_after_c1_red_ci?: ConfidenceInterval | null;
  c1_green_count: number;
  c1_red_count: number;
  c1_green_rate?: number | null;
  c1_red_rate?: number | null;
  c1_green_rate_ci?: ConfidenceInterval | null;
  c1_red_rate_ci?: ConfidenceInterval | null;
  comparative_report: ComparativeReport | null;
  short_signal?: ShortSignal | null;
  volatility_stats?: VolatilityStats;
  rsi_by_interval?: Record<string, IntervalProbability>;
  disp_by_interval?: Record<string, IntervalProbability>;
  high_prob_rsi_intervals?: Record<string, IntervalProbability>;
  high_prob_disp_intervals?: Record<string, IntervalProbability>;
  complex_pattern_analysis?: ComplexPatternAnalysis | null;
  ny_trading_guide?: NYTradingGuide;
  analysis_mode?: {
    type: string;
    description: string;
    parameters: {
      n_streak?: number;
      direction?: string;
      complex_pattern?: number[];
      filters?: {
        rsi_threshold?: number;
      };
    };
  };
  coin: string;
  interval: string;
  n_streak: number;
  direction: string;
}

export interface ComplexPatternAnalysis {
  pattern: number[];
  total_matches: number;
  analyzed_count: number;
  filtered_count?: number;
  avg_score: number;
  high_confidence_count: number;
  high_confidence_rate: number;
  patterns?: PatternDetail[];
  ny_trading_guide?: NYTradingGuide;
  chart_data?: ChartDataPoint[];
  summary?: PatternSummary;
  filters_applied?: {
    rsi_threshold: number;
  };
  short_signal?: ShortSignal | null;
  volatility_stats?: VolatilityStats;
  rsi_by_interval?: Record<string, IntervalProbability>;
  disp_by_interval?: Record<string, IntervalProbability>;
  retracement_by_interval?: Record<string, IntervalProbability>;
  high_prob_rsi_intervals?: Record<string, IntervalProbability>;
  high_prob_disp_intervals?: Record<string, IntervalProbability>;
  high_prob_retracement_intervals?: Record<string, IntervalProbability>;
  comparative_report?: ComparativeReport | null;
}

export interface PatternDetail {
  index: string;
  date?: string;
  retracement_pct: number;
  vol_ratio: number;
  rsi: number | null;
  score: number;
  confidence: 'high' | 'medium' | 'low';
  max_score: number;
  reasons: string[];
}

export interface NYTradingGuide {
  entry_window: string;
  peak_window: string;
  average_lower_shadow: string;
  average_upper_shadow: string;
  low_window?: string;
  avg_volatility?: string;
  hourly_low_probability?: Record<string, number>;
  hourly_high_probability?: Record<string, number>;
  daily_low_probability?: Record<string, number>;
  daily_high_probability?: Record<string, number>;
  note: string;
}

export interface ChartDataPoint {
  date: string;
  pattern_date: string;
  retracement: number;
  vol_ratio: number;
  rsi: number | null; // 백엔드에서 항상 값이 있지만 타입 안전성을 위해 null 허용
  score: number;
  confidence: 'high' | 'medium' | 'low';
  c1?: CandleResult | null;
  c2?: CandleResult | null;
  profit_c1?: number | null;
  profit_c2?: number | null;
  is_success_c1?: boolean | null;
  is_success_c2?: boolean | null;
}

export interface CandleResult {
  date: string;
  color: number;
  return: number;
  is_success: boolean;
}

export interface PatternSummary {
  c1_analysis: DayAnalysis;
  c2_analysis: DayAnalysis;
}

export interface DayAnalysis {
  // 표시용: 양봉/음봉 비율 (사용자가 롱/숏 전략 직접 해석)
  green_rate: number;
  red_rate: number;
  green_confidence_interval: [number, number] | null;
  red_confidence_interval: [number, number] | null;
  green_count: number;
  red_count: number;
  total_count: number;
  avg_return: number;
  // 내부 로직용: 패턴 방향 기반 승률 (디버깅/검증용, 선택적)
  pattern_based_win_rate?: number | null;
  pattern_based_confidence_interval?: [number, number] | null;
  // 하위 호환성 (deprecated)
  win_rate?: number;
  confidence_interval?: [number, number] | null;
  success_count?: number;
}
