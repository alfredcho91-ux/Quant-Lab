import { api, type ApiResponse, toApiClientError, unwrapApiResponse } from './config';

export type DistanceMode = 'fixed_pct' | 'atr' | 'mtr' | 'wick_mean' | 'wick_median' | 'wick_percentile' | 'breakout_percentile' | 'mae_percentile';
export interface LabConfig {
  coin: string; start: string; end: string;
  reference_interval: string; execution_interval: string; direction: string; reference: string; lookback: number;
  entry: { mode: DistanceMode; percentile: number }; stop: { mode: DistanceMode; percentile: number };
  target_mode: string; entry_values: number[]; stop_values: number[]; target_values: number[];
  exit_rule: string; holding_hours: number; max_entries_per_period: number;
  fee_bps: number; slippage_bps: number; initial_equity: number; sizing: string; risk_pct: number; allocation_pct: number;
  train_ratio: number; max_drawdown_pct: number; min_trades: number;
}
export interface Distribution {
  count: number; mean: number | null; median: number | null; std: number | null;
  p50: number | null; p75: number | null; p90: number | null; p95: number | null; p99: number | null;
  mean_median_ratio: number | null;
  histogram: { lower: number; upper: number; count: number; share_pct: number }[];
  ecdf: { value: number; probability_pct: number }[];
}
export type Metrics = Record<string, number | boolean | number[] | null>;
export type CandleMetric = 'upper' | 'lower' | 'tr' | 'atr' | 'mtr';
export interface LabTrade {
  side: string; entry_time: number; exit_time: number; reference_time: number;
  entry_price: number; exit_price: number; stop_price: number; target_price: number; quantity: number;
  pnl: number; fees: number; r_multiple: number; planned_rr: number;
  reason: string; ambiguous: boolean; intrabar_entry: boolean; holding_hours: number;
  mae_lower_pct: number; mae_upper_pct: number; mfe_lower_pct: number; mfe_upper_pct: number;
  conditional_sample_size: number;
}
export interface LabCandidate {
  id: number; entry: number; stop: number; target: number; counts: Record<string, number>;
  overall: Metrics; train: Metrics; test: Metrics;
  train_quality_exclusions: number;
  neighbourhood: { sampled_cells: number; median_train_ev_r: number | null; positive_fraction: number | null };
  trades: LabTrade[]; groups: Record<string, Record<string, Metrics>>;
  excursions: Record<string, Distribution>;
}
export interface LabResult {
  config: LabConfig;
  data: { source: string; as_of: number; fingerprint_sha256: string; counts: Record<string, number>; execution_first: number; execution_last: number };
  distributions: Record<string, { candle_count: number; metrics: Record<CandleMetric, { price: Distribution; percent_open: Distribution }> & { atr_mtr_ratio: Distribution } }>;
  breakouts: Record<string, Record<string, { depth_pct: Distribution; returns_confirmed: number; order_or_coverage_unknown: number; return_rate_lower_pct: number | null; return_minutes_upper_bound: Distribution }>>;
  split_time: number; selected_id: number | null; candidates: LabCandidate[];
  walk_forward: { train_end: number; test_end: number; candidate_id: number | null; test: Metrics | null }[];
}

export async function analyzeStopLossLab(config: LabConfig): Promise<LabResult> {
  try {
    return unwrapApiResponse(await api.post<ApiResponse<LabResult>>('/stop-loss-lab/analyze', config), 'Unable to run Stop-Loss Lab.');
  } catch (error) {
    throw toApiClientError(error, 'Unable to run Stop-Loss Lab.');
  }
}
