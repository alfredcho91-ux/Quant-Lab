// Trading Journal Page
import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { BarChart3, CandlestickChart, KeyRound, Link2, Loader2, RefreshCw, Trash2, X } from 'lucide-react';

import {
  configureDeepcoinCredentials,
  deleteDeepcoinCredentials,
  deleteJournalEntry,
  getDeepcoinStatus,
  getJournal,
  getJournalQualityAnalysis,
  syncDeepcoinFills,
} from '../api/client';
import { useLanguage } from '../store/useStore';
import { useNavigate } from '../router-context';
import type { JournalEntry, TradeQualityItem } from '../types';
import { isClosedPosition } from '../features/journal/journalEntries';
import {
  buildJournalPeriod,
  dateBoundaryTimestamp,
  isJournalEntryWithinPeriod,
  lookbackDaysFromStart,
  toDateInputValue,
  type JournalPeriod,
} from '../features/journal/journalPeriod';
import {
  aggregateNetReturnPct,
  feeImpact,
  fundingImpact,
  netCostImpact,
  netReturnPct,
} from '../features/journal/journalReturns';
import { journalDerivedQueryPrefixes, journalQueryKeys } from '../features/journal/journalQueryKeys';
import TradeReportModal from '../features/journal/TradeReportModal';
import { tradeOutcomeAssessment } from '../features/journal/tradeOutcomeAssessment';
import { buildAnalyzedTrades } from '../features/tradeAnalysis/tradeAnalysis';
import { summarizeTradeStyle } from '../features/journal/tradeStyleSummary';
import DailyPnlCalendar from '../features/journal/DailyPnlCalendar';
import TradingStyleSelect from '../features/preferences/TradingStyleSelect';

function formatSignedNumber(value: number | null | undefined, maximumFractionDigits = 4): string {
  if (value == null || !Number.isFinite(value)) {
    return '-';
  }
  return `${value >= 0 ? '+' : ''}${value.toLocaleString(undefined, { maximumFractionDigits })}`;
}

function formatHoldingMinutes(minutes: number | null, isKo: boolean): string {
  if (minutes == null || !Number.isFinite(minutes)) return '-';
  const totalMinutes = Math.max(0, Math.round(minutes));
  const hours = Math.floor(totalMinutes / 60);
  const remainingMinutes = totalMinutes % 60;
  if (hours === 0) return isKo ? `${remainingMinutes}분` : `${remainingMinutes}m`;
  return isKo ? `${hours}시간 ${remainingMinutes}분` : `${hours}h ${remainingMinutes}m`;
}

function DeepcoinConnectionModal({
  isKo,
  isSaving,
  error,
  onSave,
  onClose,
}: {
  isKo: boolean;
  isSaving: boolean;
  error: unknown;
  onSave: (values: { api_key: string; secret_key: string; passphrase: string }) => void;
  onClose: () => void;
}) {
  const [apiKey, setApiKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const errorText = error instanceof Error ? error.message : null;
  const canSave = Boolean(apiKey.trim() && secretKey.trim() && passphrase.trim()) && !isSaving;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/75 p-4" role="dialog" aria-modal="true" aria-label={isKo ? 'Deepcoin API 연결' : 'Deepcoin API connection'}>
      <form
        className="w-full max-w-md border border-dark-600 bg-dark-950 shadow-2xl"
        onSubmit={(event) => {
          event.preventDefault();
          if (canSave) onSave({ api_key: apiKey, secret_key: secretKey, passphrase });
        }}
      >
        <div className="flex items-start justify-between gap-4 border-b border-dark-700 px-5 py-4">
          <div>
            <h2 className="flex items-center gap-2 text-base font-semibold text-white"><KeyRound className="h-4 w-4 text-primary-300" />Deepcoin {isKo ? '연결' : 'Connection'}</h2>
            <p className="mt-1 text-xs leading-5 text-dark-400">{isKo ? '읽기 전용 API만 사용합니다. 입력값은 브라우저에 저장하지 않으며, 연결 확인 후 이 컴퓨터의 보안 저장소에 암호화해 보관됩니다.' : 'Only read-only API access is used. Values are not saved in the browser and are kept in this computer\'s protected credential store after verification.'}</p>
          </div>
          <button type="button" onClick={onClose} disabled={isSaving} className="text-dark-400 hover:text-white" aria-label={isKo ? '닫기' : 'Close'}><X className="h-4 w-4" /></button>
        </div>
        <div className="space-y-4 px-5 py-4">
          <label className="block text-xs text-dark-300">API Key<input autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} className="mt-1.5 w-full border border-dark-700 bg-dark-900 px-3 py-2 text-sm text-white" /></label>
          <label className="block text-xs text-dark-300">Secret Key<input type="password" autoComplete="new-password" value={secretKey} onChange={(event) => setSecretKey(event.target.value)} className="mt-1.5 w-full border border-dark-700 bg-dark-900 px-3 py-2 text-sm text-white" /></label>
          <label className="block text-xs text-dark-300">Passphrase<input type="password" autoComplete="new-password" value={passphrase} onChange={(event) => setPassphrase(event.target.value)} className="mt-1.5 w-full border border-dark-700 bg-dark-900 px-3 py-2 text-sm text-white" /></label>
          {errorText && <div className="border border-bear/40 bg-bear/10 px-3 py-2 text-xs leading-5 text-bear">{errorText}</div>}
        </div>
        <div className="flex justify-end gap-2 border-t border-dark-700 px-5 py-4">
          <button type="button" onClick={onClose} disabled={isSaving} className="border border-dark-700 px-3 py-2 text-xs text-dark-300 hover:text-white">{isKo ? '취소' : 'Cancel'}</button>
          <button type="submit" disabled={!canSave} className="btn-primary inline-flex items-center gap-2 px-3 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-50">{isSaving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}{isKo ? '연결 확인 후 저장' : 'Verify and Save'}</button>
        </div>
      </form>
    </div>
  );
}

function AnalysisMetric({
  label,
  value,
  detail,
  tone = 'default',
}: {
  label: string;
  value: React.ReactNode;
  detail?: React.ReactNode;
  tone?: 'default' | 'positive' | 'negative' | 'primary';
}) {
  const toneClass =
    tone === 'positive'
      ? 'text-bull'
      : tone === 'negative'
      ? 'text-bear'
      : tone === 'primary'
      ? 'text-primary-300'
      : 'text-white';

  return (
    <div className="border border-dark-700 bg-dark-900/45 p-3">
      <div className="text-[11px] text-dark-500">{label}</div>
      <div className={`mt-1 text-lg font-bold font-mono ${toneClass}`}>{value}</div>
      {detail != null && <div className="mt-1 text-[11px] text-dark-500">{detail}</div>}
    </div>
  );
}

