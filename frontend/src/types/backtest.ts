// 백테스트 관련 타입

import type { OHLCV } from './market';

export interface Trade {
  'Entry Time': string;
  'Entry Price': number;
  'Exit Time': string;
  'Exit Price': number;
  Outcome: string;
  Direction: string;
  Regime: string;
  PnL: number;
}

export interface RegimeStat {
  Regime: string;
  Count: number;
  WinRate: number;
  AvgPnL: number;
}

export interface BacktestSummary {
  n_trades: number;
  win_rate: number;
  total_pnl: number;
  liq_count: number;
  avg_pnl?: number;
  regime_stats?: RegimeStat[];
}

export interface BacktestResult {
  chart_data: OHLCV[];
  trades: Trade[];
  summary: BacktestSummary;
}

export interface BacktestParams {
  coin: string;
  interval: string;
  strategy_id: string;
  direction: 'Long' | 'Short';
  tp_pct: number;
  sl_pct: number;
  max_bars: number;
  leverage: number;
  entry_fee_pct: number;
  exit_fee_pct: number;
  rsi_ob: number;
  sma_main_len: number;
  sma1_len: number;
  sma2_len: number;
  adx_thr: number;
  donch: number;
  bb_length: number;
  bb_std_mult: number;
  atr_length: number;
  kc_mult: number;
  vol_ma_length: number;
  vol_spike_k: number;
  macd_fast: number;
  macd_slow: number;
  macd_signal: number;
  use_csv: boolean;
  start_date?: string;
  end_date?: string;
}

export interface Preset {
  coin: string;
  interval: string;
  strat_id: string;
  direction: string;
  params: Partial<BacktestParams>;
}

export interface AdvancedBacktestStats {
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number | null;
  max_drawdown_pct: number | null;
  profit_factor: number | null;
  avg_win: number | null;
  avg_loss: number | null;
  win_loss_ratio: number | null;
  t_statistic: number | null;
  p_value: number | null;
  is_significant: boolean;
}

export interface AdvancedBacktestSummary {
  n_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
}

export interface MonteCarloResult {
  mean_final_pnl: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  worst_case: number | null;
  best_case: number | null;
  median_max_dd?: number;
}

export interface AdvancedBacktestResult {
  chart_data: OHLCV[];
  trades: Trade[];
  in_sample: {
    summary: AdvancedBacktestSummary;
    stats: AdvancedBacktestStats;
    period: { start: string | null; end: string | null };
  };
  out_of_sample: {
    summary: AdvancedBacktestSummary;
    stats: AdvancedBacktestStats;
    period: { start: string | null; end: string | null };
  };
  full: {
    summary: AdvancedBacktestSummary;
    stats: AdvancedBacktestStats;
  };
  monte_carlo: MonteCarloResult;
}
