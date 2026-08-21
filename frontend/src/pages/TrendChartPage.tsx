import { useEffect, useState } from 'react';
import { RefreshCw, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';
import ErrorNotice from '../components/ErrorNotice';
import { TrendPriceChart } from '../components/TrendPriceChart';
import { useHourlyRefresh } from '../hooks/useHourlyRefresh';
import { useTrendPriceChart } from '../hooks/useTrendPriceChart';
import { usePageCommon } from '../hooks/usePageCommon';
import { useSelectedCoin, useSelectedInterval } from '../store/useStore';
import type { Coin } from '../types';

function getChartHeight(): number {
  return Math.max(520, window.innerHeight - 118);
}

export default function TrendChartPage() {
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const { isKo } = usePageCommon();
  const safeCoin = (selectedCoin || 'BTC') as Coin;
  const [priceZoom, setPriceZoom] = useState(1);
  const [chartHeight, setChartHeight] = useState(getChartHeight);
  const {
    chartPriceLevels,
    isRefreshing,
    isTrendChartError,
    isTrendChartLoading,
    refresh: refreshData,
    selectedProjection,
    trendChartData,
    vpvrData,
  } =
    useTrendPriceChart(safeCoin, selectedInterval);

  useEffect(() => {
    const updateChartHeight = () => setChartHeight(getChartHeight());
    window.addEventListener('resize', updateChartHeight);
    return () => window.removeEventListener('resize', updateChartHeight);
  }, []);

  const refresh = useHourlyRefresh(refreshData);

  useEffect(() => {
    setPriceZoom(1);
  }, [safeCoin, selectedInterval]);

  const chartUnavailable = isTrendChartError && trendChartData.length === 0;
  const subtitle = [
    `${safeCoin} · ${selectedInterval}`,
    isKo ? `캔들 ${trendChartData.length}봉` : `${trendChartData.length} candles`,
    vpvrData && `VPVR ${vpvrData.candle_count}${isKo ? '봉' : ' candles'}`,
  ]
    .filter(Boolean)
    .join(' · ');

  return (
    <div className="flex min-h-[calc(100vh-48px)] flex-col gap-2">
      <header className="flex min-h-9 shrink-0 items-center justify-between gap-3 px-1">
        <div className="min-w-0">
          <h1 className="text-base font-semibold text-white">
            {isKo ? '추세분석 차트' : 'Trend Analysis Chart'}
          </h1>
          <div className="truncate text-xs text-dark-400">{subtitle}</div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5 text-xs text-dark-400">
          <span className="font-mono text-dark-300">{priceZoom.toFixed(2)}x</span>
          <button
            type="button"
            onClick={() => setPriceZoom((zoom) => Math.max(1, zoom / 1.25))}
            disabled={priceZoom === 1}
            className="rounded p-1.5 text-dark-300 hover:bg-dark-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            title={isKo ? '가격축 축소' : 'Zoom out price axis'}
            aria-label={isKo ? '가격축 축소' : 'Zoom out price axis'}
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setPriceZoom((zoom) => Math.min(4, zoom * 1.25))}
            disabled={priceZoom >= 4}
            className="rounded p-1.5 text-dark-300 hover:bg-dark-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            title={isKo ? '가격축 확대' : 'Zoom in price axis'}
            aria-label={isKo ? '가격축 확대' : 'Zoom in price axis'}
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setPriceZoom(1)}
            disabled={priceZoom === 1}
            className="rounded p-1.5 text-dark-300 hover:bg-dark-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            title={isKo ? '가격축 확대 초기화' : 'Reset price axis zoom'}
            aria-label={isKo ? '가격축 확대 초기화' : 'Reset price axis zoom'}
          >
            <RotateCcw className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={refresh}
            disabled={isRefreshing}
            className="rounded p-1.5 text-dark-300 hover:bg-dark-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            title={isKo ? '새로고침' : 'Refresh'}
            aria-label={isKo ? '새로고침' : 'Refresh'}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {isTrendChartLoading ? (
        <div className="flex items-center justify-center rounded-lg border border-dark-700 bg-dark-800/30 text-sm text-dark-400" style={{ height: chartHeight }}>
          {isKo ? '차트 데이터를 불러오는 중...' : 'Loading chart data...'}
        </div>
      ) : chartUnavailable ? (
        <div className="flex items-center justify-center" style={{ height: chartHeight }}>
          <div className="w-full max-w-xl">
            <ErrorNotice
              title={isKo ? '캔들 데이터를 불러오지 못했습니다' : 'Candle data is unavailable'}
              message={isKo ? '백엔드 연결 또는 Binance 데이터 응답을 확인할 수 없습니다.' : 'The backend or Binance data source did not respond.'}
              actionLabel={isKo ? '다시 불러오기' : 'Retry'}
              actionDisabled={isRefreshing}
              onAction={refresh}
            />
          </div>
        </div>
      ) : (
        <TrendPriceChart
          data={trendChartData}
          vpvr={vpvrData}
          vwaps={selectedProjection}
          priceLevels={chartPriceLevels}
          verticalZoom={priceZoom}
          isKo={isKo}
          height={chartHeight}
          baseHalfRangePercent={0.08}
        />
      )}
    </div>
  );
}
