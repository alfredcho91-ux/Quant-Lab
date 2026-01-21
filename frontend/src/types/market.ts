// 시장 데이터 타입

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

export interface SRLevel {
  price: number;
  touches: number;
  kind: 'support' | 'resistance' | 'pivot';
  timeframe: string;
  source: string;
  label?: string;
}

export interface MarketContext {
  last_time: string;
  last_close: number;
  regime: string;
  adx: number;
  rsi: number;
  rsi2: number | null;
}
