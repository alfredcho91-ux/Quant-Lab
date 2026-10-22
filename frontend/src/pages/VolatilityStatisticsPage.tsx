import { useMemo, useState, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { EChartsCoreOption } from 'echarts/core';
import { getOHLCV } from '../api/market';
import EChart from '../components/EChart';
import ErrorNotice from '../components/ErrorNotice';
import { useLanguage, useSelectedCoin, useSelectedInterval } from '../store/useStore';
import { getCompletedCandles } from '../utils/ohlcv';
import { formatNum } from '../utils/format';
import { getErrorMessage } from '../utils/error';
import { computeVolatilityStatistics, type VolatilityMetric, type VolatilityUnit } from '../utils/volatilityStatistics';

// The existing API accepts at most 10,000 rows, including the forming last bar.
const MAX_COMPLETED_BARS = 9_999;
const SERIES: Array<{ key: VolatilityMetric; ko: string; en: string; color: string }> = [
  { key: 'atr', ko: 'ATR · 평균 진폭', en: 'ATR · Average True Range', color: '#38bdf8' },
  { key: 'mtr', ko: 'MTR · 중앙값 진폭', en: 'MTR · Median True Range', color: '#a78bfa' },
  { key: 'upperStd', ko: '윗꼬리 표준편차', en: 'Upper wick standard deviation', color: '#fbbf24' },
  { key: 'lowerStd', ko: '아랫꼬리 표준편차', en: 'Lower wick standard deviation', color: '#34d399' },
];

export default function VolatilityStatisticsPage() {
  const isKo = useLanguage() === 'ko';
  const coin = useSelectedCoin();
  const interval = useSelectedInterval();
  const [settings, setSettings] = useState({ period: 14, count: 500, unit: 'percent' as VolatilityUnit });
  const [draftPeriod, setDraftPeriod] = useState('14');
  const [draftCount, setDraftCount] = useState('500');
  const [draftUnit, setDraftUnit] = useState<VolatilityUnit>('percent');
  const period = Number(draftPeriod);
  const count = Number(draftCount);
  const valid = Number.isSafeInteger(period) && period > 0 && Number.isSafeInteger(count) && count > 0 && count <= MAX_COMPLETED_BARS;
  const query = useQuery({
    queryKey: ['volatilityStatistics', coin, interval, settings.count],
    queryFn: async () => {
      const response = await getOHLCV(coin, interval, false, settings.count + 1);
      return { candles: getCompletedCandles(response.data, settings.count), source: response.source };
    },
    staleTime: 60 * 60 * 1000, retry: 1,
  });
  const candles = useMemo(() => query.data?.candles ?? [], [query.data]);
  const values = useMemo(() => computeVolatilityStatistics(candles, settings.period, settings.unit), [candles, settings.period, settings.unit]);
  const suffix = settings.unit === 'percent' ? '%' : '';
  const names = useMemo(() => SERIES.map(series => isKo ? series.ko : series.en), [isKo]);
  const option = useMemo<EChartsCoreOption>(() => {
    const categories = candles.map(row => row.open_dt);
    return {
      animation: false,
      legend: { top: 8, data: names, textStyle: { color: '#cbd5e1' } },
      tooltip: {
        trigger: 'axis', renderMode: 'richText', axisPointer: { type: 'cross' },
        // Candlestick aggregates are arrays; ECharts formats their individual
        // numeric OHLC dimensions separately. Do not label the array as missing.
        valueFormatter: (value: unknown) => typeof value === 'number' ? formatNum(value) : value == null ? '—' : '',
      },
      axisPointer: { link: [{ xAxisIndex: 'all' }], label: { precision: 2 } },
      grid: [{ left: 72, right: 28, top: 64, height: '36%' }, { left: 72, right: 28, top: '55%', bottom: 76 }],
      xAxis: [0, 1].map(index => ({
        type: 'category', gridIndex: index, data: categories, boundaryGap: true,
        axisLabel: { show: index === 1, color: '#94a3b8', hideOverlap: true },
        axisLine: { lineStyle: { color: '#334155' } },
      })),
      yAxis: [0, 1].map(index => ({
        type: 'value', gridIndex: index, scale: index === 0, ...(index === 1 ? { min: 0, name: suffix ? '% / %p' : (isKo ? '가격 단위' : 'Price units') } : {}),
        nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8', formatter: (value: number) => formatNum(value) },
        splitLine: { lineStyle: { color: '#334155' } },
      })),
      dataZoom: [{ type: 'inside', xAxisIndex: [0, 1] }, { type: 'slider', xAxisIndex: [0, 1], bottom: 12, height: 24 }],
      series: [
        { name: isKo ? '가격' : 'Price', type: 'candlestick', data: candles.map(row => [row.open, row.close, row.low, row.high]),
          itemStyle: { color: '#26a69a', color0: '#ef5350', borderColor: '#26a69a', borderColor0: '#ef5350' } },
        ...SERIES.map((series, index) => ({
          name: names[index], type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: values[series.key],
          showSymbol: false, connectNulls: false, itemStyle: { color: series.color }, lineStyle: { color: series.color, width: 2 },
        })),
      ],
    };
  }, [candles, values, names, isKo, suffix]);

  function apply(event: FormEvent) {
    event.preventDefault();
    if (valid) setSettings({ period, count, unit: draftUnit });
  }

  return (
    <div className="min-w-0 space-y-5">
      <header>
        <h1 className="text-2xl font-bold text-white">{isKo ? '변동성·꼬리 통계' : 'Volatility & Wick Statistics'}</h1>
        <p className="mt-1 text-sm text-dark-300">{coin} · {interval} · {isKo ? 'ATR / MTR / 윗꼬리·아랫꼬리 표준편차' : 'ATR / MTR / Upper and lower wick standard deviation'}</p>
      </header>
      <form onSubmit={apply} className="card flex flex-wrap items-end gap-4 p-4">
        <label className="text-sm text-dark-300">{isKo ? '계산 기간 N' : 'Calculation period N'}
          <input type="number" min="1" step="1" value={draftPeriod} onChange={event => setDraftPeriod(event.target.value)} className="mt-1 block w-36 rounded border border-dark-600 bg-dark-800 px-3 py-2" />
        </label>
        <label className="text-sm text-dark-300">{isKo ? '불러올 완료 봉 수' : 'Completed candles to load'}
          <input type="number" min="1" max={MAX_COMPLETED_BARS} step="1" value={draftCount} onChange={event => setDraftCount(event.target.value)} className="mt-1 block w-44 rounded border border-dark-600 bg-dark-800 px-3 py-2" />
        </label>
        <label className="text-sm text-dark-300">{isKo ? '단위' : 'Unit'}
          <select value={draftUnit} onChange={event => setDraftUnit(event.target.value as VolatilityUnit)} className="mt-1 block rounded border border-dark-600 bg-dark-800 px-3 py-2">
            <option value="percent">{isKo ? '종가 대비 %' : '% of close'}</option>
            <option value="price">{isKo ? '가격 절대값' : 'Absolute price'}</option>
          </select>
        </label>
        <button type="submit" disabled={!valid} className="btn-primary disabled:opacity-50">{isKo ? '설정 적용' : 'Apply settings'}</button>
        <button type="button" onClick={() => { void query.refetch(); }} disabled={query.isFetching} className="btn-secondary disabled:opacity-50">{isKo ? '새로고침' : 'Refresh'}</button>
        <p className="w-full text-xs text-dark-400">{isKo ? 'N은 양의 정수, 완료 봉 수는 1–9,999개. API 한도 10,000봉 중 마지막 진행 봉은 제외합니다. 적용 버튼을 눌러 계산하세요.' : 'N must be a positive integer; load 1–9,999 completed candles. The API allows 10,000 rows; the last forming candle is excluded. Apply settings to recalculate.'}</p>
        {!valid && <p role="alert" className="w-full text-sm text-amber-300">{isKo ? '기간과 봉 수를 허용 범위의 정수로 입력해주세요.' : 'Enter whole numbers within the supported ranges.'}</p>}
      </form>
      <p className="text-sm text-dark-300">{isKo ? `적용값: N=${settings.period} · 요청 ${settings.count}봉 · 실제 완료 ${candles.length}봉` : `Applied: N=${settings.period} · ${settings.count} requested · ${candles.length} completed`}{query.data?.source ? ` · ${query.data.source}` : ''}</p>
      {query.isPending ? <p role="status">{isKo ? '완료 봉을 불러오는 중...' : 'Loading completed candles...'}</p>
        : query.isError ? <ErrorNotice title={isKo ? '데이터를 불러오지 못했습니다' : 'Unable to load data'} message={getErrorMessage(query.error)} />
          : candles.length === 0 ? <p role="status" className="card p-5">{isKo ? '사용 가능한 완료 봉이 없습니다.' : 'No completed candles available.'}</p>
            : <>
              {candles.length < settings.period && <p role="status" className="text-amber-300">{isKo ? '계산 기간보다 완료 봉이 부족하여 통계는 —로 표시합니다.' : 'There are fewer completed candles than N; statistics are shown as —.'}</p>}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {SERIES.map((series, index) => <section key={series.key} aria-label={names[index]} className="card p-4">
                  <h2 className="text-sm" style={{ color: series.color }}>{names[index]}</h2>
                  <p className="mt-2 font-mono text-2xl text-white">{formatNum(values[series.key][candles.length - 1])}{values[series.key][candles.length - 1] != null ? (suffix && (series.key === 'upperStd' || series.key === 'lowerStd') ? '%p' : suffix) : ''}</p>
                </section>)}
              </div>
              <p className="text-xs text-dark-400">{isKo ? '최근 완료 봉 시작 시각' : 'Latest completed candle open time'}: {candles[candles.length - 1]?.open_dt}</p>
              <section aria-label={isKo ? '변동성 시계열 차트' : 'Volatility time-series chart'} className="card min-w-0 overflow-hidden p-2">
                <EChart option={option} height={680} />
                <p className="px-3 pb-2 text-xs text-dark-400">{isKo ? '범례를 눌러 지표 표시를 전환하고, 하단 슬라이더로 두 패널의 조회 구간을 함께 조절합니다.' : 'Toggle series using the legend; the bottom slider adjusts both panels together.'}</p>
              </section>
            </>}
      <details className="card p-4 text-sm text-dark-300">
        <summary className="cursor-pointer font-semibold">{isKo ? '계산 기준과 해석 주의사항' : 'Calculation definitions and limitations'}</summary>
        <div className="mt-3 space-y-2 text-xs leading-relaxed">
          <p>TR = max(High − Low, |High − Previous Close|, |Low − Previous Close|)</p>
          <p>{isKo ? 'ATR: 기존 핵심 엔진과 같은 Wilder 평활(α=1/N). 첫 TR은 High−Low이며 첫 TR부터 평활하고 N개 이후 표시합니다. 데이터 시작점·불러온 봉 수가 달라지면 초기값 영향으로 ATR이 달라질 수 있습니다.' : 'ATR: Wilder smoothing (α=1/N), matching the core engine. The first TR is High−Low; smoothing starts at that TR and is displayed after N observations. Changing the loaded history changes initialization and can affect ATR.'}</p>
          <p>{isKo ? 'MTR: 최근 N개 TR의 중앙값. 짝수 N은 가운데 두 값의 평균입니다.' : 'MTR: median of the last N true ranges; even windows average the central pair.'}</p>
          <p>{isKo ? '윗꼬리 = High−max(Open, Close), 아랫꼬리 = min(Open, Close)−Low. 표준편차 = √(Σ(x−평균)²/N), 모집단 기준(ddof=0). 길이 0도 포함합니다.' : 'Upper wick = High−max(Open, Close); lower wick = min(Open, Close)−Low. Population standard deviation = √(Σ(x−mean)²/N), ddof=0. Zero wicks are included.'}</p>
          <p>{isKo ? '% 모드: ATR·MTR은 가격 단위 통계를 해당 시점 종가로 나눠 ×100. 꼬리는 각 봉 종가 대비 %로 먼저 변환한 뒤 표준편차를 계산합니다. 꼬리 표준편차의 단위는 %p입니다.' : '% mode: ATR/MTR are divided by the current candle close ×100 after aggregation. Wick lengths are normalized by each candle close before calculating standard deviation; wick standard deviation is in percentage points.'}</p>
          <p>{isKo ? '완료 봉만 사용하며 미래 봉은 참조하지 않습니다. 부족한 표본·비정상 OHLC는 —. 비정상 봉 이후 TR은 이전 종가를 확인할 수 없어 한 봉 더 미정이며 ATR은 유효 TR N개로 다시 준비합니다. API가 반환한 봉 수가 요청보다 적을 수 있습니다. 가격 차트는 원본 응답을 표시하며 통계 유효성과는 별개입니다.' : 'Completed candles only, with no future data. Insufficient/invalid OHLC produces —. An invalid candle also makes the next TR unavailable; ATR restarts with N valid TR observations. The API may return fewer bars than requested. Price candles display the original response independently of statistic validity.'}</p>
          <p>{isKo ? '표준편차는 꼬리 길이의 산포이며 방향 예측·손익 보장이 아닙니다. 계산은 반올림하지 않고 화면만 소수점 두 자리로 표시합니다.' : 'Standard deviation describes dispersion, not direction or guaranteed returns. Calculations are unrounded; display uses two decimals.'}</p>
        </div>
      </details>
    </div>
  );
}
