import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { isWickPeriod } from '../utils/wickStatistics';
import { WICK_SERIES } from '../utils/wickStatisticsPresentation';

export function WickStatisticsSettings({ isKo }: { isKo: boolean }) {
  const settings = useStore(state => state.wickStatistics);
  const update = useStore(state => state.updateWickStatistics);
  const [input, setInput] = useState(String(settings.period));
  useEffect(() => setInput(String(settings.period)), [settings.period]);
  const valid = input.trim() !== '' && isWickPeriod(Number(input));
  return (
    <fieldset className="rounded-lg border border-dark-700 px-3 py-2 text-xs text-dark-300">
      <legend className="px-1 font-semibold">{isKo ? '꼬리 통계 · Wick Statistics' : 'Wick Statistics'}</legend>
      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2">
          {isKo ? '기간' : 'Period'}
          <input type="number" min="1" step="1" value={input} aria-invalid={!valid} aria-describedby="wick-policy"
            className="w-24 rounded border border-dark-600 bg-dark-800 px-2 py-1"
            onChange={event => {
              const value = event.target.value;
              setInput(value);
              if (value.trim() !== '' && isWickPeriod(Number(value))) update({ period: Number(value) });
            }} />
        </label>
        <label className="flex items-center gap-2">
          {isKo ? '단위' : 'Unit'}
          <select value={settings.unit} className="rounded border border-dark-600 bg-dark-800 px-2 py-1"
            onChange={event => update({ unit: event.target.value === 'percent' ? 'percent' : 'price' })}>
            <option value="price">{isKo ? '가격 절대값' : 'Absolute price'}</option>
            <option value="percent">{isKo ? '각 봉 종가 대비 %' : '% of each close'}</option>
          </select>
        </label>
        {WICK_SERIES.map(series => (
          <label key={series.key} className="flex items-center gap-1.5" title={isKo ? series.ko : series.en}>
            <input type="checkbox" checked={settings.visible[series.key]}
              onChange={event => update({ visible: { ...settings.visible, [series.key]: event.target.checked } })} />
            <span style={{ color: series.color }}>{series.label}</span>
            <span>{isKo ? series.ko : series.en}</span>
          </label>
        ))}
      </div>
      {!valid && <p role="alert" className="mt-2 text-red-300">{isKo ? '양의 정수를 입력하세요. 마지막 유효 기간을 유지합니다.' : 'Enter a positive integer. The last valid period remains active.'}</p>}
      <p id="wick-policy" className="mt-2 text-dark-400">{isKo
        ? '완료된 봉만 사용 · 최대 최근 200봉 · 표본 부족 또는 비정상 OHLC가 포함된 윈도우는 — · 0 길이 꼬리는 포함'
        : 'Completed candles only · up to 200 recent bars · incomplete/invalid OHLC windows: — · zero-length wicks included'}</p>
    </fieldset>
  );
}
