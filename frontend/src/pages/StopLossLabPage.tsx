import { useState, type FormEvent, type ReactNode } from 'react';
import { useMutation } from '@tanstack/react-query';
import { analyzeStopLossLab, type LabConfig, type DistanceMode } from '../api/stopLossLab';
import { useLanguage, useSelectedCoin } from '../store/useStore';
import { getErrorMessage } from '../utils/error';
import ErrorNotice from '../components/ErrorNotice';
import StopLossLabResults from '../components/StopLossLabResults';
import StopLossCandleStatistics from '../components/StopLossCandleStatistics';

const control = 'mt-1 block w-full min-w-0 rounded border border-dark-600 bg-dark-800 px-3 py-2 text-white';
const button = 'rounded border border-dark-600 px-4 py-2 disabled:opacity-50';
const day = (offset: number) => new Date(Date.now()+offset*86400000).toISOString().slice(0, 10);
const modes: [DistanceMode, string, string][] = [
  ['fixed_pct', '고정 %', 'Fixed %'], ['atr', '평균 변동폭 배수', 'Average range multiple'], ['mtr', '변동폭 중위값 배수', 'Median range multiple'],
  ['wick_mean', '꼬리 평균 배수', 'Mean wick multiple'], ['wick_median', '꼬리 중위값 배수', 'Median wick multiple'],
  ['wick_percentile', '꼬리 백분위수 배수', 'Wick percentile multiple'], ['breakout_percentile', '이탈 깊이 백분위수 배수', 'Overshoot percentile multiple'],
  ['mae_percentile', '과거 조건부 MAE 상한 백분위수 배수', 'Prior conditional MAE upper-bound percentile multiple'],
];

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="min-w-0 text-sm text-dark-200">{label}{children}</label>;
}