function PlanLabSummary({ data, isKo, onOpen }: {
  data?: import('../types').PlanLabData;
  isKo: boolean;
  onOpen: () => void;
}) {
  const summary = data?.summary;
  return <section className="flex items-center justify-between gap-4 border border-dark-700 bg-dark-900/30 px-4 py-3">
    <div className="min-w-0">
      <div className="text-xs font-semibold text-dark-100">{isKo ? '계획 분석' : 'Plan Lab'}</div>
      {summary?.plan_recorded_count ? <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-[11px] text-dark-400">
        <span>{isKo ? '계획 입력' : 'Plan coverage'} <strong className="font-mono text-dark-100">{summary.plan_recorded_count}/{data?.coverage.closed_trades || 0}</strong></span>
        <span>Plan Exp <strong className="font-mono text-dark-100">{formatSignedNumber(summary.plan_expectancy_r, 2)}R</strong></span>
        <span>Actual <strong className="font-mono text-dark-100">{formatSignedNumber(summary.actual_expectancy_r, 2)}R</strong></span>
        <span>Δ <strong className={`font-mono ${(summary.execution_delta_r || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>{formatSignedNumber(summary.execution_delta_r, 2)}R</strong></span>
      </div> : <div className="mt-1 text-[11px] text-dark-500">{data ? (isKo ? '사전 계획을 기록하면 계획 품질과 실행 이행도를 분석할 수 있습니다.' : 'Record pre-trade plans to analyze plan quality and execution adherence.') : (isKo ? 'Plan Lab 결과는 Plan Lab에서 불러온 뒤 이곳에 표시됩니다.' : 'Load Plan Lab for this period to show its official summary here.')}</div>}
    </div>
    <button type="button" onClick={onOpen} className="shrink-0 text-xs text-primary-200 hover:text-white">{isKo ? 'Plan Lab에서 자세히 보기 →' : 'Open Plan Lab →'}</button>
  </section>;
}

function CumulativePnlChart({ trades, isKo }: { trades: JournalEntry[]; isKo: boolean }) {
  const ordered = [...trades].sort((a, b) => {
    const aTime = a.datetime ? new Date(a.datetime).getTime() : 0;
    const bTime = b.datetime ? new Date(b.datetime).getTime() : 0;
    return aTime - bTime;
  });

  let cumulative = 0;
  const values = [0];
  for (const trade of ordered) {
    cumulative += trade.realized_pnl || 0;
    values.push(cumulative);
  }

  const width = 900;
  const height = 190;
  const padX = 12;
  const padY = 14;
  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 0);
  const rawRange = maxValue - minValue;
  const range = rawRange === 0 ? 1 : rawRange;
  const xStep = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
  const yFor = (value: number) => padY + ((maxValue - value) / range) * (height - padY * 2);
  const points = values.map((value, index) => `${padX + index * xStep},${yFor(value)}`).join(' ');
  const zeroY = yFor(0);
  const finalPnl = values[values.length - 1] || 0;

  return (
    <div className="border border-dark-700 bg-dark-900/35 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-sm font-semibold text-white">{isKo ? '누적 실현 PnL' : 'Cumulative Realized PnL'}</div>
          <div className="text-[11px] text-dark-500">
            {isKo ? '선택 기간의 종료 포지션을 종료시간 순으로 누적' : 'Closed positions accumulated by close time'}
          </div>
        </div>
        <div className={`font-mono text-lg font-bold ${finalPnl >= 0 ? 'text-bull' : 'text-bear'}`}>
          {formatSignedNumber(finalPnl, 2)} USDT
        </div>
      </div>

      {ordered.length === 0 ? (
        <div className="flex h-44 items-center justify-center text-sm text-dark-500">
          {isKo ? '선택 기간에 분석할 종료 거래가 없습니다.' : 'No closed trades in the selected period.'}
        </div>
      ) : (
        <>
          <div className="relative h-48 w-full overflow-hidden">
            <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="h-full w-full">
              <line
                x1={padX}
                x2={width - padX}
                y1={zeroY}
                y2={zeroY}
                stroke="currentColor"
                strokeWidth="1"
                strokeDasharray="5 5"
                className="text-dark-600"
              />
              <polyline
                points={points}
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                vectorEffect="non-scaling-stroke"
                className={finalPnl >= 0 ? 'text-bull' : 'text-bear'}
              />
            </svg>
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-dark-500">
            <span>{ordered[0]?.datetime ? new Date(ordered[0].datetime as string).toLocaleDateString() : '-'}</span>
            <span>
              {ordered[ordered.length - 1]?.datetime
                ? new Date(ordered[ordered.length - 1].datetime as string).toLocaleDateString()
                : '-'}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

function PeriodAnalysis({
  allEntries,
  closedEntries,
  qualityItems,
  isKo,
  instType,
  canSync,
  isSyncing,
  syncMessage,
  syncError,
  period,
  onSyncDays,
  onPeriodApply,
}: {
  allEntries: JournalEntry[];
  closedEntries: JournalEntry[];
  qualityItems: TradeQualityItem[];
  isKo: boolean;
  instType: 'SWAP' | 'SPOT';
  canSync: boolean;
  isSyncing: boolean;
  syncMessage: string | null;
  syncError: unknown;
  period: JournalPeriod;
  onSyncDays: (days: number) => void;
  onPeriodApply: (period: JournalPeriod) => void;
}) {
  const [initialPeriod] = useState(() => buildJournalPeriod());
  const [analysisStart, setAnalysisStart] = useState(initialPeriod.start);
  const [analysisEnd, setAnalysisEnd] = useState(initialPeriod.end);
  const [activePreset, setActivePreset] = useState<'7' | '30' | '90' | 'custom'>('30');
  const [customError, setCustomError] = useState<string | null>(null);
  const [showSupportingMetrics, setShowSupportingMetrics] = useState(false);

  const applyPreset = (days: 7 | 30 | 90) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - (days - 1));
    setAnalysisStart(toDateInputValue(start));
    setAnalysisEnd(toDateInputValue(end));
    setActivePreset(String(days) as '7' | '30' | '90');
    setCustomError(null);
    onPeriodApply({ start: toDateInputValue(start), end: toDateInputValue(end) });
    if (canSync) {
      onSyncDays(days);
    }
  };

  const applyCustomPeriod = () => {
    const startTs = dateBoundaryTimestamp(analysisStart);
    const endTs = dateBoundaryTimestamp(analysisEnd, true);
    const todayEndTs = dateBoundaryTimestamp(toDateInputValue(new Date()), true);
    if (startTs == null || endTs == null) {
      setCustomError(isKo ? '시작일과 종료일을 선택하세요.' : 'Choose both start and end dates.');
      return;
    }
    if (startTs > endTs) {
      setCustomError(isKo ? '시작일이 종료일보다 늦습니다.' : 'The start date is after the end date.');
      return;
    }
    if (todayEndTs != null && endTs > todayEndTs) {
      setCustomError(isKo ? '종료일은 오늘 이후로 설정할 수 없습니다.' : 'The end date cannot be after today.');
      return;
    }

    const lookbackDays = lookbackDaysFromStart(analysisStart);
    if (lookbackDays == null || lookbackDays < 1) {
      setCustomError(isKo ? '미래 날짜는 동기화할 수 없습니다.' : 'Future dates cannot be synchronized.');
      return;
    }
    setActivePreset('custom');
    onPeriodApply({ start: analysisStart, end: analysisEnd });
    if (lookbackDays > 90) {
      setCustomError(
        isKo
          ? '90일을 초과한 구간은 기존에 저장된 데이터만 분석합니다. Deepcoin 자동 동기화는 최근 90일까지 지원합니다.'
          : 'Periods beyond 90 days use already-saved data only; automatic Deepcoin sync supports the most recent 90 days.',
      );
      return;
    }

    setCustomError(null);
    if (canSync) {
      onSyncDays(lookbackDays);
    }
  };

  const periodClosedEntries = closedEntries
    .filter((entry) => isJournalEntryWithinPeriod(entry, period))
    .sort((a, b) => {
      const aTime = a.datetime ? new Date(a.datetime).getTime() : 0;
      const bTime = b.datetime ? new Date(b.datetime).getTime() : 0;
      return aTime - bTime;
    });

  const analysisTrades = periodClosedEntries.filter(
    (entry) => typeof entry.realized_pnl === 'number' && Number.isFinite(entry.realized_pnl),
  );
  const missingPnlCount = periodClosedEntries.length - analysisTrades.length;
  const pnlValues = analysisTrades.map((entry) => entry.realized_pnl as number);
  const wins = pnlValues.filter((value) => value > 0);
  const losses = pnlValues.filter((value) => value < 0);
  const breakevens = pnlValues.filter((value) => value === 0);
  const netPnl = pnlValues.reduce((sum, value) => sum + value, 0);
  const periodNetReturn = aggregateNetReturnPct(analysisTrades);
  const returnTradeCount = analysisTrades.filter((entry) => netReturnPct(entry) != null).length;
  const grossProfit = wins.reduce((sum, value) => sum + value, 0);
  const grossLoss = Math.abs(losses.reduce((sum, value) => sum + value, 0));
  const winRate = analysisTrades.length > 0 ? (wins.length / analysisTrades.length) * 100 : 0;
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? Infinity : 0;
  const averageWin = wins.length > 0 ? grossProfit / wins.length : 0;
  const averageLoss = losses.length > 0 ? -grossLoss / losses.length : 0;
  const expectancy = analysisTrades.length > 0 ? netPnl / analysisTrades.length : 0;
  const periodFeeImpact = feeImpact(analysisTrades);
  const periodFundingImpact = fundingImpact(analysisTrades);
  const periodNetCostImpact = netCostImpact(analysisTrades);
  const periodAnalyzedTrades = useMemo(() => {
    const periodIds = new Set(periodClosedEntries.flatMap((entry) => entry.id == null ? [] : [entry.id]));
    return buildAnalyzedTrades(allEntries).filter((trade) => trade.entry.id != null && periodIds.has(trade.entry.id));
  }, [allEntries, periodClosedEntries]);
  const averageHoldingMinutes = useMemo(() => {
    const values = periodAnalyzedTrades.flatMap((trade) => (
      trade.holdingMinutes != null && Number.isFinite(trade.holdingMinutes) ? [trade.holdingMinutes] : []
    ));
    return values.length ? values.reduce((total, value) => total + value, 0) / values.length : null;
  }, [periodAnalyzedTrades]);
  const tradeStyle = useMemo(
    () => summarizeTradeStyle(periodAnalyzedTrades, qualityItems, isKo),
    [isKo, periodAnalyzedTrades, qualityItems],
  );

  const directionStats = (direction: 'Long' | 'Short') => {
    const subset = analysisTrades.filter((entry) => entry.direction === direction);
    const subsetWins = subset.filter((entry) => (entry.realized_pnl || 0) > 0).length;
    const subsetPnl = subset.reduce((sum, entry) => sum + (entry.realized_pnl || 0), 0);
    return {
      count: subset.length,
      pnl: subsetPnl,
      winRate: subset.length > 0 ? (subsetWins / subset.length) * 100 : 0,
    };
  };

  const longStats = directionStats('Long');
  const shortStats = directionStats('Short');
  const symbolMap = new Map<string, { count: number; wins: number; pnl: number }>();
  for (const entry of analysisTrades) {
    const symbol = entry.symbol || '-';
    const current = symbolMap.get(symbol) || { count: 0, wins: 0, pnl: 0 };
    current.count += 1;
    current.wins += (entry.realized_pnl || 0) > 0 ? 1 : 0;
    current.pnl += entry.realized_pnl || 0;
    symbolMap.set(symbol, current);
  }
  const symbolRows = [...symbolMap.entries()]
    .map(([symbol, data]) => ({
      symbol,
      ...data,
      winRate: data.count > 0 ? (data.wins / data.count) * 100 : 0,
    }))
    .sort((a, b) => b.pnl - a.pnl);

  const inputStartTs = dateBoundaryTimestamp(analysisStart);
  const inputEndTs = dateBoundaryTimestamp(analysisEnd, true);
  const periodInvalid = inputStartTs != null && inputEndTs != null && inputStartTs > inputEndTs;
  const syncErrorText = syncError instanceof Error ? syncError.message : null;

  return (
    <section className="card p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">{isKo ? '기간 성과 분석' : 'Period Performance Analysis'}</h2>
          <p className="mt-1 text-xs text-dark-400">
            {isKo
              ? '기간을 선택하면 Deepcoin 데이터를 동기화한 뒤 종료 포지션을 분석합니다.'
              : 'Choosing a period syncs Deepcoin data and analyzes closed positions.'}
          </p>
          <div className="mt-1 text-[11px] text-dark-500">
            {period.start || '-'} ~ {period.end || '-'}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <TradingStyleSelect isKo={isKo} />
          {[7, 30, 90].map((days) => {
            const isActive = activePreset === String(days);
            return (
              <button
                key={days}
                type="button"
                onClick={() => applyPreset(days as 7 | 30 | 90)}
                disabled={isSyncing}
                className={`rounded-md border px-3 py-2 text-xs transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                  isActive
                    ? 'border-primary-500/60 bg-primary-500/15 text-primary-200'
                    : 'border-dark-700 bg-dark-800/50 text-dark-300 hover:border-dark-600 hover:text-white'
                }`}
              >
                {days}{isKo ? '일' : 'D'}
              </button>
            );
          })}
          <button
            type="button"
            onClick={() => {
              setActivePreset('custom');
              setCustomError(null);
            }}
            className={`rounded-md border px-3 py-2 text-xs transition-colors ${
              activePreset === 'custom'
                ? 'border-primary-500/60 bg-primary-500/15 text-primary-200'
                : 'border-dark-700 bg-dark-800/50 text-dark-300 hover:border-dark-600 hover:text-white'
            }`}
          >
            {isKo ? '직접 설정' : 'Custom'}
          </button>
        </div>
      </div>

      {activePreset === 'custom' && (
        <div className="mt-4 flex flex-wrap items-end gap-2 border border-dark-700 bg-dark-900/35 p-3">
          <div>
            <div className="mb-1 text-[10px] text-dark-500">{isKo ? '시작일' : 'From'}</div>
            <input
              type="date"
              value={analysisStart}
              max={toDateInputValue(new Date())}
              onChange={(event) => setAnalysisStart(event.target.value)}
              className="bg-dark-700 border border-dark-600 rounded-md px-2.5 py-2 text-xs"
            />
          </div>
          <div>
            <div className="mb-1 text-[10px] text-dark-500">{isKo ? '종료일' : 'To'}</div>
            <input
              type="date"
              value={analysisEnd}
              max={toDateInputValue(new Date())}
              onChange={(event) => setAnalysisEnd(event.target.value)}
              className="bg-dark-700 border border-dark-600 rounded-md px-2.5 py-2 text-xs"
            />
          </div>
          <button
            type="button"
            onClick={applyCustomPeriod}
            disabled={isSyncing}
            className="btn-primary flex items-center gap-2 px-3 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing
              ? isKo
                ? '동기화 중'
                : 'Syncing'
              : canSync
              ? isKo
                ? '적용·동기화'
                : 'Apply & Sync'
              : isKo
              ? '적용'
              : 'Apply'}
          </button>
          <span className="text-[10px] text-dark-500">
            {canSync
              ? isKo
                ? '90일 이내는 자동 동기화 · 초과 구간은 저장된 데이터만 분석'
                : 'Up to 90 days auto-syncs; longer periods use saved data only.'
              : isKo
              ? 'API 미연결 상태에서는 저장된 데이터만 분석'
              : 'Without API connection, analysis uses saved data only.'}
          </span>
        </div>
      )}

      {instType === 'SPOT' && (
        <div className="mt-3 border border-primary-500/20 bg-primary-500/5 p-2 text-[11px] text-primary-200">
          {isKo
            ? '현물 선택 시 체결 기록은 동기화되지만, 아래 성과 분석은 Deepcoin 선물 종료 포지션 기준입니다.'
            : 'Spot sync imports fills, while the performance section below is based on closed futures positions.'}
        </div>
      )}

      {(customError || syncErrorText || syncMessage) && (
        <div
          className={`mt-3 text-xs ${customError || syncErrorText ? 'text-bear' : 'text-dark-300'}`}
        >
          {customError || syncErrorText || syncMessage}
        </div>
      )}

      {periodInvalid ? (
        <div className="mt-4 border border-bear/30 bg-bear/10 p-3 text-sm text-bear">
          {isKo ? '시작일이 종료일보다 늦습니다.' : 'The start date is after the end date.'}
        </div>
      ) : (
        <>
          <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-5">
            <AnalysisMetric
              label={isKo ? '기간 순수익률' : 'Net Return'}
              value={periodNetReturn == null ? '-' : `${formatSignedNumber(periodNetReturn, 2)}%`}
              tone={(periodNetReturn || 0) >= 0 ? 'positive' : 'negative'}
              detail={`${returnTradeCount}${isKo ? '회 · 수수료·펀딩 반영' : ' trades · after fees/funding'}`}
            />
            <AnalysisMetric
              label={isKo ? '기간 순수익금' : 'Net Profit'}
              value={`${formatSignedNumber(netPnl, 2)} USDT`}
              tone={netPnl >= 0 ? 'positive' : 'negative'}
              detail={`${analysisTrades.length}${isKo ? '회 종료 거래 합계' : ' closed trades'}`}
            />
            <AnalysisMetric
              label={isKo ? '승률' : 'Win Rate'}
              value={`${winRate.toFixed(1)}%`}
              tone="primary"
              detail={`${wins.length}W · ${losses.length}L · ${breakevens.length}BE`}
            />
            <AnalysisMetric
              label="Profit Factor"
              value={Number.isFinite(profitFactor) ? profitFactor.toFixed(2) : '∞'}
              detail={isKo ? '총이익 ÷ 총손실' : 'Gross profit / gross loss'}
            />
            <AnalysisMetric
              label={isKo ? '평균 보유 시간' : 'Average Holding Time'}
              value={formatHoldingMinutes(averageHoldingMinutes, isKo)}
              detail={isKo ? '선택 기간의 종료 거래 기준' : 'Based on closed trades in selected period'}
            />
          </div>

          <div className="mt-3 flex flex-wrap items-baseline gap-x-2 gap-y-1 border-l-2 border-primary-400/60 bg-dark-900/25 px-3 py-2.5 text-sm leading-6 text-dark-200">
            <span className="font-bold text-primary-200">{isKo ? '매매 스타일' : 'Trading style'}</span>
            <span className="font-medium text-dark-100">
              {tradeStyle.insufficientData
                ? (isKo ? '분석할 거래가 더 필요합니다' : 'More completed trades are needed to analyze.')
                : tradeStyle.traits.join(' · ')}
            </span>
          </div>

          <div className="mt-5">
            <div className="mb-2 text-xs text-dark-500">
              {isKo ? `${period.start} ~ ${period.end} 선택 기간 기준` : `For ${period.start} to ${period.end}`}
            </div>
            <div className="grid gap-3 md:grid-cols-2">
            <div className="border border-dark-700 bg-dark-900/35 p-4">
              <div className="text-xs font-semibold text-dark-300">LONG</div>
              <div className={`mt-2 font-mono text-xl font-bold ${longStats.pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                {formatSignedNumber(longStats.pnl, 2)} USDT
              </div>
              <div className="mt-1 text-xs text-dark-500">
                {longStats.count}{isKo ? '회' : ' trades'} · {isKo ? '승률' : 'win'} {longStats.winRate.toFixed(1)}%
              </div>
            </div>
            <div className="border border-dark-700 bg-dark-900/35 p-4">
              <div className="text-xs font-semibold text-dark-300">SHORT</div>
              <div className={`mt-2 font-mono text-xl font-bold ${shortStats.pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                {formatSignedNumber(shortStats.pnl, 2)} USDT
              </div>
              <div className="mt-1 text-xs text-dark-500">
                {shortStats.count}{isKo ? '회' : ' trades'} · {isKo ? '승률' : 'win'} {shortStats.winRate.toFixed(1)}%
              </div>
            </div>
            </div>
          </div>

          <div className="mt-4">
            <CumulativePnlChart trades={analysisTrades} isKo={isKo} />
          </div>

          <DailyPnlCalendar trades={analysisTrades} period={period} isKo={isKo} />

          <div className="mt-4 border border-dark-700 bg-dark-900/35 p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <div>
                  <div className="text-sm font-semibold text-white">{isKo ? '코인별 성과' : 'Performance by Symbol'}</div>
                  <div className="text-[11px] text-dark-500">{isKo ? '순손익 기준 정렬' : 'Sorted by net PnL'}</div>
                </div>
                <div className="text-[11px] text-dark-500">{symbolRows.length}{isKo ? '종목' : ' symbols'}</div>
              </div>
              {symbolRows.length === 0 ? (
                <div className="py-8 text-center text-sm text-dark-500">-</div>
              ) : (
                <div className="max-h-52 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="text-dark-500">
                      <tr className="border-b border-dark-700">
                        <th className="py-1.5 text-left">{isKo ? '심볼' : 'Symbol'}</th>
                        <th className="py-1.5 text-right">{isKo ? '거래' : 'Trades'}</th>
                        <th className="py-1.5 text-right">{isKo ? '승률' : 'Win'}</th>
                        <th className="py-1.5 text-right">PnL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {symbolRows.map((row) => (
                        <tr key={row.symbol} className="border-b border-dark-800">
                          <td className="py-2 text-dark-200">{row.symbol}</td>
                          <td className="py-2 text-right font-mono text-dark-300">{row.count}</td>
                          <td className="py-2 text-right font-mono text-dark-300">{row.winRate.toFixed(0)}%</td>
                          <td className={`py-2 text-right font-mono ${row.pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                            {formatSignedNumber(row.pnl, 2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
          </div>

          <div className="mt-3 border border-dark-700 bg-dark-900/25">
            <button
              type="button"
              onClick={() => setShowSupportingMetrics((value) => !value)}
              className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-dark-200 hover:bg-dark-800/50 hover:text-white"
              aria-expanded={showSupportingMetrics}
            >
              <span>{isKo ? '보조 성과 지표 보기' : 'View supporting performance metrics'}</span>
              <span className="text-dark-500">{showSupportingMetrics ? '▴' : '▾'}</span>
            </button>
            {showSupportingMetrics && (
              <div className="grid grid-cols-2 gap-3 border-t border-dark-700 p-4 md:grid-cols-4">
                <AnalysisMetric
                  label={isKo ? '평균 수익' : 'Avg Win'}
                  value={`${formatSignedNumber(averageWin, 2)} USDT`}
                  tone="positive"
                />
                <AnalysisMetric
                  label={isKo ? '평균 손실' : 'Avg Loss'}
                  value={`${formatSignedNumber(averageLoss, 2)} USDT`}
                  tone="negative"
                />
                <AnalysisMetric
                  label={isKo ? '거래당 기대값' : 'Expectancy / Trade'}
                  value={`${formatSignedNumber(expectancy, 2)} USDT`}
                  tone={expectancy >= 0 ? 'positive' : 'negative'}
                />
                <AnalysisMetric
                  label={isKo ? '비용 순효과' : 'Net Cost Impact'}
                  value={`${formatSignedNumber(periodNetCostImpact, 2)} USDT`}
                  tone={periodNetCostImpact >= 0 ? 'positive' : 'negative'}
                  detail={`${isKo ? '수수료' : 'Fee'} ${formatSignedNumber(periodFeeImpact, 2)} · ${isKo ? '펀딩' : 'Funding'} ${formatSignedNumber(periodFundingImpact, 2)}`}
                />
              </div>
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[11px] text-dark-500">
            <span>
              {isKo
                ? `분석 대상 ${periodClosedEntries.length}건 · PnL 계산 가능 ${analysisTrades.length}건`
                : `${periodClosedEntries.length} closed · ${analysisTrades.length} with PnL`}
              {missingPnlCount > 0 ? ` · ${isKo ? 'PnL 누락' : 'missing PnL'} ${missingPnlCount}` : ''}
            </span>
            <span>
              {isKo
                ? '순수익률 = 순실현손익 ÷ 실제 투입 증거금, 투자금 가중 합산'
                : 'Net return = net realized PnL / invested margin, margin-weighted'}
            </span>
          </div>
        </>
      )}
    </section>
  );
}

export default function JournalPage() {
  const language = useLanguage();
  const isKo = language === 'ko';
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const [deepcoinInstType, setDeepcoinInstType] = useState<'SWAP' | 'SPOT'>('SWAP');
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [snapshotEntry, setSnapshotEntry] = useState<JournalEntry | null>(null);
  const [historyPeriod, setHistoryPeriod] = useState<JournalPeriod>(() => buildJournalPeriod());
  const [connectionOpen, setConnectionOpen] = useState(false);
  const [visibleTradeCount, setVisibleTradeCount] = useState(10);

  const { data: entries, isLoading, isError: entriesError, refetch: refetchEntries } = useQuery({
    queryKey: journalQueryKeys.entries,
    queryFn: getJournal,
  });
  const historyStartTime = dateBoundaryTimestamp(historyPeriod.start);
  const historyEndTime = dateBoundaryTimestamp(historyPeriod.end, true);
  const cachedPlanLab = queryClient.getQueryData<import('../types').PlanLabData>(
    journalQueryKeys.planLab(historyStartTime, historyEndTime, 'ALL', undefined, undefined, 'ALL'),
  );
  const qualityQuery = useQuery({
    queryKey: journalQueryKeys.qualityAnalysis(historyStartTime, historyEndTime),
    queryFn: () => getJournalQualityAnalysis({
      start_time: historyStartTime as number,
      end_time: historyEndTime as number,
    }),
    enabled: historyStartTime != null && historyEndTime != null && historyStartTime <= historyEndTime,
    staleTime: 30 * 60_000,
    retry: false,
  });
  const qualityByJournalId = useMemo(
    () => new Map((qualityQuery.data?.items || []).map((item) => [item.journal_id, item])),
    [qualityQuery.data?.items],
  );
  const excursionByJournalId = useMemo(
    () => new Map((qualityQuery.data?.items || []).flatMap((item) => (
      item.excursion ? [[item.journal_id, item.excursion] as const] : []
    ))),
    [qualityQuery.data?.items],
  );

  const { data: deepcoinStatus } = useQuery({
    queryKey: ['deepcoin-status'],
    queryFn: getDeepcoinStatus,
    staleTime: 60_000,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteJournalEntry,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: journalQueryKeys.entries });
      await Promise.all(journalDerivedQueryPrefixes.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
    },
  });

  const deepcoinConnectionMutation = useMutation({
    mutationFn: configureDeepcoinCredentials,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['deepcoin-status'] });
      setConnectionOpen(false);
      setSyncMessage(isKo ? 'Deepcoin 읽기 전용 연결을 확인하고 이 컴퓨터에 저장했습니다.' : 'Deepcoin read-only connection verified and saved on this computer.');
    },
  });

  const deepcoinDisconnectMutation = useMutation({
    mutationFn: deleteDeepcoinCredentials,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['deepcoin-status'] });
      setSyncMessage(isKo ? '이 컴퓨터에 저장된 Deepcoin 연결 정보를 삭제했습니다.' : 'The Deepcoin connection stored on this computer was deleted.');
    },
  });

  const deepcoinSyncMutation = useMutation({
    mutationFn: syncDeepcoinFills,
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: journalQueryKeys.entries });
      await Promise.all(journalDerivedQueryPrefixes.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
      setSyncMessage(
        isKo
          ? `동기화 완료: 체결 ${result.imported}건 저장, 종료 포지션 ${result.positions_imported}건 저장 · 기존 기록 ${result.fills_updated + result.positions_updated}건의 지표 기준 갱신${result.warnings.length ? ' · 일부 스냅샷 또는 조회 범위를 확인하세요.' : ''}`
          : `Sync complete: ${result.imported} fills imported, ${result.positions_imported} closed positions imported · refreshed indicator references for ${result.fills_updated + result.positions_updated} existing records${result.warnings.length ? ' · Review snapshot or range warnings.' : ''}`,
      );
    },
  });

  const allEntries = entries || [];
  const closedEntries = allEntries.filter(isClosedPosition);
  const periodClosedEntries = closedEntries.filter((entry) => isJournalEntryWithinPeriod(entry, historyPeriod));
  const visibleEntries = periodClosedEntries
    .sort((a, b) => {
      const aTime = a.datetime ? new Date(a.datetime).getTime() : 0;
      const bTime = b.datetime ? new Date(b.datetime).getTime() : 0;
      if (aTime !== bTime) return bTime - aTime;
      return (b.id || 0) - (a.id || 0);
    });
  const displayedEntries = visibleEntries.slice(0, visibleTradeCount);

  return (
    <div className="space-y-6">
      <div>
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            📒 {isKo ? '매매 일지' : 'Trading Journal'}
          </h1>
          <p className="text-dark-400 mt-1">
            {isKo ? '거래 기록 및 복기 관리' : 'Track and review your trades'}
          </p>
        </div>
      </div>

      <section className="flex flex-col gap-3 border border-dark-700 bg-dark-800/35 p-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center border border-dark-600 bg-dark-900 text-primary-300">
            <Link2 className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Deepcoin</div>
            <div className={`text-xs ${deepcoinStatus?.configured ? 'text-bull' : 'text-dark-400'}`}>
              {deepcoinStatus?.configured
                ? isKo
                  ? '읽기 전용 연결 준비됨'
                  : 'Read-only connection ready'
                : isKo
                ? '읽기 전용 API 연결 필요'
                : 'Read-only API connection required'}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={() => setConnectionOpen(true)} className="inline-flex items-center gap-1.5 border border-dark-600 bg-dark-900 px-3 py-2 text-xs text-dark-200 hover:border-primary-400/60 hover:text-white">
            <KeyRound className="h-3.5 w-3.5 text-primary-300" />
            {deepcoinStatus?.configured ? (isKo ? '연결 설정' : 'Connection settings') : (isKo ? 'API 연결' : 'Connect API')}
          </button>
          {deepcoinStatus?.configured && deepcoinStatus.credential_storage !== 'environment' && (
            <button
              type="button"
              onClick={() => {
                if (window.confirm(isKo ? '이 컴퓨터에 저장된 Deepcoin API 연결 정보를 삭제할까요?' : 'Delete the Deepcoin API connection stored on this computer?')) {
                  deepcoinDisconnectMutation.mutate();
                }
              }}
              disabled={deepcoinDisconnectMutation.isPending}
              className="inline-flex items-center gap-1.5 border border-bear/40 px-3 py-2 text-xs text-bear hover:bg-bear/10 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {isKo ? '연결 삭제' : 'Delete connection'}
            </button>
          )}
          <select
            value={deepcoinInstType}
            onChange={(event) => setDeepcoinInstType(event.target.value as 'SWAP' | 'SPOT')}
            className="bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            aria-label={isKo ? '상품 유형' : 'Instrument type'}
          >
            <option value="SWAP">{isKo ? 'USDT 선물' : 'USDT Perpetual'}</option>
            <option value="SPOT">{isKo ? '현물' : 'Spot'}</option>
          </select>
          <span className="text-xs text-dark-400">
            {isKo ? '동기화 기간은 아래 기간 성과 분석에서 선택합니다.' : 'Choose the sync period in the performance section below.'}
          </span>
        </div>
      </section>

      <PeriodAnalysis
        allEntries={allEntries}
        closedEntries={closedEntries}
        qualityItems={qualityQuery.data?.items || []}
        isKo={isKo}
        instType={deepcoinInstType}
        canSync={Boolean(deepcoinStatus?.configured)}
        isSyncing={deepcoinSyncMutation.isPending}
        syncMessage={syncMessage}
        syncError={deepcoinSyncMutation.error}
        period={historyPeriod}
        onSyncDays={(days) => {
          setSyncMessage(null);
          deepcoinSyncMutation.mutate({
            inst_type: deepcoinInstType,
            lookback_days: days,
          });
        }}
        onPeriodApply={(period) => {
          setHistoryPeriod(period);
          setVisibleTradeCount(10);
        }}
      />

      <PlanLabSummary data={cachedPlanLab} isKo={isKo} onOpen={() => navigate('/plan-lab')} />

      <div className="card p-6">
        <div className="mb-4">
          <div>
            <h3 className="text-lg font-semibold">{isKo ? '거래 기록' : 'Trade History'}</h3>
            <p className="mt-1 text-xs text-dark-500">
              {isKo
                ? `${historyPeriod.start} ~ ${historyPeriod.end} · 종료된 포지션만 표시합니다.`
                : `${historyPeriod.start} ~ ${historyPeriod.end} · Closed positions only.`}
            </p>
          </div>
        </div>

        {entriesError ? (
          <div className="flex items-center justify-center gap-3 py-8 text-sm text-amber-300">
            <span>{isKo ? '거래 기록을 불러오지 못했습니다.' : 'Trade history could not be loaded.'}</span>
            <button type="button" onClick={() => void refetchEntries()} className="inline-flex items-center gap-1 border border-amber-300/40 px-2 py-1 text-xs"><RefreshCw className="h-3 w-3" />{isKo ? '재시도' : 'Retry'}</button>
          </div>
        ) : isLoading ? (
          <div className="text-center py-8 text-dark-400">{isKo ? '로딩 중...' : 'Loading...'}</div>
        ) : visibleEntries.length === 0 ? (
          <div className="text-center py-8 text-dark-400">
            {isKo ? '현재 필터에 표시할 거래가 없습니다.' : 'No trades match the current filter.'}
          </div>
        ) : (
          <>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-700">
                  <th className="text-left py-2 px-3">{isKo ? '날짜' : 'Date'}</th>
                  <th className="text-left py-2 px-3">{isKo ? '심볼' : 'Symbol'}</th>
                  <th className="text-center py-2 px-3">{isKo ? '방향' : 'Dir'}</th>
                  <th className="text-right py-2 px-3">{isKo ? '진입' : 'Entry'}</th>
                  <th className="text-right py-2 px-3">{isKo ? '청산' : 'Exit'}</th>
                  <th className="text-right py-2 px-3">{isKo ? '투입금 대비 수익률' : 'Margin Return'}</th>
                  <th className="text-right py-2 px-3">{isKo ? '순수익금' : 'Net Profit'}</th>
                  <th className="text-center py-2 px-3">{isKo ? '손익 결과' : 'PnL Result'}</th>
                  <th className="text-center py-2 px-1">
                    <span className="sr-only">{isKo ? '거래 리포트' : 'Trade report'}</span>
                  </th>
                  <th className="text-center py-2 px-3"></th>
                </tr>
              </thead>
              <tbody>
                {displayedEntries.map((entry) => {
                  const closed = isClosedPosition(entry);
                  const excursion = entry.id == null ? null : excursionByJournalId.get(entry.id) || null;
                  const quality = entry.id == null ? null : qualityByJournalId.get(entry.id) || null;
                  const assessment = excursion
                    ? tradeOutcomeAssessment(excursion, quality?.quality_class, isKo)
                    : null;
                  const displayNetReturnPct = netReturnPct(entry);
                  const closeDate = entry.datetime ? new Date(entry.datetime) : null;
                  const hasValidCloseDate = closeDate != null && Number.isFinite(closeDate.getTime());

                  return (
                    <tr
                      key={entry.id}
                      className={`border-b border-dark-800 align-top transition-colors hover:bg-dark-800/50 ${
                        closed ? 'bg-primary-500/[0.035]' : ''
                      }`}
                    >
                      <td className="py-2 px-3 text-xs font-mono whitespace-nowrap">
                        <div>{hasValidCloseDate ? toDateInputValue(closeDate) : '-'}</div>
                        <div className="mt-0.5 text-[10px] text-dark-500">
                          {hasValidCloseDate
                            ? closeDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                            : ''}
                        </div>
                      </td>
                      <td className="py-2 px-3">
                        <div className="font-medium">{entry.symbol || '-'}</div>
                        <div className="flex items-center gap-1.5 text-xs text-dark-400">
                          <span>{entry.timeframe || '-'}</span>
                          {entry.source === 'deepcoin' && (
                            <span className="border border-primary-500/30 bg-primary-500/10 px-1 text-[10px] text-primary-300">
                              Deepcoin
                            </span>
                          )}
                          {entry.source === 'deepcoin_position' && (
                            <span className="border border-bull/30 bg-bull/10 px-1 text-[10px] text-bull">
                              {isKo ? 'Deepcoin 종료' : 'Deepcoin Closed'}
                            </span>
                          )}
                        </div>
                      </td>
                      <td
                        className={`py-2 px-3 text-center ${
                          entry.direction === 'Long' ? 'text-bull' : 'text-bear'
                        }`}
                      >
                        {entry.direction || '-'}
                      </td>
                      <td className="py-2 px-3 text-right font-mono">
                        {entry.entry_price?.toLocaleString() || '-'}
                      </td>
                      <td className="py-2 px-3 text-right font-mono">
                        {entry.exit_price?.toLocaleString() || '-'}
                      </td>
                      <td
                        className={`py-2 px-3 text-right font-mono ${
                          (displayNetReturnPct || 0) >= 0 ? 'text-bull' : 'text-bear'
                        }`}
                      >
                        <div className={closed ? 'text-base font-bold' : ''}>
                          {displayNetReturnPct == null ? '-' : `${formatSignedNumber(displayNetReturnPct, 3)}%`}
                        </div>
                      </td>
                      <td
                        className={`py-2 px-3 text-right font-mono font-bold ${
                          (entry.realized_pnl || 0) >= 0 ? 'text-bull' : 'text-bear'
                        }`}
                      >
                        {entry.realized_pnl == null
                          ? '-'
                          : `${formatSignedNumber(entry.realized_pnl, 4)} USDT`}
                      </td>
                      <td className="py-2 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            entry.outcome === 'Win'
                              ? 'bg-bull/20 text-bull'
                              : entry.outcome === 'Loss'
                              ? 'bg-bear/20 text-bear'
                              : 'bg-dark-600 text-dark-300'
                          }`}
                        >
                          {entry.outcome || '-'}
                        </span>
                      </td>
                      <td className="py-2 px-1 text-center">
                        <div className="flex min-w-14 items-center justify-center gap-2">
                          {closed && entry.datetime && entry.exit_price != null && (
                            <button
                              type="button"
                              onClick={() => setSnapshotEntry(entry)}
                              className="text-amber-300 transition-colors hover:text-amber-100"
                              title={isKo ? '거래 리포트 및 차트' : 'Trade report and chart'}
                            >
                              <CandlestickChart className="h-4 w-4" />
                            </button>
                          )}
                          {!closed && entry.indicator_snapshot && (
                          <button
                            type="button"
                            onClick={() => setSnapshotEntry(entry)}
                            className="text-primary-400 transition-colors hover:text-primary-200"
                            title={isKo ? '거래 리포트 보기' : 'View trade report'}
                          >
                            <BarChart3 className="h-4 w-4" />
                          </button>
                          )}
                        </div>
                      </td>
                      <td className="py-2 px-3">
                        <details className="group relative">
                          <summary className="cursor-pointer list-none text-xs text-dark-500 hover:text-white">{isKo ? '상세' : 'Details'}</summary>
                          <div className="absolute right-0 z-10 mt-2 w-64 border border-dark-700 bg-dark-950 p-3 text-left shadow-xl">
                            {assessment ? (
                              <div>
                                <div className={`text-xs font-semibold ${assessment.tone === 'negative' ? 'text-bear' : assessment.tone === 'warning' ? 'text-amber-300' : 'text-primary-300'}`}>{assessment.label}</div>
                                <div className="mt-1 text-[11px] leading-4 text-dark-400">{assessment.explanation}</div>
                              </div>
                            ) : qualityQuery.isLoading ? (
                              <div className="text-xs text-dark-500">{isKo ? '판정 계산 중' : 'Calculating assessment'}</div>
                            ) : null}
                            {(entry.fee != null || entry.funding_fee != null) && (
                              <div className="mt-2 border-t border-dark-800 pt-2 text-[11px] text-dark-400">
                                {entry.fee != null && <div>{isKo ? '수수료' : 'Fee'}: {formatSignedNumber(-Math.abs(entry.fee))} {entry.fee_currency || 'USDT'}</div>}
                                {entry.funding_fee != null && <div>{isKo ? '펀딩' : 'Funding'}: {formatSignedNumber(entry.funding_fee)} USDT</div>}
                              </div>
                            )}
                            <button
                              type="button"
                              onClick={() => entry.id && deleteMutation.mutate(entry.id)}
                              disabled={deleteMutation.isPending}
                              className="mt-3 inline-flex items-center gap-1 text-xs text-dark-500 hover:text-red-400 disabled:opacity-50"
                            >
                              <Trash2 className="h-3.5 w-3.5" />{isKo ? '삭제' : 'Delete'}
                            </button>
                          </div>
                        </details>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="space-y-2 md:hidden">
            {displayedEntries.map((entry) => {
              const excursion = entry.id == null ? null : excursionByJournalId.get(entry.id) || null;
              const quality = entry.id == null ? null : qualityByJournalId.get(entry.id) || null;
              const assessment = excursion ? tradeOutcomeAssessment(excursion, quality?.quality_class, isKo) : null;
              const displayNetReturnPct = netReturnPct(entry);
              const closeDate = entry.datetime ? new Date(entry.datetime) : null;
              const hasValidCloseDate = closeDate != null && Number.isFinite(closeDate.getTime());
              const pnl = entry.realized_pnl || 0;
              return (
                <article key={entry.id} className="border border-dark-700 bg-dark-900/35 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-white">{entry.symbol || '-'}</div>
                      <div className="mt-0.5 text-[11px] text-dark-500">
                        {hasValidCloseDate ? `${toDateInputValue(closeDate)} ${closeDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : '-'}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-semibold ${entry.direction === 'Long' ? 'text-bull' : 'text-bear'}`}>{entry.direction || '-'}</span>
                      <span className={`rounded px-2 py-0.5 text-xs ${entry.outcome === 'Win' ? 'bg-bull/20 text-bull' : entry.outcome === 'Loss' ? 'bg-bear/20 text-bear' : 'bg-dark-600 text-dark-300'}`}>{entry.outcome || '-'}</span>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                    <div><span className="text-dark-500">{isKo ? '진입' : 'Entry'}</span><div className="mt-0.5 font-mono text-dark-200">{entry.entry_price?.toLocaleString() || '-'}</div></div>
                    <div><span className="text-dark-500">{isKo ? '청산' : 'Exit'}</span><div className="mt-0.5 font-mono text-dark-200">{entry.exit_price?.toLocaleString() || '-'}</div></div>
                    <div><span className="text-dark-500">{isKo ? '투입금 대비 수익률' : 'Margin return'}</span><div className={`mt-0.5 font-mono font-semibold ${(displayNetReturnPct || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>{displayNetReturnPct == null ? '-' : `${formatSignedNumber(displayNetReturnPct, 3)}%`}</div></div>
                    <div><span className="text-dark-500">{isKo ? '순수익금' : 'Net profit'}</span><div className={`mt-0.5 font-mono font-semibold ${pnl >= 0 ? 'text-bull' : 'text-bear'}`}>{entry.realized_pnl == null ? '-' : `${formatSignedNumber(entry.realized_pnl, 4)} USDT`}</div></div>
                  </div>
                  <div className="mt-3 flex items-center justify-between gap-3 border-t border-dark-800 pt-2">
                    <details>
                      <summary className="cursor-pointer list-none text-xs text-dark-500 hover:text-white">{isKo ? '세부 정보' : 'Details'}</summary>
                      <div className="mt-2 space-y-1 text-[11px] leading-4 text-dark-400">
                        {assessment && <><div className={assessment.tone === 'negative' ? 'font-semibold text-bear' : assessment.tone === 'warning' ? 'font-semibold text-amber-300' : 'font-semibold text-primary-300'}>{assessment.label}</div><div>{assessment.explanation}</div></>}
                        {entry.fee != null && <div>{isKo ? '수수료' : 'Fee'}: {formatSignedNumber(-Math.abs(entry.fee))} {entry.fee_currency || 'USDT'}</div>}
                        {entry.funding_fee != null && <div>{isKo ? '펀딩' : 'Funding'}: {formatSignedNumber(entry.funding_fee)} USDT</div>}
                      </div>
                    </details>
                    <div className="flex items-center gap-3">
                      {entry.datetime && entry.exit_price != null && <button type="button" onClick={() => setSnapshotEntry(entry)} className="text-amber-300 hover:text-amber-100" title={isKo ? '거래 리포트 및 차트' : 'Trade report and chart'}><CandlestickChart className="h-4 w-4" /></button>}
                      <button type="button" onClick={() => entry.id && deleteMutation.mutate(entry.id)} disabled={deleteMutation.isPending} className="text-dark-500 hover:text-red-400 disabled:opacity-50" aria-label={isKo ? '거래 삭제' : 'Delete trade'}><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
          {visibleEntries.length > displayedEntries.length && (
            <div className="mt-4 flex justify-center">
              <button
                type="button"
                onClick={() => setVisibleTradeCount((count) => count + 10)}
                className="border border-dark-600 bg-dark-900 px-4 py-2 text-xs text-dark-200 hover:border-primary-400/60 hover:text-white"
              >
                {isKo ? `거래 ${Math.min(10, visibleEntries.length - displayedEntries.length)}건 더 보기` : `Show ${Math.min(10, visibleEntries.length - displayedEntries.length)} more`}
              </button>
            </div>
          )}
          </>
        )}
      </div>

      {snapshotEntry && (
        <TradeReportModal
          entry={snapshotEntry}
          allEntries={entries || []}
          excursion={snapshotEntry.id == null ? null : excursionByJournalId.get(snapshotEntry.id) || null}
          excursionLoading={qualityQuery.isLoading}
          qualityItem={snapshotEntry.id == null ? null : qualityByJournalId.get(snapshotEntry.id) || null}
          isKo={isKo}
          onClose={() => setSnapshotEntry(null)}
          onBehaviorUpdated={async () => {
            await queryClient.invalidateQueries({ queryKey: journalQueryKeys.entries });
            await Promise.all(journalDerivedQueryPrefixes.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
          }}
        />
      )}
      {connectionOpen && (
        <DeepcoinConnectionModal
          isKo={isKo}
          isSaving={deepcoinConnectionMutation.isPending}
          error={deepcoinConnectionMutation.error}
          onSave={(values) => deepcoinConnectionMutation.mutate(values)}
          onClose={() => setConnectionOpen(false)}
        />
      )}

    </div>
  );
}
