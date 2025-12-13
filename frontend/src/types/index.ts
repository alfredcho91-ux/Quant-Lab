// Type definitions for WolGem Quant Master

export interface MarketPrice {
  last: number;
  percentage: number;
  high: number;
  low: number;
  volume: number;
}

export interface FearGreedIndex {
  value: string;
  value_classification: string;
  timestamp: string;
}

export interface Strategy {
  id: string;
  name_ko: string;
  name_en: string;
  prefix: string;
  logic: string;
}

export interface StrategyInfo {
  concept: string;
  Long: string;
  Short: string;
  regime: string;
}

export interface OHLCV {
  open_dt: string;
  open_time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  RSI?: number;
  EMA_main?: number;
  SMA_1?: number;
  SMA_2?: number;
  BB_Up?: number;
  BB_Low?: number;
  BB_Mid?: number;
  ADX?: number;
  Regime?: string;
  MACD?: number;
  MACD_signal?: number;
  MACD_hist?: number;
}

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
  rsi2_ob: number;
  ema_len: number;
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

export interface SRLevel {
  price: number;
  touches: number;
  kind: 'support' | 'resistance' | 'pivot';
  timeframe: string;
  source: string;
  label?: string;
}

export interface Preset {
  coin: string;
  interval: string;
  strat_id: string;
  direction: string;
  params: Partial<BacktestParams>;
}

export type Language = 'ko' | 'en';

export type Coin = 'BTC' | 'ETH' | 'SOL' | 'XRP';

export type MenuPage = 'backtest' | 'pattern' | 'ma-cross' | 'journal' | 'scanner' | 'pattern-scanner';

