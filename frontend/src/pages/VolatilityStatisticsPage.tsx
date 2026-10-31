import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getOHLCV } from '../api/market';
import { MARKET_INTERVAL_LABELS_KO } from '../constants/market';
import ErrorNotice from '../components/ErrorNotice';
import { useLanguage, useSelectedCoin, useSelectedInterval } from '../store/useStore';
import { getCompletedCandles } from '../utils/ohlcv';
import { formatNum } from '../utils/format';
import { getErrorMessage } from '../utils/error';
import { computeVolatilityStatistics, type VolatilityMetric, type VolatilityUnit } from '../utils/volatilityStatistics';

// The existing API accepts at most 10,000 rows, including the forming last bar.
const MAX_COMPLETED_BARS = 9_999;
const PAGE_SIZE = 50;
const METRICS: Array<{ key: VolatilityMetric; ko: string; en: string; color: string }> = [
  { key: 'rangeMean', ko: '봉 변동성 평균', en: 'Candle volatility mean', color: '#38bdf8' },
  { key: 'rangeMedian', ko: '봉 변동성 중위값', en: 'Candle volatility median', color: '#38bdf8' },
  { key: 'auw', ko: '윗꼬리 평균', en: 'Upper wick mean', color: '#fbbf24' },
  { key: 'muw', ko: '윗꼬리 중위값', en: 'Upper wick median', color: '#fbbf24' },
  { key: 'alw', ko: '아랫꼬리 평균', en: 'Lower wick mean', color: '#34d399' },
  { key: 'mlw', ko: '아랫꼬리 중위값', en: 'Lower wick median', color: '#34d399' },
];

