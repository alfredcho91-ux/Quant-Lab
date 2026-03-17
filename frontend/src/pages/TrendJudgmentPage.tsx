// 추세판단 페이지 - Slow Stochastic, MACD, ADX, RSI, VWAP, Supertrend (사이드바 코인/타임프레임 연동)
import { useQuery, useQueries } from '@tanstack/react-query';
import { runTrendIndicators } from '../api/client';
import { useSelectedCoin, useSelectedInterval } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { TrendingUp, RefreshCw } from 'lucide-react';
import { IndicatorCard } from '../components/IndicatorCard';
import { MiniChart } from '../components/MiniChart';
import { StochMiniChart } from '../components/StochMiniChart';
import { MtfTrendCard } from '../components/MtfTrendCard';
import { IndicatorProjectionCard } from '../components/IndicatorProjectionCard';
import type { Coin } from '../types';
import {
  getStochState,
  getStochStateFromSeries,
  getStochCross,
} from '../utils/trendAnalyzers';






const ENABLE_MTF_SNAPSHOT = true;
const MTF_INTERVALS = ['1h', '4h', '1d', '1w'] as const;




export default function TrendJudgmentPage() {
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const { isKo } = usePageCommon();
  const safeCoin = (selectedCoin || 'BTC') as Coin;

  const { data, refetch, isFetching } = useQuery({
    queryKey: ['trendIndicators', safeCoin, selectedInterval],
    queryFn: () => runTrendIndicators({ coin: safeCoin, interval: selectedInterval, use_csv: false }),
    enabled: true,
  });

  const mtfQueries = useQueries({
    queries: MTF_INTERVALS.map((interval) => ({
      queryKey: ['trendIndicators', safeCoin, interval],
      queryFn: () => runTrendIndicators({ coin: safeCoin, interval, use_csv: false }),
      enabled: ENABLE_MTF_SNAPSHOT,
      staleTime: 30_000,
    })),
  });

  const latest = data?.latest;
  const series = data?.series || {};
  const hasData = !!data?.success && !!latest;

  const stoch5k = latest?.slow_stoch_5k ?? null;
  const stoch5d = latest?.slow_stoch_5d ?? null;
  const stoch10k = latest?.slow_stoch_10k ?? null;
  const stoch10d = latest?.slow_stoch_10d ?? null;
  const stoch20k = latest?.slow_stoch_20k ?? null;
  const stoch20d = latest?.slow_stoch_20d ?? null;

  const stochSeries5k = series.slow_stoch_5k;
  const stochSeries5d = series.slow_stoch_5d;
  const stochSeries10k = series.slow_stoch_10k;
  const stochSeries10d = series.slow_stoch_10d;
  const stochSeries20k = series.slow_stoch_20k;
  const stochSeries20d = series.slow_stoch_20d;

  const stochState5 =
    getStochState(stoch5k, stoch5d) ??
    getStochStateFromSeries(stochSeries5k?.t, stochSeries5k?.v, stochSeries5d?.t, stochSeries5d?.v);
  const stochState10 =
    getStochState(stoch10k, stoch10d) ??
    getStochStateFromSeries(stochSeries10k?.t, stochSeries10k?.v, stochSeries10d?.t, stochSeries10d?.v);
  const stochState20 =
    getStochState(stoch20k, stoch20d) ??
    getStochStateFromSeries(stochSeries20k?.t, stochSeries20k?.v, stochSeries20d?.t, stochSeries20d?.v);

  const stochCross5 = getStochCross(stochSeries5k?.t, stochSeries5k?.v, stochSeries5d?.t, stochSeries5d?.v);
  const stochCross10 = getStochCross(stochSeries10k?.t, stochSeries10k?.v, stochSeries10d?.t, stochSeries10d?.v);
  const stochCross20 = getStochCross(stochSeries20k?.t, stochSeries20k?.v, stochSeries20d?.t, stochSeries20d?.v);
  const isMtfFetching = ENABLE_MTF_SNAPSHOT && mtfQueries.some((query) => query.isFetching);

  const stochBlockBg = (state: 'golden' | 'dead' | null) =>
    state === 'golden' ? 'bg-primary-500/10 border-primary-500/20' : state === 'dead' ? 'bg-red-500/10 border-red-500/20' : '';

  const handleRefresh = () => {
    void refetch();
    if (ENABLE_MTF_SNAPSHOT) {
      mtfQueries.forEach((query) => {
        void query.refetch();
      });
    }
  };

  const stochConfigs = [
    {
      label: '5-3-3',
      k: stoch5k,
      d: stoch5d,
      state: stochState5,
      cross: stochCross5,
      seriesK: stochSeries5k,
      seriesD: stochSeries5d,
    },
    {
      label: '10-6-6',
      k: stoch10k,
      d: stoch10d,
      state: stochState10,
      cross: stochCross10,
      seriesK: stochSeries10k,
      seriesD: stochSeries10d,
    },
    {
      label: '20-12-12',
      k: stoch20k,
      d: stoch20d,
      state: stochState20,
      cross: stochCross20,
      seriesK: stochSeries20k,
      seriesD: stochSeries20d,
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-400" />
            {isKo ? '추세판단' : 'Trend Judgment'}
          </h1>
          <p className="text-dark-400 text-sm mt-0.5">
            {isKo ? 'Slow Stochastic, MACD, ADX, RSI, VWAP, Supertrend 지표 종합' : 'Slow Stochastic, MACD, ADX, RSI, VWAP, Supertrend indicators'}
          </p>
        </div>
        <div className="flex items-center gap-2 text-dark-400 text-sm">
          <span>{safeCoin}</span>
          <span>·</span>
          <span>{selectedInterval}</span>
          <button
            onClick={handleRefresh}
            disabled={isFetching || isMtfFetching}
            className="p-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 disabled:opacity-50"
            title={isKo ? '새로고침' : 'Refresh'}
          >
            <RefreshCw className={`w-4 h-4 ${isFetching || isMtfFetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <IndicatorProjectionCard coin={safeCoin} interval="1h" />
        <IndicatorProjectionCard coin={safeCoin} interval="4h" />
        <IndicatorProjectionCard coin={safeCoin} interval="1d" />
      </div>

      {ENABLE_MTF_SNAPSHOT && (
        <div className="card p-4">
          <div className="flex items-center justify-between gap-2 mb-3">
            <h2 className="text-sm font-semibold text-white">
              {isKo ? 'MTF 스냅샷 (1h·4h·1d·1w)' : 'MTF Snapshot (1h·4h·1d·1w)'}
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded border border-amber-500/30 text-amber-300 bg-amber-500/10">
              Beta
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
            {MTF_INTERVALS.map((interval, index) => (
              <MtfTrendCard
                key={interval}
                interval={interval}
                isKo={isKo}
                selectedInterval={selectedInterval}
                payload={interval === selectedInterval ? data : mtfQueries[index]?.data}
                isFetching={interval === selectedInterval ? isFetching : !!mtfQueries[index]?.isFetching}
              />
            ))}
          </div>
        </div>
      )}

      {!hasData && !isFetching && (
        <div className="card p-6 text-center text-dark-500 text-sm">{isKo ? '데이터를 불러오지 못했습니다.' : 'Failed to load data.'}</div>
      )}

      {hasData && (
        <>
          {/* RSI 그래프 맨 위 (수치 표기 포함) */}
          <div className="card p-4">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-sm font-semibold text-white">RSI(14)</h2>
              <span className={`text-sm font-mono font-bold ${latest.rsi != null && latest.rsi > 50 ? 'text-primary-400' : 'text-red-400'}`}>
                {latest.rsi != null ? latest.rsi.toFixed(1) : '—'}
              </span>
            </div>
            <div className="w-full" style={{ minHeight: 96 }}>
              <MiniChart t={series.rsi?.t ?? []} v={series.rsi?.v ?? []} yRefs={[30, 70]} height={96} />
            </div>
          </div>

          {/* Indicator Cards (RSI 제외) */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 w-full">
            <IndicatorCard label="ADX" value={latest.adx} sub={latest.adx != null && latest.adx > 25 ? (isKo ? '추세강함' : 'Strong') : (isKo ? '약함' : 'Weak')} bullish={null} />
            <IndicatorCard
              label="ATR%"
              value={latest.atr_pct}
              sub={
                latest.atr_pct != null
                  ? latest.atr_pct >= 2
                    ? (isKo ? '고변동성' : 'High Vol')
                    : latest.atr_pct >= 1
                      ? (isKo ? '보통 변동성' : 'Normal Vol')
                      : (isKo ? '저변동성' : 'Low Vol')
                  : undefined
              }
              bullish={null}
            />
            <IndicatorCard label="MACD Hist" value={latest.macd_hist} bullish={latest.macd_hist != null ? latest.macd_hist > 0 : null} />
            <IndicatorCard label="VWAP(20)" value={latest.vwap_20} bullish={latest.close != null && latest.vwap_20 != null ? latest.close > latest.vwap_20 : null} />
            <IndicatorCard label="Supertrend" value={latest.supertrend} bullish={latest.supertrend_dir != null ? latest.supertrend_dir > 0 : null} />
          </div>

          {/* 3 Slow Stochastic 세로 배치 (표시 순서: 5/10/20) */}
          <div className="card p-4">
            <h2 className="text-sm font-semibold text-white mb-3">{isKo ? 'Slow Stochastic (3 기간)' : 'Slow Stochastic (3 periods)'}</h2>
            <div className="flex flex-col gap-3">
              {stochConfigs.map((config) => (
                <div
                  key={config.label}
                  className={`space-y-1 border rounded-lg border-dark-700 pb-3 px-2 pt-1 ${stochBlockBg(config.state)}`}
                >
                  <div className="flex justify-between text-xs">
                    <span className="text-dark-400">{config.label}</span>
                    <span className="flex gap-3">
                      <span className="text-primary-400">K: {config.k != null ? config.k.toFixed(1) : '—'}</span>
                      <span className="text-amber-500">D: {config.d != null ? config.d.toFixed(1) : '—'}</span>
                      {config.cross && (
                        <span className={config.cross === 'golden' ? 'text-primary-400' : 'text-red-400'}>
                          {config.cross === 'golden' ? (isKo ? '골든크로스' : 'Golden') : (isKo ? '데드크로스' : 'Dead')}
                        </span>
                      )}
                    </span>
                  </div>
                  <StochMiniChart
                    tk={config.seriesK?.t ?? []}
                    vk={config.seriesK?.v ?? []}
                    vd={config.seriesD?.v}
                    yRefs={[20, 80]}
                    height={100}
                  />
                </div>
              ))}
            </div>
          </div>
        </>
      )}

    </div>
  );
}
