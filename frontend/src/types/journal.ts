// 매매 일지 타입

export interface JournalEntry {
  id?: number;
  datetime?: string;
  symbol?: string;
  timeframe?: string;
  direction?: string;
  strategy_id?: string;
  size?: number;
  entry_price?: number;
  exit_price?: number;
  pnl_pct?: number;
  r_multiple?: number;
  outcome?: string;
  emotion?: string;
  tags?: string;
  mistakes?: string;
  notes?: string;
  created_at?: string;
}
