// 통계 분석 관련 타입
import type { AnchoredVwapDeviation } from './indicators';

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

export interface TrendIndicatorsParams {
  coin: string;
  interval: string;
  use_csv: boolean;
}

export interface TrendIndicatorsLatest {
  close: number | null;
  rsi: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  macd_cross: 'golden' | 'dead' | null;
  macd_hist_direction: 'rising' | 'falling' | 'flat' | null;
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
  stoch_rsi_k: number | null;
  stoch_rsi_d: number | null;
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
  current_rsi: number | null;
  vwaps: Array<{
    anchor: 'day' | 'week' | 'month' | 'quarter' | 'year';
    value: number | null;
  }>;
  rolling_vwaps: Array<{
    window: number;
    value: number | null;
  }>;
  rsi_30_price: number;
  rsi_70_price: number;
  vwap_deviation?: AnchoredVwapDeviation | null;
}
