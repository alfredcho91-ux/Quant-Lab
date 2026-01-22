// 통계 분석 관련 타입

export interface BBMidParams {
  coin: string;
  intervals: string[];
  start_side: 'lower' | 'upper';
  max_bars: number;
  regime: string | null;
  use_csv: boolean;
}

export interface BBMidResult {
  interval: string;
  events: number;
  success: number;
  success_rate: number | null;
}

export interface BBMidExcursion {
  avg_mfe: number;
  avg_mae: number;
  avg_end: number;
}

export interface ComboFilterParams {
  coin: string;
  interval: string;
  direction: 'long' | 'short';
  tp_pct: number;
  horizon: number;
  rsi_min: number;
  rsi_max: number;
  sma_short: number;
  sma_long: number;
  filter1_type: string;
  filter1_params: Record<string, unknown>;
  filter2_type: string;
  filter2_params: Record<string, unknown>;
  filter3_type: string;
  filter3_params: Record<string, unknown>;
  use_csv: boolean;
}

export interface ComboFilterResult {
  events: number;
  tp_hits: number;
  no_tp: number;
  hit_rate: number | null;
  avg_ret: number | null;
}

export interface MultiTFSqueezeParams {
  coin: string;
  high_tf: string;
  low_tf: string;
  squeeze_thr_high: number;
  squeeze_thr_low: number;
  lower_lookback_bars: number;
  rsi_min: number;
  rsi_max: number;
  require_above_mid: boolean;
}

export interface SqueezeEvent {
  break_time: string;
  direction: 'up' | 'down';
  immediate_ret: number;
  lt_rsi_last: number;
  lt_above_mid: boolean;
}

export interface SqueezeStats {
  total_events: number;
  filtered_events: number;
  p_up?: number;
  p_down?: number;
  n_up?: number;
  n_down?: number;
  avg_ret_up?: number | null;
  avg_ret_down?: number | null;
}

export interface PatternScanParams {
  coin: string;
  intervals: string[];
  tp_pct: number;
  horizon: number;
  mode: 'natural' | 'position';
  position: 'long' | 'short';
  use_csv?: boolean;
}

export interface PatternStat {
  direction: 'bull' | 'bear' | null;
  signals: number;
  hit_rate: number | null;
  last_on: boolean;
}
