// 전략 관련 타입

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

export interface StrategySignal {
  id: string;
  name_ko: string;
  name_en: string;
  long_signal: boolean;
  short_signal: boolean;
}

export interface PresetSignal {
  name: string;
  strategy_id: string;
  long_signal: boolean;
  short_signal: boolean;
}

export interface ScannerResult {
  signals: StrategySignal[];
  preset_signals: PresetSignal[];
  market_context: import('./market').MarketContext;
}
