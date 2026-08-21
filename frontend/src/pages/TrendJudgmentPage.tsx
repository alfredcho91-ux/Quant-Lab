// 추세판단 페이지 - Slow Stochastic, MACD, ADX, RSI, VWAP, Supertrend (사이드바 코인/타임프레임 연동)
import { useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { runTrendIndicators } from '../api/client';
import { useSelectedCoin, useSelectedInterval } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { RefreshCw, TrendingUp } from 'lucide-react';
import { MiniChart } from '../components/MiniChart';
import { StochMiniChart } from '../components/StochMiniChart';
import { IndicatorProjectionCard } from '../components/IndicatorProjectionCard';
import { MomentumIndicatorPanels } from '../components/MomentumIndicatorPanels';
import { VPVRTable } from '../components/VPVRTable';
import ErrorNotice from '../components/ErrorNotice';
import type { Coin } from '../types';
import { PRICE_PROJECTION_INTERVALS, TREND_PRICE_QUERY_OPTIONS, useTrendPriceChart } from '../hooks/useTrendPriceChart';
import { useHourlyRefresh } from '../hooks/useHourlyRefresh';
import {
  getStochState,
  getStochStateFromSeries,
  getStochCross,
} from '../utils/trendAnalyzers';

export default function TrendJudgmentPage() {
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const { isKo } = usePageCommon();
  const safeCoin = (selectedCoin || 'BTC') as Coin;
  const trendPriceData = useTrendPriceChart(safeCoin, selectedInterval, { includeChart: false });

  const { data, refetch: refetchTrendIndicators, isFetching } = useQuery({
    queryKey: ['trendIndicators', safeCoin, selectedInterval],
    queryFn: () => runTrendIndicators({ coin: safeCoin, interval: selectedInterval, use_csv: false }),
    ...TREND_PRICE_QUERY_OPTIONS,
  });

  const latest = data?.latest;
  const series = data?.series || {};
  const hasData = !!data?.success && !!latest;
  const {
    vpvrData,
    isVPVRLoading,
    isRefreshing: isTrendPriceRefreshing,
    projectionQueries,
    refresh: refreshTrendPriceData,
  } = trendPriceData;

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
  const stochBlockBg = (state: 'golden' | 'dead' | null) =>
    state === 'golden' ? 'bg-primary-500/10 border-primary-500/20' : state === 'dead' ? 'bg-red-500/10 border-red-500/20' : '';

  const refreshAll = useCallback(() => {
    void refetchTrendIndicators();
    refreshTrendPriceData();
  }, [refetchTrendIndicators, refreshTrendPriceData]);

  const refresh = useHourlyRefresh(refreshAll);

  const isRefreshing = isFetching || isTrendPriceRefreshing;

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
            {isKo ? 'Slow Stochastic, Stoch RSI, MACD, ADX, RSI, VWAP, Supertrend 지표 종합' : 'Slow Stochastic, Stoch RSI, MACD, ADX, RSI, VWAP, Supertrend indicators'}
          </p>
        </div>
        <div className="flex items-center gap-2 text-dark-400 text-sm">
          <span>{safeCoin}</span>
          <span>·</span>
          <span>{selectedInterval}</span>
          <button
            onClick={refresh}
            disabled={isRefreshing}
            className="p-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 disabled:opacity-50"
            title={isKo ? '새로고침' : 'Refresh'}
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {PRICE_PROJECTION_INTERVALS.map((interval, index) => (
          <IndicatorProjectionCard
            key={interval}
            interval={interval}
            isKo={isKo}
            data={projectionQueries[index]?.data}
            isLoading={projectionQueries[index]?.isLoading ?? false}
            isError={projectionQueries[index]?.isError ?? false}
          />
        ))}
      </div>

      <VPVRTable data={vpvrData} isLoading={isVPVRLoading} isKo={isKo} />

      {!hasData && !isFetching && (
        <ErrorNotice
          title={isKo ? '핵심 추세 지표를 불러오지 못했습니다' : 'Trend indicators are unavailable'}
          message={isKo ? '백엔드 연결 또는 Binance 데이터 응답을 확인할 수 없습니다.' : 'The backend or Binance data source did not respond.'}
          actionLabel={isKo ? '다시 불러오기' : 'Retry'}
          actionDisabled={isRefreshing}
          onAction={refresh}
        />
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
              <MiniChart
                t={series.rsi?.t ?? []}
                v={series.rsi?.v ?? []}
                volume={series.volume}
                yRefs={[30, 70]}
                height={96}
              />
            </div>
          </div>

          {data && <MomentumIndicatorPanels isKo={isKo} payload={data} />}

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
