import type { LineData, UTCTimestamp, WhitespaceData } from 'lightweight-charts';
import type { OHLCV } from '../types';
import type { WickStatistic } from '../types/indicators';

export const WICK_SERIES: Array<{ key: WickStatistic; label: string; ko: string; en: string; color: string }> = [
  { key: 'auw', label: 'AUW', ko: '평균 윗꼬리', en: 'Average Upper Wick', color: '#38bdf8' },
  { key: 'muw', label: 'MUW', ko: '중앙값 윗꼬리', en: 'Median Upper Wick', color: '#a78bfa' },
  { key: 'alw', label: 'ALW', ko: '평균 아랫꼬리', en: 'Average Lower Wick', color: '#34d399' },
  { key: 'mlw', label: 'MLW', ko: '중앙값 아랫꼬리', en: 'Median Lower Wick', color: '#fbbf24' },
];

export function wickBinLabel(index: number): string {
  const edge = (value: number) => `${Math.floor(value / 10)}.${value % 10}`;
  return `${edge(index)}–${edge(index + 1)}%`;
}

export function wickLineData(candles: readonly OHLCV[], values: Array<number | null>): Array<LineData<UTCTimestamp> | WhitespaceData<UTCTimestamp>> {
  return candles.map((candle, index) => {
    const time = Math.floor(candle.open_time / 1000) as UTCTimestamp;
    const value = values[index];
    if (value == null) return { time };
    // Native whitespace omits points but connects the surrounding line. Hide
    // the outgoing segment at a gap, without inventing a zero or extra series.
    return { time, value, ...(index + 1 < values.length && values[index + 1] == null ? { color: 'transparent' } : {}) };
  });
}
