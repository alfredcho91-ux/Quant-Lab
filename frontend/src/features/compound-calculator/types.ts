export type ChartMode = 'compound' | 'simple' | 'both';
export type Tone = 'positive' | 'negative' | 'warning' | 'neutral';
export type TradeOutcome = 'win' | 'loss';

export interface TradeScenario {
  outcomes: TradeOutcome[];
  winTrades: number;
  lossTrades: number;
}

export interface GrowthResult {
  balances: number[];
  maxDrawdown: number;
  worstCaseDrawdown: number;
}

export interface SummaryRow {
  trade: number;
  compoundCapital: number;
  compoundRoi: number;
  simpleCapital: number;
  simpleRoi: number;
}

export interface RiskRow {
  streak: number;
  probability: number;
  capitalLoss: number;
  tone: Tone;
  label: string;
}
