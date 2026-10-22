import type { OHLCV } from '../types';
import { candleWicks } from './wickStatistics';

export type VolatilityMetric = 'atr' | 'mtr' | 'upperStd' | 'lowerStd';
export type VolatilityUnit = 'price' | 'percent';

/** Completed, chronological bars only. ATR matches core/indicator_primitives.py
 * on valid data: first TR = H-L; RMA starts at that TR, visible after N bars.
 * Invalid data resets ATR; no skipped/imputed observations or future bars.
 */
export function computeVolatilityStatistics(candles: readonly OHLCV[], period = 14, unit: VolatilityUnit = 'percent') {
  if (!Number.isSafeInteger(period) || period < 1) throw new RangeError('Period must be a positive safe integer');
  if (unit !== 'price' && unit !== 'percent') throw new RangeError('Unknown volatility unit');
  const result: Record<VolatilityMetric, Array<number | null>> = {
    atr: Array(candles.length).fill(null), mtr: Array(candles.length).fill(null),
    upperStd: Array(candles.length).fill(null), lowerStd: Array(candles.length).fill(null),
  };
  if (period > candles.length) return result;
  const rawWicks = candles.map(row => candleWicks(row, 'price'));
  const wicks = unit === 'price' ? rawWicks : candles.map(row => candleWicks(row, 'percent'));
  const trueRanges = candles.map((row, index) => {
    if (!rawWicks[index] || (index > 0 && !rawWicks[index - 1])) return null;
    return index === 0 ? row.high - row.low : Math.max(
      row.high - row.low, Math.abs(row.high - candles[index - 1].close), Math.abs(row.low - candles[index - 1].close),
    );
  });
  // Scale first to keep finite, nonnegative price observations from overflowing.
  const populationStd = (values: number[]) => {
    const maximum = Math.max(...values);
    if (maximum === 0) return 0;
    const scaled = values.map(value => value / maximum);
    const mean = scaled.reduce((sum, value) => sum + value, 0) / values.length;
    return Math.sqrt(scaled.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length) * maximum;
  };
  const displayRange = (value: number, close: number) => {
    const normalized = unit === 'price' ? value : value / close * 100;
    return Number.isFinite(normalized) ? normalized : null;
  };
  let average: number | null = null;
  let consecutive = 0;
  for (let index = 0; index < candles.length; index++) {
    const tr = trueRanges[index];
    if (tr === null) { average = null; consecutive = 0; }
    else {
      average = average === null ? tr : average * (1 - 1 / period) + tr / period;
      consecutive++;
      if (consecutive >= period) result.atr[index] = displayRange(average, candles[index].close);
    }
    if (index < period - 1) continue;
    const rangeWindow = trueRanges.slice(index - period + 1, index + 1);
    if (rangeWindow.every((value): value is number => value !== null)) {
      rangeWindow.sort((a, b) => a - b);
      const middle = Math.floor(period / 2);
      const median = period % 2 ? rangeWindow[middle] : rangeWindow[middle - 1] / 2 + rangeWindow[middle] / 2;
      result.mtr[index] = displayRange(median, candles[index].close);
    }
    const wickWindow = wicks.slice(index - period + 1, index + 1);
    if (wickWindow.some(value => value === null)) continue;
    result.upperStd[index] = populationStd(wickWindow.map(value => value![0]));
    result.lowerStd[index] = populationStd(wickWindow.map(value => value![1]));
  }
  return result;
}
