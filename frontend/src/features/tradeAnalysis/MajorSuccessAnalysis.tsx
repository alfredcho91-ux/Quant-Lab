import { useMemo, useState } from 'react';
import { CandlestickChart, Trophy } from 'lucide-react';

import type { JournalEntry, TradeQualityItem } from '../../types';
import { netReturnPct } from '../journal/journalReturns';
import TradeReportModal from '../journal/TradeReportModal';
import type { AnalyzedTrade } from './tradeAnalysis';

type Props = {
  trades: AnalyzedTrade[];
  qualityItems: TradeQualityItem[];
  allEntries: JournalEntry[];
  isLoading: boolean;
  isKo: boolean;
};

const RETURN_THRESHOLD = 30;
const PRICE_THRESHOLD = 3;

function number(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return '-';
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function priceReturn(trade: AnalyzedTrade): number | null {
  const { entry_price: entryPrice, exit_price: exitPrice, direction, pnl_pct: fallback } = trade.entry;
  if (entryPrice != null && entryPrice > 0 && exitPrice != null && Number.isFinite(exitPrice)) {
    return ((exitPrice - entryPrice) / entryPrice) * (direction === 'Short' ? -1 : 1) * 100;
  }
  return fallback != null && Number.isFinite(fallback) ? fallback : null;
}

function formatDate(value: string | null | undefined, isKo: boolean): string {
  if (!value) return '-';
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return '-';
  return isKo
    ? `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`
    : date.toLocaleDateString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit' });
}

export default function MajorSuccessAnalysis({ trades, qualityItems, allEntries, isLoading, isKo }: Props) {
  const [selectedTrade, setSelectedTrade] = useState<AnalyzedTrade | null>(null);
  const qualityById = useMemo(() => new Map(qualityItems.map((item) => [item.journal_id, item])), [qualityItems]);
  const cases = useMemo(() => trades
    .filter((trade) => {
      const pnl = trade.entry.realized_pnl;
      return pnl != null && pnl > 0 && ((netReturnPct(trade.entry) || 0) >= RETURN_THRESHOLD || (priceReturn(trade) || 0) >= PRICE_THRESHOLD);
    })
    .sort((left, right) => new Date(right.entry.datetime || 0).getTime() - new Date(left.entry.datetime || 0).getTime()), [trades]);
  const totalProfit = cases.reduce((sum, trade) => sum + (trade.entry.realized_pnl || 0), 0);
  const grossProfit = trades.reduce((sum, trade) => sum + Math.max(0, trade.entry.realized_pnl || 0), 0);

  return (
    <section className="border border-bull/45 bg-bull/5">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-bull/25 px-4 py-3">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-semibold text-white"><Trophy className="h-4 w-4 text-bull" />{isKo ? '대성공 거래' : 'Major Successes'}</h2>
          <p className="mt-1 text-[11px] text-dark-400">{isKo ? `투자금 대비 순수익률 ${RETURN_THRESHOLD}% 이상 또는 방향 반영 가격 수익률 ${PRICE_THRESHOLD}% 이상` : `Net margin return of ${RETURN_THRESHOLD}%+ or direction-adjusted price return of ${PRICE_THRESHOLD}%+`}</p>
        </div>
        <span className="font-mono text-xs text-bull">{cases.length}{isKo ? '건' : ''}</span>
      </div>

      {isLoading ? <div className="px-4 py-6 text-sm text-dark-400">{isKo ? '대성공 거래를 분석 중입니다.' : 'Analyzing major successes.'}</div> : cases.length === 0 ? <div className="px-4 py-5 text-sm text-dark-300">{isKo ? '선택 기간에는 대성공 기준에 해당하는 거래가 없습니다.' : 'No trade met the major-success threshold.'}</div> : <>
        <div className="grid border-b border-bull/20 sm:grid-cols-3">
          <div className="border-b border-bull/15 px-4 py-3 sm:border-b-0 sm:border-r"><div className="text-[11px] text-dark-500">{isKo ? '대성공 순수익' : 'Major profit'}</div><div className="mt-1 font-mono text-lg text-bull">+{number(totalProfit, 2)} USDT</div></div>
          <div className="border-b border-bull/15 px-4 py-3 sm:border-b-0 sm:border-r"><div className="text-[11px] text-dark-500">{isKo ? '전체 수익 중 비중' : 'Share of gross profit'}</div><div className="mt-1 font-mono text-lg text-white">{grossProfit > 0 ? number(totalProfit / grossProfit * 100) : '-'}%</div></div>
          <div className="px-4 py-3"><div className="text-[11px] text-dark-500">{isKo ? '최근 거래 우선' : 'Newest first'}</div><div className="mt-1 text-sm text-dark-200">{cases[0]?.entry.symbol} · {cases[0]?.entry.direction}</div></div>
        </div>
        <div>
          {cases.map((trade) => {
            const marginReturn = netReturnPct(trade.entry);
            const marketReturn = priceReturn(trade);
            const quality = trade.entry.id == null ? undefined : qualityById.get(trade.entry.id);
            return <article key={trade.entry.id} className="grid gap-3 border-b border-dark-800 px-4 py-3 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center">
              <button type="button" onClick={() => setSelectedTrade(trade)} className="text-left text-sm text-dark-200 hover:text-primary-200"><span className="flex items-center gap-1.5">{formatDate(trade.entry.datetime, isKo)}<CandlestickChart className="h-3.5 w-3.5 text-bull" /></span><span className="mt-1 block text-[11px] text-dark-500">{trade.entry.symbol} · {trade.entry.direction}{quality?.market_regime?.id ? ` · ${quality.market_regime.id}` : ''}</span></button>
              <div className="text-right"><div className="text-[10px] text-dark-500">{isKo ? '순수익금' : 'Net PnL'}</div><div className="font-mono text-bull">+{number(trade.entry.realized_pnl, 2)} USDT</div></div>
              <div className="text-right"><div className="text-[10px] text-dark-500">{isKo ? '투자금 / 가격 수익률' : 'Margin / price return'}</div><div className="font-mono text-xs text-dark-200">{marginReturn != null ? `+${number(marginReturn)}%` : '-'} / {marketReturn != null ? `+${number(marketReturn)}%` : '-'}</div></div>
            </article>;
          })}
        </div>
      </>}
      {selectedTrade && <TradeReportModal entry={selectedTrade.entry} allEntries={allEntries} excursion={selectedTrade.excursion} isKo={isKo} onClose={() => setSelectedTrade(null)} />}
    </section>
  );
}
