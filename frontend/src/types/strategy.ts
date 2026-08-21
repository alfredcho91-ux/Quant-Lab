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
