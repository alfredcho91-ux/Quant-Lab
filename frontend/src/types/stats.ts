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
  avg_bars_to_mid?: number;
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

export interface TrendIndicatorsParams {
  coin: string;
  interval: string;
  use_csv: boolean;
}

export interface TrendIndicatorsLatest {
  close: number | null;
  rsi: number | null;
  macd_hist: number | null;
  adx: number | null;
  atr: number | null;
  atr_pct: number | null;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
  slow_stoch_5k: number | null;
  slow_stoch_5d: number | null;
  slow_stoch_10k: number | null;
  slow_stoch_10d: number | null;
  slow_stoch_20k: number | null;
  slow_stoch_20d: number | null;
  vwap_20: number | null;
  supertrend: number | null;
  supertrend_dir: number | null;
}

export interface TrendIndicatorsResult {
  success: boolean;
  latest: TrendIndicatorsLatest;
  series: Record<string, { t: string[]; v: number[] }>;
  interval: string;
  coin: string;
  error?: string;
}

export interface IndicatorProjection {
  current_price: number;
  rsi_30_price: number;
  rsi_70_price: number;
  stoch_20_price: number;
  stoch_80_price: number;
  stoch_hh?: number;
  stoch_ll?: number;
}