export default function VolatilityStatisticsPage() {
  const isKo = useLanguage() === 'ko';
  const coin = useSelectedCoin();
  const interval = useSelectedInterval();
  const [settings, setSettings] = useState({ period: 14, count: 500, unit: 'percent' as VolatilityUnit });
  const [draftPeriod, setDraftPeriod] = useState('14');
  const [draftCount, setDraftCount] = useState('500');
  const [draftUnit, setDraftUnit] = useState<VolatilityUnit>('percent');
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [coin, interval]);
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
  const names = METRICS.map(metric => isKo ? metric.ko : metric.en);
  const pageCount = Math.max(1, Math.ceil(candles.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const offset = (currentPage - 1) * PAGE_SIZE;
  const rowIndices = Array.from({ length: Math.min(PAGE_SIZE, candles.length - offset) }, (_, index) => candles.length - 1 - offset - index);

  function apply(event: FormEvent) {
    event.preventDefault();
    if (valid) {
      setSettings({ period, count, unit: draftUnit });
      setPage(1);
    }
  }

  return (
    <div className="min-w-0 space-y-5">
      <header>
        <h1 className="text-2xl font-bold text-white">{isKo ? '변동성·꼬리 통계' : 'Volatility & Wick Statistics'}</h1>
        <p className="mt-1 text-sm text-dark-300">{coin} · {isKo ? MARKET_INTERVAL_LABELS_KO[interval] ?? interval : interval} · {isKo ? '봉 변동성·윗꼬리·아랫꼬리의 평균과 중위값' : 'Means and medians of candle volatility, upper wicks and lower wicks'}</p>
        <p className="mt-1 text-xs text-dark-400">{isKo ? '봉 변동성은 갭을 포함한 변동폭 기준 · 평균은 최근 N봉 산술평균(Wilder 평활평균과 다름)' : 'Candle volatility uses gap-inclusive candle ranges · means are arithmetic averages of N bars, not Wilder-smoothed averages'}</p>
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
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-flow-col xl:grid-cols-3 xl:grid-rows-2">
                {METRICS.map((metric, index) => <section key={metric.key} aria-label={names[index]} className="card p-4">
                  <h2 className="text-sm" style={{ color: metric.color }}>{names[index]}</h2>
                  <p className="mt-2 font-mono text-2xl text-white">{formatNum(values[metric.key][candles.length - 1])}{values[metric.key][candles.length - 1] != null ? suffix : ''}</p>
                </section>)}
              </div>
              <p className="text-xs text-dark-400">{isKo ? '최근 완료 봉 시작 시각' : 'Latest completed candle open time'}: {candles[candles.length - 1]?.open_dt}</p>
              <section className="card min-w-0 p-4">
                <h2 className="font-semibold text-white">{isKo ? '봉별 통계 테이블' : 'Per-candle statistics'}</h2>
                <p className="mt-1 text-xs text-dark-400">{isKo ? '최신 완료 봉부터 표시 · 페이지당 50봉 · 각 행은 해당 시점의 N기간 통계입니다. 표본 부족·비정상 값은 —로 표시합니다.' : 'Newest completed candles first · 50 rows per page · each row shows its N-period statistics. Insufficient or invalid values are shown as —.'}</p>
                <div className="mt-3 max-h-[600px] overflow-auto rounded border border-dark-700">
                  <table aria-label={isKo ? '봉별 변동성·꼬리 통계' : 'Per-candle volatility statistics'} className="w-full whitespace-nowrap text-right text-sm">
                    <thead className="sticky top-0 bg-dark-800 text-xs text-dark-300">
                      <tr>
                        <th scope="col" rowSpan={2} className="px-3 py-3 text-left">{isKo ? '봉 시작 시각' : 'Candle open time'}</th>
                        <th scope="col" rowSpan={2} className="px-3 py-3">{isKo ? '종가' : 'Close'}</th>
                        {[0, 2, 4].map(index => <th key={index} scope="colgroup" colSpan={2} className="px-3 pt-3 text-center" style={{ color: METRICS[index].color }}>
                          {index === 0 ? (isKo ? '봉 변동폭' : 'Candle range') : index === 2 ? (isKo ? '윗꼬리' : 'Upper wick') : (isKo ? '아랫꼬리' : 'Lower wick')}{suffix ? ` (${suffix})` : ''}
                        </th>)}
                      </tr>
                      <tr>
                        {METRICS.map((metric, index) => <th key={metric.key} scope="col" aria-label={`${names[index]}${suffix ? ` (${suffix})` : ''}`} className="px-3 pb-3 pt-2" style={{ color: metric.color }}>
                          {index % 2 === 0 ? (isKo ? '평균' : 'Mean') : (isKo ? '중위값' : 'Median')}
                        </th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {rowIndices.map(index => <tr key={candles[index].open_time} className="border-t border-dark-700/50 hover:bg-dark-700/30">
                        <th scope="row" className="px-3 py-2 text-left font-normal text-dark-300">{candles[index].open_dt}</th>
                        <td className="px-3 py-2 font-mono text-dark-200">{formatNum(candles[index].close)}</td>
                        {METRICS.map(metric => <td key={metric.key} className="px-3 py-2 font-mono text-dark-200">{formatNum(values[metric.key][index])}</td>)}
                      </tr>)}
                    </tbody>
                  </table>
                </div>
                <nav aria-label={isKo ? '봉별 통계 페이지' : 'Candle statistics pagination'} className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-dark-300">
                  <p aria-live="polite">{isKo ? `${offset + 1}–${offset + rowIndices.length} / ${candles.length}봉 · ${currentPage} / ${pageCount}페이지` : `${offset + 1}–${offset + rowIndices.length} of ${candles.length} candles · Page ${currentPage} of ${pageCount}`}</p>
                  <div className="flex gap-2">
                    <button type="button" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)} className="btn-secondary disabled:opacity-50">{isKo ? '이전 페이지' : 'Previous page'}</button>
                    <button type="button" disabled={currentPage === pageCount} onClick={() => setPage(currentPage + 1)} className="btn-secondary disabled:opacity-50">{isKo ? '다음 페이지' : 'Next page'}</button>
                  </div>
                </nav>
              </section>
            </>}
      <details className="card p-4 text-sm text-dark-300">
        <summary className="cursor-pointer font-semibold">{isKo ? '계산 기준과 해석 주의사항' : 'Calculation definitions and limitations'}</summary>
        <div className="mt-3 space-y-2 text-xs leading-relaxed">
          <p>{isKo ? '봉 변동폭 = max(고가 − 저가, |고가 − 이전 종가|, |저가 − 이전 종가|)' : 'Candle range = max(High − Low, |High − Previous Close|, |Low − Previous Close|)'}</p>
          <p>{isKo ? '봉 변동성은 갭을 포함한 변동폭입니다(봉 자체의 고가−저가와 다를 수 있음). 첫 봉은 이전 종가가 없어 고가−저가를 사용합니다. 평균은 최근 N개 값의 산술평균으로, Wilder 평활평균을 사용하지 않습니다.' : 'Candle volatility uses gap-inclusive candle ranges, which can differ from High−Low. The first loaded bar uses High−Low because its previous close is unavailable. Means are arithmetic averages of N observations, not Wilder-smoothed averages.'}</p>
          <p>{isKo ? '중위값은 최근 N개 값을 정렬한 중앙값입니다. 짝수 N은 가운데 두 값의 평균입니다. 여섯 항목 모두 같은 N개 완료 봉 기준입니다.' : 'Medians use the central value of the sorted N observations, averaging the central pair for even N. All six metrics use the same N completed bars.'}</p>
          <p>{isKo ? '윗꼬리 = High−max(Open, Close), 아랫꼬리 = min(Open, Close)−Low. 각 꼬리의 평균과 중위값을 따로 계산하며 길이 0도 포함합니다.' : 'Upper wick = High−max(Open, Close); lower wick = min(Open, Close)−Low. Each side has its own mean and median; zero wicks are included.'}</p>
          <p>{isKo ? '% 모드: 각 봉의 변동폭과 꼬리 길이를 해당 봉 종가로 나눠 ×100한 뒤 평균·중위값을 계산합니다. 여섯 항목의 단위는 모두 %입니다.' : '% mode: divide each candle\'s range and wick lengths by its own close ×100 before calculating means/medians. All six metrics are percentages.'}</p>
          <p>{isKo ? '완료 봉만 사용하며 미래 봉은 참조하지 않습니다. 부족한 표본·비정상 OHLC는 —. 비정상 봉 다음 변동폭도 이전 종가를 확인할 수 없어 미정입니다. API가 반환한 봉 수가 요청보다 적을 수 있습니다. 페이지를 이동해도 계산 표본은 바뀌지 않습니다.' : 'Completed candles only, with no future data. Insufficient/invalid OHLC produces —. The range after an invalid bar is also unavailable because its previous close cannot be validated. The API may return fewer bars than requested. Pagination does not change the calculation population.'}</p>
          <p>{isKo ? '평균·중위값은 과거 크기의 요약이며 방향 예측·손익 보장이 아닙니다. 계산은 반올림하지 않고 화면만 소수점 두 자리로 표시합니다.' : 'Means/medians describe historical sizes, not direction or guaranteed returns. Calculations are unrounded; display uses two decimals.'}</p>
        </div>
      </details>
    </div>
  );
}
