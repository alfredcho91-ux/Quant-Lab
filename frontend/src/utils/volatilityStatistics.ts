import type { OHLCV } from '../types';
import { candleWicks, computeWickStatistics } from './wickStatistics';

export type VolatilityMetric = 'rangeMean' | 'rangeMedian' | 'auw' | 'muw' | 'alw' | 'mlw';
export type VolatilityUnit = 'price' | 'percent';

/** Trailing arithmetic means and medians of completed, chronological bars.
 * Candle volatility uses TR (including gaps), not Wilder-smoothed ATR.
 * Percent mode normalizes each observation before either statistic.
 */
export function computeVolatilityStatistics(candles: readonly OHLCV[], period = 14, unit: VolatilityUnit = 'percent') {
  if (!Number.isSafeInteger(period) || period < 1) throw new RangeError('Period must be a positive safe integer');
  if (unit !== 'price' && unit !== 'percent') throw new RangeError('Unknown volatility unit');
  const result: Record<VolatilityMetric, Array<number | null>> = {
    rangeMean: Array(candles.length).fill(null), rangeMedian: Array(candles.length).fill(null),
    ...computeWickStatistics(candles, period, unit),
  };
  if (period > candles.length) return result;
  const rawWicks = candles.map(row => candleWicks(row, 'price'));
  const trueRanges = candles.map((row, index) => {
    if (!rawWicks[index] || (index > 0 && !rawWicks[index - 1])) return null;
    const tr = index === 0 ? row.high - row.low : Math.max(
      row.high - row.low, Math.abs(row.high - candles[index - 1].close), Math.abs(row.low - candles[index - 1].close),
    );
    const value = unit === 'price' ? tr : tr / row.close * 100;
    return Number.isFinite(value) ? value : null;
  });
  for (let index = period - 1; index < candles.length; index++) {
    const rangeWindow = trueRanges.slice(index - period + 1, index + 1);
    if (rangeWindow.every((value): value is number => value !== null)) {
      rangeWindow.sort((a, b) => a - b);
      // Scale the nonnegative observations before summing to avoid overflow.
      const maximum = rangeWindow[period - 1];
      result.rangeMean[index] = maximum === 0 ? 0 : rangeWindow.reduce((sum, value) => sum + value / maximum, 0) / period * maximum;
      const middle = Math.floor(period / 2);
      result.rangeMedian[index] = period % 2 ? rangeWindow[middle] : rangeWindow[middle - 1] / 2 + rangeWindow[middle] / 2;
    }
  }
  return result;
}
