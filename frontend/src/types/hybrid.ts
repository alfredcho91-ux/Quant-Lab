// 하이브리드 전략 분석 타입

export interface HybridAnalysisParams {
  coin: string;
  interval: string;
  strategies?: string[];  // None이면 전체 전략 분석
}

export interface HybridStrategyResult {
  strategy: string;
  signal_count: number;
  signal_rate: number;
  avg_rsi: number | null;
  avg_adx: number | null;
}

export interface HybridAnalysisResult {
  success: boolean;
  coin: string;
  interval: string;
  total_candles: number;
  strategies: HybridStrategyResult[];
  error?: string;
}

export interface HybridBacktestParams {
  coin: string;
  interval: string;
  strategy: string;  // SMA_ADX_Strong, MACD_RSI_Trend, Pure_Trend
  tp: number;  // 익절 비율 (%)
  sl: number;  // 손절 비율 (%)
  max_hold: number;  // 최대 보유 기간 (봉 수)
}

export interface HybridBacktestTrade {
  entry_idx: number;
  exit_idx: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  gross_pnl: number;
  reason: 'TP' | 'SL' | 'Time';
  hold: number;
  is_win: boolean;
}

export interface HybridBacktestResult {
  success: boolean;
  coin: string;
  interval: string;
  strategy: string;
  total_candles: number;
  trades: HybridBacktestTrade[];
  summary: {
    n_trades: number;
    win_rate: number;
    total_pnl: number;
    avg_pnl: number;
    max_pnl: number;
    min_pnl: number;
    profit_factor: number | null;
    tp_hit_rate: number;
    sl_hit_rate: number;
    time_exit_rate: number;
    avg_hold: number;
  };
  warnings?: string[];
  error?: string;
}

export interface HybridLiveModeParams {
  coin: string;
  interval: string;
  strategies?: string[];  // None이면 전체 전략 분석
}

export interface HybridLiveModeStrategy {
  strategy: string;
  is_active: boolean;
  timestamp: string;
  conditions: {
    sma20?: number | null;
    sma50?: number | null;
    adx?: number | null;
    sma20_above_sma50?: boolean | null;
    adx_above_25?: boolean | null;
    macd_hist?: number | null;
    rsi?: number | null;
    close?: number | null;
    sma200?: number | null;
    macd_positive?: boolean | null;
    rsi_above_55?: boolean | null;
    close_above_sma200?: boolean | null;
  };
}

export interface HybridLiveModeResult {
  success: boolean;
  coin: string;
  interval: string;
  timestamp: string;
  current_price: number | null;
  strategies: HybridLiveModeStrategy[];
  error?: string;
}
