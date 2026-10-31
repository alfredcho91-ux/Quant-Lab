import { useState, type FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getStopLossCandleStatistics, type CandleMetric, type CandleStatisticsConfig, type Distribution } from '../api/stopLossLab';
import { useSelectedCoin } from '../store/useStore';
import { getErrorMessage } from '../utils/error';
import { formatNum } from '../utils/format';
import ErrorNotice from './ErrorNotice';
import EChart from './EChart';
import VolatilityStatisticsPage from '../pages/VolatilityStatisticsPage';

const control = 'mt-1 block w-full min-w-0 rounded border border-dark-600 bg-dark-800 px-3 py-2 text-white';
const cell = 'whitespace-nowrap border-b border-dark-700 px-3 py-2 text-right';

export default function StopLossCandleStatistics({ ko }: { ko: boolean }) {
  const selectedCoin = useSelectedCoin();
  const [draft, setDraft] = useState<CandleStatisticsConfig>({ coin: selectedCoin, candles: 90, lookback: 14 });
  const [scope, setScope] = useState<'all' | 'weekend'>('all');
  const [metric, setMetric] = useState<CandleMetric>('upper');
  const [legacyOpen, setLegacyOpen] = useState(false);
  const mutation = useMutation({ mutationFn: getStopLossCandleStatistics, retry: false });
  const stale = Boolean(mutation.data && mutation.variables && JSON.stringify(draft) !== JSON.stringify(mutation.variables));
  const distribution = mutation.data?.distributions[scope];
  const selected = distribution?.metrics[metric].percent_open;
  const valid = Number.isSafeInteger(draft.candles) && draft.candles >= 1 && draft.candles <= 10000;
  const labels: Record<CandleMetric, string> = {
    upper: ko ? '윗꼬리' : 'Upper wick', lower: ko ? '아랫꼬리' : 'Lower wick',
    tr: ko ? '봉 변동폭' : 'Candle range', atr: ko ? '평균 변동폭' : 'Average range', mtr: ko ? '변동폭 중위값' : 'Median range',
  };

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!valid) return;
    mutation.mutate(draft);
  }

  return <div className="space-y-5">
    <form onSubmit={submit} className="card space-y-4 p-4">
      <div><h2 className="text-xl font-semibold">{ko ? '봉 통계 조회' : 'Candle statistics'}</h2><p className="mt-1 text-sm text-dark-300">{ko ? '최근 완료된 일봉을 입력한 개수만큼 조회합니다. 진행 중인 봉과 지표 계산용 준비 봉은 표본에서 제외합니다. 주말 표본은 조회한 봉 중 토·일 봉입니다.' : 'Load the requested number of recent completed daily candles. Forming and indicator warmup candles are excluded from the sample. Weekend samples are the Sat/Sun candles within those bars.'}</p></div>
      <div className="grid gap-4 sm:grid-cols-3">
        <label className="text-sm text-dark-200">{ko ? '종목' : 'Symbol'}<select aria-label={ko ? '통계 종목' : 'Statistics symbol'} className={control} value={draft.coin} onChange={e => setDraft(v => ({ ...v, coin: e.target.value }))}>{['BTC', 'ETH', 'SOL'].map(v => <option key={v}>{v}</option>)}</select></label>
        <label className="text-sm text-dark-200">{ko ? '조회 봉 수' : 'Candle count'}<input aria-label={ko ? '조회 봉 수' : 'Statistics candle count'} className={control} type="number" min={1} max={10000} step={1} required value={draft.candles || ''} onChange={e => setDraft(v => ({ ...v, candles: Number(e.target.value) }))} /></label>
        <label className="text-sm text-dark-200">{ko ? '표본 범위' : 'Sample'}<select className={control} aria-label={ko ? '표본 범위' : 'Sample'} value={scope} onChange={e => setScope(e.target.value as typeof scope)}><option value="all">{ko ? '전체 일봉' : 'All daily candles'}</option><option value="weekend">{ko ? '주말 (토·일)' : 'Weekend (Sat/Sun)'}</option></select></label>
      </div>
      <button type="submit" className="rounded bg-sky-500 px-5 py-3 font-semibold text-dark-950 disabled:opacity-50" disabled={mutation.isPending || !valid}>{mutation.isPending ? (ko ? '통계 조회 중…' : 'Loading statistics…') : (ko ? '통계 조회' : 'Load statistics')}</button>
    </form>
    {mutation.error && <ErrorNotice title={ko ? '봉 통계를 불러오지 못했습니다' : 'Unable to load candle statistics'} message={getErrorMessage(mutation.error)} />}
    {stale && <p role="status" className="text-amber-300">{ko ? '조회 조건이 변경되었습니다. 아래 결과는 이전 조건 기준입니다.' : 'Filters changed. Results below belong to the previous request.'}</p>}
    {distribution && mutation.data && <section className="card space-y-4 p-4" aria-label={ko ? '봉 통계 결과' : 'Candle statistics results'}>
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-semibold">{scope === 'weekend' ? (ko ? '주말 봉 통계' : 'Weekend candle statistics') : (ko ? '전체 봉 통계' : 'All candle statistics')}</h2><p className="mt-1 text-sm text-dark-300">{mutation.data.config.coin} · {ko ? `최근 완료 일봉 ${mutation.data.config.candles}개 요청 · 실제 확보 ${mutation.data.data.candle_count}개` : `Requested ${mutation.data.config.candles} recent completed daily candles · available ${mutation.data.data.candle_count}`}</p></div><div className="rounded bg-dark-800 px-4 py-3"><div className="text-xs text-dark-300">{ko ? '완료 일봉 표본' : 'Completed daily samples'}</div><div className="font-mono text-2xl">{distribution.candle_count}</div></div></div>
      {mutation.data.data.candle_count < mutation.data.config.candles && <p role="status" className="text-sm text-amber-300">{ko ? '요청한 봉 수보다 데이터가 부족합니다. 통계는 실제 확보한 봉만 사용합니다.' : 'Fewer candles are available than requested. Statistics use only the available candles.'}</p>}
      {scope === 'weekend' && <div className="text-sm text-dark-300">{ko ? '토요일 / 일요일' : 'Saturday / Sunday'}: {mutation.data.distributions.weekend.day_counts.Saturday} / {mutation.data.distributions.weekend.day_counts.Sunday}</div>}
      {distribution.candle_count === 0 ? <p>{ko ? '조회한 봉 중 해당 표본에 포함되는 완료 일봉이 없습니다.' : 'No completed daily candles match this sample.'}</p> : <>
        <div className="grid gap-3 sm:grid-cols-3">{(['upper', 'lower', 'tr'] as const).map(key => <button type="button" key={key} aria-pressed={metric === key} onClick={() => setMetric(key)} className={`rounded border p-3 text-left ${metric === key ? 'border-sky-400 bg-sky-950/30' : 'border-dark-700 bg-dark-800'}`}><div className="text-sm text-dark-300">{labels[key]}</div><div className="mt-1 font-mono text-lg">{ko ? '중위값' : 'Median'} {formatNum(distribution.metrics[key].percent_open.p50)}%</div><div className="text-sm">{ko ? '90% 기준값' : '90% threshold'} {formatNum(distribution.metrics[key].percent_open.p90)}%</div></button>)}</div>
        <p className="text-xs text-dark-300">{ko ? '중위값은 관측 봉을 작은 값부터 정렬했을 때 가운데 값입니다. 90% 기준값은 관측 봉 약 90%가 해당 값 이하였다는 뜻입니다. 다른 기준값도 같은 방식으로 읽습니다. 미래 확률이나 손절 성공률을 의미하지 않습니다.' : 'The median is the middle value when observations are sorted. The 90% threshold means about 90% of observed candles were at or below that value; other thresholds work the same way. These are not future probabilities or stop-success rates.'}</p>
        <p className="text-xs text-dark-300">{ko ? `봉 변동폭은 이전 종가와의 가격 차이(갭)를 포함합니다. 평균 변동폭은 ${mutation.data.config.lookback}봉 기준 Wilder 평활평균이며 단순 산술평균과 다릅니다. 변동폭 중위값은 같은 ${mutation.data.config.lookback}봉 변동폭의 중위값입니다.` : `Candle range includes gaps from the previous close. Average range uses Wilder smoothing over ${mutation.data.config.lookback} candles, not a simple arithmetic mean. Median range is the median of the same ${mutation.data.config.lookback} candle ranges.`}</p>
        <label className="block max-w-xs text-sm">{ko ? '차트 지표' : 'Chart metric'}<select className={control} value={metric} onChange={e => setMetric(e.target.value as CandleMetric)}>{(Object.keys(labels) as CandleMetric[]).map(key => <option key={key} value={key}>{labels[key]}</option>)}</select></label>
        {selected && <EChart height={260} option={{ backgroundColor: 'transparent', tooltip: { trigger: 'axis' }, grid: { left: 55, right: 20, bottom: 60, top: 25 }, xAxis: { type: 'category', name: '%', data: selected.histogram.map(v => `${formatNum(v.lower)}–${formatNum(v.upper)}`), axisLabel: { rotate: 35 } }, yAxis: { type: 'value', name: 'N' }, series: [{ type: 'bar', data: selected.histogram.map(v => v.count), itemStyle: { color: '#38bdf8' } }] }} />}
        <details><summary className="cursor-pointer font-medium">{ko ? '전체 상세 통계 보기' : 'View full statistics'}</summary><DistributionTable distribution={distribution.metrics} ko={ko} labels={labels} /></details>
      </>}
      <details className="text-xs"><summary>{ko ? '데이터 재현 정보' : 'Data reproducibility'}</summary><pre className="mt-2 max-h-56 overflow-auto">{JSON.stringify(mutation.data.data, null, 2)}</pre></details>
    </section>}
    <details className="card p-4" onToggle={e => setLegacyOpen(e.currentTarget.open)}><summary className="cursor-pointer font-semibold">{ko ? '기존 봉별 통계 (상세)' : 'Legacy candle statistics (advanced)'}</summary><p className="mt-3 text-sm text-amber-300">{ko ? '기존 표는 종가 기준 %와 봉 변동폭의 산술평균을 사용하므로 위 시가 기준 통계와 계산 기준이 다릅니다.' : 'The legacy table uses close-based percentages and arithmetic candle-range means, so its basis differs from the open-based summary above.'}</p>{legacyOpen && <div className="mt-4"><VolatilityStatisticsPage /></div>}</details>
  </div>;
}

function DistributionTable({ distribution, labels, ko }: { distribution: Record<string, { price: Distribution; percent_open: Distribution } | Distribution>; labels: Record<CandleMetric, string>; ko: boolean }) {
  const rows = (['upper', 'lower', 'tr', 'atr', 'mtr'] as CandleMetric[]).map(key => [labels[key], (distribution[key] as { percent_open: Distribution }).percent_open] as const);
  return <div className="mt-3 overflow-x-auto"><table className="w-full text-sm"><thead><tr>{[ko ? '지표 (%/시가)' : 'Metric (%/open)', 'N', ko ? '평균' : 'Mean', ko ? '중위값' : 'Median', ...[75, 90, 95, 99].map(value => ko ? `${value}% 기준값` : `${value}% threshold`)].map(v => <th className={cell} key={v}>{v}</th>)}</tr></thead><tbody>{rows.map(([name, d]) => <tr key={name}><th className={cell}>{name}</th>{(['count', 'mean', 'p50', 'p75', 'p90', 'p95', 'p99'] as const).map(key => <td className={cell} key={key}>{formatNum(d[key])}</td>)}</tr>)}</tbody></table></div>;
}