export default function StopLossLabPage() {
  const ko = useLanguage() === 'ko';
  const selectedCoin = useSelectedCoin();
  const [tab, setTab] = useState<'statistics' | 'lab'>('statistics');
  const [draft, setDraft] = useState<LabConfig>(() => ({
    coin: selectedCoin, start: day(-61), end: day(-1), reference_interval: '1d', execution_interval: '15m', direction: 'Short',
    reference: 'previous_extreme', lookback: 14, entry: { mode: 'fixed_pct', percentile: 95 }, stop: { mode: 'fixed_pct', percentile: 95 },
    target_mode: 'fixed_pct', entry_values: [.5], stop_values: [.5], target_values: [1.5],
    exit_rule: 'period_end', holding_hours: 24, max_entries_per_period: 1, fee_bps: 5, slippage_bps: 2,
    initial_equity: 10000, sizing: 'risk', risk_pct: 1, allocation_pct: 100, train_ratio: .7, max_drawdown_pct: 30, min_trades: 5,
  }));
  const [grids, setGrids] = useState({ entry_values: '0.5', stop_values: '0.5', target_values: '1.5' });
  const [inputError, setInputError] = useState('');
  const mutation = useMutation({ mutationFn: analyzeStopLossLab, retry: false });
  const set = <K extends keyof LabConfig>(key: K, value: LabConfig[K]) => setDraft(current => ({ ...current, [key]: value }));
  const select = (key: keyof LabConfig, options: [string, string][]) => <select className={control} value={String(draft[key])} onChange={e => set(key, e.target.value)}>{options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>;
  const numeric = (key: keyof LabConfig, min: number, max: number, step = 1) => <input className={control} type="number" min={min} max={max} step={step} required value={String(draft[key])} onChange={e => set(key, Number(e.target.value))} />;
  const isEdited = mutation.variables && (JSON.stringify(draft) !== JSON.stringify({ ...mutation.variables, entry_values: draft.entry_values, stop_values: draft.stop_values, target_values: draft.target_values }) || Object.entries(grids).some(([key, text]) => JSON.stringify(text.split(',').map(v => Number(v.trim()))) !== JSON.stringify(mutation.variables?.[key as keyof typeof grids])));

  function submit(event: FormEvent) {
    event.preventDefault();
    const parsed = Object.fromEntries(Object.entries(grids).map(([key, text]) => [key, text.split(',').map(v => v.trim() ? Number(v.trim()) : NaN)])) as Pick<LabConfig, keyof typeof grids>;
    if (Object.values(parsed).some(values => values.length > 10 || values.some(v => !Number.isFinite(v)) || new Set(values).size !== values.length)) {
      setInputError(ko ? '각 축에 중복 없는 숫자를 쉼표로 최대 10개 입력하세요.' : 'Use at most 10 unique comma-separated numbers on each axis.');
      return;
    }
    const combinations = parsed.entry_values.length*parsed.stop_values.length*parsed.target_values.length;
    const bars = ((Date.parse(draft.end)-Date.parse(draft.start))/86400000+1)*1440/({ '5m': 5, '15m': 15, '1h': 60, '4h': 240 }[draft.execution_interval] ?? 15);
    if (combinations > 125 || bars > 30000 || bars*combinations*draft.max_entries_per_period > 3000000) {
      setInputError(ko ? '계산 한도 초과: 30,000봉·125조합·3,000,000 봉×조합×재진입 이내로 기간이나 격자를 줄이세요.' : 'Budget exceeded: reduce dates/grid to ≤30,000 bars, ≤125 combinations and ≤3,000,000 bar×combination×entry operations.');
      return;
    }
    setInputError('');
    mutation.mutate({ ...draft, ...parsed });
  }

  return <div className="min-w-0 space-y-5">
    <header><h1 className="text-2xl font-bold">{ko ? '손절 실험실' : 'Stop-Loss Lab'}</h1><p className="mt-1 text-sm text-dark-300">{ko ? '봉 변동성·꼬리 분포로 진입·손절·익절의 관계를 연구합니다. 자동매매가 아니며 수익을 보장하지 않습니다.' : 'Research entry, stop and target trade-offs using volatility and wick distributions. Not automated trading or a return guarantee.'}</p></header>
    <nav className="flex flex-wrap gap-2" aria-label={ko ? '실험실 보기' : 'Lab views'}><button type="button" className={button} aria-pressed={tab === 'statistics'} onClick={() => setTab('statistics')}>{ko ? '봉 통계' : 'Candle statistics'}</button><button type="button" className={button} aria-pressed={tab === 'lab'} onClick={() => setTab('lab')}>{ko ? '전략 실험' : 'Strategy experiment'}</button></nav>
    {tab === 'statistics' ? <StopLossCandleStatistics ko={ko} /> : <>
      <form onSubmit={submit} className="card space-y-5 p-4">
        <div><h2 className="text-xl font-semibold">{ko ? '전략 실험 설정' : 'Strategy experiment settings'}</h2><p className="mt-1 text-sm text-dark-300">{ko ? '핵심 조건을 먼저 정하고, 필요한 경우에만 고급 설정을 펼치세요.' : 'Start with the essential conditions and open advanced settings only when needed.'}</p></div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Field label={ko ? '종목' : 'Symbol'}>{select('coin', ['BTC', 'ETH', 'SOL'].map(v => [v, v]))}</Field>
          <Field label={ko ? '방향' : 'Direction'}>{select('direction', [['Short', ko ? '숏' : 'Short'], ['Long', ko ? '롱' : 'Long'], ['Both', ko ? '양방향' : 'Both']])}</Field>
          <Field label={ko ? '시작 날짜 UTC' : 'Start date UTC'}><input className={control} type="date" required max={draft.end} value={draft.start} onChange={e => set('start', e.target.value)} /></Field>
          <Field label={ko ? '종료 날짜 UTC (포함)' : 'End date UTC (inclusive)'}><input className={control} type="date" required min={draft.start} max={day(0)} value={draft.end} onChange={e => set('end', e.target.value)} /></Field>
          <Field label={ko ? '기준 가격' : 'Reference price'}>{select('reference', [['previous_extreme', ko ? '이전 완료 봉 고점/저점' : 'Previous completed high/low'], ['previous_close', ko ? '이전 종가' : 'Previous close'], ['previous_open', ko ? '이전 시가' : 'Previous open'], ['wick_extreme', ko ? '확정 꼬리 극값 (꼬리 없으면 제외)' : 'Confirmed wick extreme (nonzero only)'], ['confirmed_swing', ko ? '확정 스윙 극값 (좌우 3봉)' : 'Confirmed swing (3 bars each side)']])}</Field>
        </div>
        <fieldset className="grid gap-4 rounded border border-dark-700 p-3 md:grid-cols-3"><legend className="px-2">{ko ? '진입·손절·익절' : 'Entry / stop / target'}</legend>
          {(['entry', 'stop'] as const).map(key => <div key={key} className="space-y-3"><Field label={key === 'entry' ? (ko ? '진입 방식' : 'Entry method') : (ko ? '손절 방식' : 'Stop method')}><select className={control} value={draft[key].mode} onChange={e => set(key, { ...draft[key], mode: e.target.value as DistanceMode })}>{modes.filter(([mode]) => key !== 'entry' || mode !== 'mae_percentile').map(([mode, kr, en]) => <option key={mode} value={mode}>{ko ? kr : en}</option>)}</select></Field>{draft[key].mode.includes('percentile') && <Field label={key === 'entry' ? (ko ? '진입 백분위수' : 'Entry percentile') : (ko ? '손절 백분위수' : 'Stop percentile')}><input className={control} type="number" min={50} max={99} step={1} required value={draft[key].percentile} onChange={e => set(key, { ...draft[key], percentile: Number(e.target.value) })} /></Field>}<Field label={key === 'entry' ? (ko ? '진입 값' : 'Entry value') : (ko ? '손절 값' : 'Stop value')}><input aria-label={key === 'entry' ? (ko ? '진입 값 (쉼표 구분)' : 'Entry values (comma separated)') : (ko ? '손절 값 (쉼표 구분)' : 'Stop values (comma separated)')} className={control} required value={grids[`${key}_values`]} onChange={e => setGrids(current => ({ ...current, [`${key}_values`]: e.target.value }))} /></Field></div>)}
          <div className="space-y-3"><Field label={ko ? '익절 방식' : 'Target method'}>{select('target_mode', [['fixed_pct', ko ? '고정 %' : 'Fixed %'], ['atr', ko ? '평균 변동폭' : 'Average range'], ['mtr', ko ? '변동폭 중위값' : 'Median range'], ['r_multiple', ko ? '계획 R 배수' : 'Planned R multiple'], ['reference', ko ? '기준 가격 복귀 (값 1개)' : 'Reference return (one value)'], ['price', ko ? '지정 가격 USDT' : 'Specified price USDT']])}</Field><Field label={ko ? '익절 값' : 'Target value'}><input aria-label={ko ? '익절 값 (쉼표 구분)' : 'Target values (comma separated)'} className={control} required value={grids.target_values} onChange={e => setGrids(current => ({ ...current, target_values: e.target.value }))} /></Field><p className="text-xs text-dark-300">{ko ? '값을 여러 개 비교하려면 쉼표로 구분하세요. 고정 %는 퍼센트포인트, 평균 변동폭·변동폭 중위값·꼬리 길이는 배수입니다.' : 'Separate values with commas to compare a grid. Fixed % uses percentage points; average-range, median-range and wick values are multiples.'}</p></div>
        </fieldset>
        <details className="rounded border border-dark-700 p-3"><summary className="cursor-pointer font-semibold">{ko ? '고급 설정' : 'Advanced settings'} <span className="font-normal text-dark-300">· {draft.reference_interval} / {draft.execution_interval} · {draft.fee_bps}+{draft.slippage_bps} bps</span></summary><div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Field label={ko ? '기준 봉' : 'Reference timeframe'}>{select('reference_interval', [['1d', ko ? '날봉' : 'Daily'], ['1w', ko ? '주봉' : 'Weekly']])}</Field>
          <Field label={ko ? '실행·체결 봉' : 'Execution timeframe'}>{select('execution_interval', [['5m', ko ? '5분봉' : '5m'], ['15m', ko ? '15분봉' : '15m'], ['1h', ko ? '1시간봉' : '1h'], ['4h', ko ? '4시간봉' : '4h']])}</Field>
          <Field label={ko ? '통계 기간 N' : 'Lookback N'}>{numeric('lookback', 1, 365)}</Field>
          <Field label={ko ? '최대 보유 규칙' : 'Maximum holding rule'}>{select('exit_rule', [['period_end', ko ? '기준 기간 종료 (일/주)' : 'Reference period end (day/week)'], ['holding_hours', ko ? '지정 시간 (주간 이월 가능)' : 'Fixed hours (may cross weeks)']])}</Field>
          <Field label={ko ? '최대 보유시간' : 'Holding hours'}>{numeric('holding_hours', 1, 720)}</Field>
          <Field label={ko ? '기간당 최대 진입 수' : 'Maximum entries per period'}>{numeric('max_entries_per_period', 1, 5)}</Field>
          <Field label={ko ? '초기 자본 USDT' : 'Initial equity USDT'}>{numeric('initial_equity', 100, 1e9, .01)}</Field>
          <Field label={ko ? '편도 수수료 bps (1 = 0.01%)' : 'One-way fee bps (1 = 0.01%)'}>{numeric('fee_bps', 0, 100, .1)}</Field>
          <Field label={ko ? '편도 슬리피지 bps' : 'One-way slippage bps'}>{numeric('slippage_bps', 0, 100, .1)}</Field>
          <Field label={ko ? '수량 계산' : 'Position sizing'}>{select('sizing', [['risk', ko ? '계좌 위험 / 손절 거리' : 'Account risk / stop distance'], ['notional', ko ? '계좌 배분 비중' : 'Notional allocation']])}</Field>
          <Field label={ko ? '거래당 계좌 위험 %' : 'Account risk per trade %'}>{numeric('risk_pct', .01, 10, .01)}</Field>
          <Field label={ko ? '명목 배분 % (최대 1배)' : 'Notional allocation % (max 1×)'}>{numeric('allocation_pct', .01, 100, .01)}</Field>
          <Field label={ko ? '학습 비중 (0.50–0.85)' : 'Training fraction (0.50–0.85)'}>{numeric('train_ratio', .5, .85, .01)}</Field>
          <Field label={ko ? '학습 최대낙폭 한도 %' : 'Training MDD limit %'}>{numeric('max_drawdown_pct', .01, 100, .01)}</Field>
          <Field label={ko ? '최소 평가·조건부 표본 수' : 'Minimum evaluation / conditional samples'}>{numeric('min_trades', 3, 100)}</Field>
        </div></details>
        <div className="rounded bg-dark-800 p-3 text-sm"><strong>{ko ? '실행 요약' : 'Run summary'}:</strong> {draft.coin} · {draft.direction} · {draft.start} – {draft.end} · {ko ? '진입/손절/익절' : 'Entry/stop/target'} {grids.entry_values} / {grids.stop_values} / {grids.target_values}</div>
        <details className="rounded border border-dark-700 p-3"><summary className="cursor-pointer text-sm font-semibold">{ko ? '실험 가정과 제한' : 'Experiment assumptions and limits'}</summary><p className="mt-3 text-xs text-amber-300">{ko ? '주문은 가격 접촉 시 시장가 가정입니다. 이전 완료 봉으로 수준을 고정하고 하위 봉으로 판정합니다. 갭·양방향 비용 포함, 동시 SL/TP는 손절 우선. 진입 전/후 순서가 불명인 거래는 제외·표시합니다. 조건부 MAE 손절은 같은 진입 조건의 이전 완료 보유기간만 사용합니다. 1배 명목 상한·동시 1포지션; 레버리지·펀딩·청산·유동성은 모델링하지 않습니다.' : 'Market-on-touch orders, levels frozen from prior completed candles, lower-timeframe execution. Gaps and two-way costs included; same-bar SL/TP uses stop first. Unknown entry ordering is excluded and counted. Conditional MAE stops use only earlier completed horizons for the same entry condition. Max 1× notional and one position; no leverage, funding, liquidation or liquidity model.'}</p><p className="mt-2 text-xs text-dark-300">{ko ? '주간은 월요일 00:00 UTC 확정. 미완료 기간·실행 봉 누락·통계 부족은 제외하며 결과에 사유를 표시합니다. 거래 진입/청산 시각은 봉 단위 근사입니다. 외부 공개 시세가 필요하며 샘플 워크스페이스에서는 지원하지 않습니다.' : 'Weeks complete Monday 00:00 UTC. Incomplete periods, missing execution bars and unavailable statistics are excluded with reasons. Entry/exit times are candle-resolution approximations. Requires public market access; unavailable in the offline sample workspace.'}</p></details>
        {inputError && <p role="alert" className="text-rose-300">{inputError}</p>}
        <button type="submit" className="rounded bg-sky-500 px-5 py-3 font-semibold text-dark-950 disabled:opacity-50" disabled={mutation.isPending}>{mutation.isPending ? (ko ? '과거 데이터 분석 중…' : 'Analyzing historical data…') : (ko ? '실험 실행' : 'Run experiment')}</button>
      </form>
      {mutation.error && <ErrorNotice title={ko ? '실험을 실행하지 못했습니다' : 'Experiment failed'} message={getErrorMessage(mutation.error)} />}
      {isEdited && mutation.data && <p role="status" className="text-amber-300">{ko ? '설정이 변경되었습니다. 아래는 이전에 제출한 설정의 결과입니다. 다시 실행해야 반영됩니다.' : 'Settings changed. Results below belong to the previous submitted settings; run again to apply edits.'}</p>}
      {mutation.data && <StopLossLabResults key={JSON.stringify(mutation.variables)} result={mutation.data} ko={ko} />}
    </>}
  </div>;
}
