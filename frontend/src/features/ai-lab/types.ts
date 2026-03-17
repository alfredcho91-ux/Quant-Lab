export type Direction = 'Long' | 'Short' | 'Both';

export type IndicatorDef = {
  id: string;
  label: string;
  params: Record<string, number>;
  descriptionKo: string;
  descriptionEn: string;
};

export type StrategyDraft = {
  name: string;
  execution_mode: 'template_strategy';
  strategy_hint: string;
  market: {
    coin: string;
    interval: string;
    direction: Direction;
  };
  indicators: Array<{
    id: string;
    params: Record<string, number>;
  }>;
  entry_rules: string[];
  exit_rules: string[];
  risk: {
    tp_pct: number;
    sl_pct: number;
    max_bars: number;
    leverage: number;
  };
  notes: string;
};
