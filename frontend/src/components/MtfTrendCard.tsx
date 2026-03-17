import type { TrendIndicatorsResult } from '../types';
import {
  getStochState,
  getAlignedStochTail,
  getStochCross,
  getTrendBiasBadgeClass,
  getTrendBiasLabel,
  calculateTrendBias,
} from '../utils/trendAnalyzers';
import { formatNum } from '../utils/format';

export function MtfTrendCard({
  interval,
  isKo,
  selectedInterval,
  payload,
  isFetching,
}: {
  interval: string;
  isKo: boolean;
  selectedInterval: string;
  payload: TrendIndicatorsResult | null | undefined;
  isFetching: boolean;
}) {
  const latest = payload?.latest;
  const series = payload?.series || {};
  const hasData = !!payload?.success && !!latest;
  const isCurrent = selectedInterval === interval;

  if (!hasData) {
    return (
      <div className={`rounded-lg border border-dark-700 p-3 ${isCurrent ? 'ring-1 ring-primary-500/40' : ''}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs font-semibold text-white">{interval}</div>
          {isCurrent && <span className="text-[10px] text-primary-300">{isKo ? '현재' : 'Current'}</span>}
        </div>
        <div className="text-xs text-dark-400">
          {isFetching ? (isKo ? '불러오는 중...' : 'Loading...') : (isKo ? '데이터 없음' : 'No data')}
        </div>
      </div>
    );
  }

  const stochSeries5k = series.slow_stoch_5k;
  const stochSeries5d = series.slow_stoch_5d;
  const stochSeries10k = series.slow_stoch_10k;
  const stochSeries10d = series.slow_stoch_10d;
  const stochSeries20k = series.slow_stoch_20k;
  const stochSeries20d = series.slow_stoch_20d;

  const stochPair5 = getAlignedStochTail(stochSeries5k?.t, stochSeries5k?.v, stochSeries5d?.t, stochSeries5d?.v, 1)[0];
  const stochPair10 = getAlignedStochTail(stochSeries10k?.t, stochSeries10k?.v, stochSeries10d?.t, stochSeries10d?.v, 1)[0];
  const stochPair20 = getAlignedStochTail(stochSeries20k?.t, stochSeries20k?.v, stochSeries20d?.t, stochSeries20d?.v, 1)[0];

  const stoch5k = latest.slow_stoch_5k ?? stochPair5?.k ?? null;
  const stoch5d = latest.slow_stoch_5d ?? stochPair5?.d ?? null;
  const stoch10k = latest.slow_stoch_10k ?? stochPair10?.k ?? null;
  const stoch10d = latest.slow_stoch_10d ?? stochPair10?.d ?? null;
  const stoch20k = latest.slow_stoch_20k ?? stochPair20?.k ?? null;
  const stoch20d = latest.slow_stoch_20d ?? stochPair20?.d ?? null;

  const stochState5 = getStochState(stoch5k, stoch5d);
  const stochState10 = getStochState(stoch10k, stoch10d);
  const stochState20 = getStochState(stoch20k, stoch20d);

  const stochCross5 = getStochCross(stochSeries5k?.t, stochSeries5k?.v, stochSeries5d?.t, stochSeries5d?.v);
  const stochCross10 = getStochCross(stochSeries10k?.t, stochSeries10k?.v, stochSeries10d?.t, stochSeries10d?.v);
  const stochCross20 = getStochCross(stochSeries20k?.t, stochSeries20k?.v, stochSeries20d?.t, stochSeries20d?.v);

  const bias = calculateTrendBias(latest, stochState20);
  const stochRows = [
    { label: '5-3-3', k: stoch5k, d: stoch5d, state: stochState5, cross: stochCross5 },
    { label: '10-6-6', k: stoch10k, d: stoch10d, state: stochState10, cross: stochCross10 },
    { label: '20-12-12', k: stoch20k, d: stoch20d, state: stochState20, cross: stochCross20 },
  ] as const;

  return (
    <div className={`rounded-lg border border-dark-700 p-3 space-y-2 ${isCurrent ? 'ring-1 ring-primary-500/40' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold text-white">{interval}</div>
        {isCurrent && <span className="text-[10px] text-primary-300">{isKo ? '현재' : 'Current'}</span>}
      </div>
      <div className={`inline-flex rounded-md border px-2 py-1 text-[11px] font-medium ${getTrendBiasBadgeClass(bias)}`}>
        {getTrendBiasLabel(bias, isKo)}
      </div>
      <div className="grid grid-cols-2 gap-1 text-[11px] text-dark-300">
        <div>RSI: <span className="font-mono text-dark-100">{formatNum(latest.rsi, 1)}</span></div>
        <div>ADX: <span className="font-mono text-dark-100">{formatNum(latest.adx, 1)}</span></div>
        <div>MACD: <span className="font-mono text-dark-100">{formatNum(latest.macd_hist, 2)}</span></div>
        <div>ATR%: <span className="font-mono text-dark-100">{formatNum(latest.atr_pct, 2)}</span></div>
      </div>
      <div className="rounded-md border border-dark-700/80 p-2">
        <div className="text-[10px] text-dark-500 mb-1">
          {isKo ? 'Slow Stochastic (5-3-3 / 10-6-6 / 20-12-12)' : 'Slow Stochastic (5-3-3 / 10-6-6 / 20-12-12)'}
        </div>
        <div className="space-y-1">
          {stochRows.map((row) => (
            <div key={row.label} className="grid grid-cols-[58px_1fr_auto] items-center gap-1 text-[11px]">
              <span className="text-dark-400">{row.label}</span>
              <span className="font-mono text-dark-100">K {formatNum(row.k, 1)} / D {formatNum(row.d, 1)}</span>
              <span
                className={`font-medium ${
                  row.cross === 'golden' || row.state === 'golden'
                    ? 'text-primary-300'
                    : row.cross === 'dead' || row.state === 'dead'
                      ? 'text-red-300'
                      : 'text-dark-300'
                }`}
              >
                {row.cross === 'golden'
                  ? (isKo ? '골든' : 'Golden')
                  : row.cross === 'dead'
                    ? (isKo ? '데드' : 'Dead')
                    : row.state === 'golden'
                      ? (isKo ? '상승' : 'Bull')
                      : row.state === 'dead'
                        ? (isKo ? '하락' : 'Bear')
                        : (isKo ? '중립' : 'Flat')}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
