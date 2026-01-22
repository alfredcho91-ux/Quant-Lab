// 주간 패턴 분석 타입

export interface WeeklyPatternParams {
  coin: string;
  interval: string;
  direction?: 'down' | 'up';
  deep_drop_threshold: number;
  deep_rise_threshold: number;
  rsi_min: number;
  rsi_max: number;
  start_day?: number;  // 분석 시작 요일 (0=월요일, 1=화요일, ..., 6=일요일)
  end_day?: number;  // 분석 종료 요일 (0=월요일, 1=화요일, ..., 6=일요일)
}

export interface WeeklyPatternManualParams {
  coin: string;
  monday_open: number;
  tuesday_close: number;
  wednesday_date: string;
}

export interface WeeklyPatternStats {
  title: string;
  description: string;
  sample_count: number;
  sample_size_warning?: string | null;
  period?: {
    start: string | null;
    end: string | null;
  };
  win_rate: number | null;
  expected_return: number | null;
  median_return: number | null;
  volatility: number | null;
  confidence_interval?: {
    ci_lower: number | null;
    ci_upper: number | null;
    ci_width: number | null;
  };
  t_test?: {
    t_statistic: number | null;
    p_value: number | null;
    is_significant: boolean;
  };
  profit_factor: number | null;
  sharpe_ratio: number | null;
  max_drawdown?: {
    max_drawdown: number | null;
    max_drawdown_pct: number | null;
  };
  max_consecutive_loss: number;
  positive_sum: number | null;
  negative_sum: number | null;
}

export interface WeeklyPatternResult {
  success: boolean;
  coin: string;
  total_weeks: number;
  warnings?: string[];
  filters: {
    deep_drop_threshold: number;
    rsi_min?: number;
    rsi_max?: number;
    rsi_threshold?: number;  // 하위 호환성
    rsi_period?: number;
    atr_period?: number;
    vol_period?: number;
  };
  results: {
    baseline?: WeeklyPatternStats;
    deep_drop?: WeeklyPatternStats;
    deep_rise?: WeeklyPatternStats;
    oversold?: WeeklyPatternStats;
    contra?: WeeklyPatternStats;
  };
  error?: string;
  traceback?: string;
}

export interface WeeklyPatternBacktestParams {
  coin: string;
  interval: string;
  direction: 'down' | 'up';
  deep_drop_threshold: number;
  deep_rise_threshold: number;
  rsi_min: number;
  rsi_max: number;
  start_day?: number;  // 분석 시작 요일 (0=월요일, 1=화요일, ..., 6=일요일)
  end_day?: number;  // 분석 종료 요일 (0=월요일, 1=화요일, ..., 6=일요일)
  leverage?: number;
  fee_entry_rate?: number;
  fee_exit_rate?: number;
}

export interface WeeklyPatternBacktestTrade {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  gross_return_pct: number;
  net_return_pct: number;
  pnl_pct: number;
  is_win: boolean;
  ret_early: number;
  rsi_tue: number;
}

export interface WeeklyPatternBacktestResult {
  success: boolean;
  coin: string;
  total_weeks: number;
  filtered_weeks: number;
  filters: {
    deep_drop_threshold: number;
    rsi_min?: number;
    rsi_max?: number;
    rsi_threshold?: number;  // 하위 호환성
  };
  trades: WeeklyPatternBacktestTrade[];
  summary: {
    n_trades: number;
    win_rate: number;
    total_pnl: number;
    avg_pnl: number;
    max_pnl: number;
    min_pnl: number;
    profit_factor: number;
  };
  warnings?: string[];
  error?: string;
}

export interface WeeklyPatternManualResult {
  success: boolean;
  coin: string;
  input: {
    monday_open: number;
    tuesday_close: number;
    wednesday_date: string;
    ret_early: number;
  };
  output: {
    wednesday_open: number;
    sunday_close: number;
    ret_mid_late: number;
    wednesday_date: string;
    sunday_date: string | null;
  };
  backtest: {
    entry_price: number;
    exit_price: number;
    return_pct: number;
    is_profitable: boolean;
    entry_date: string;
    exit_date: string | null;
  };
  error?: string;
  error_type?: string;
}
