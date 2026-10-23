import { describe, expect, it } from 'vitest';
import type { OHLCV } from '../types';
import { computeVolatilityStatistics } from './volatilityStatistics';
import { getCompletedCandles } from './ohlcv';
import { computeWickStatistics } from './wickStatistics';

function bar(open: number, high: number, low: number, close: number, index = 0): OHLCV {
  return { open, high, low, close, open_time: index * 60_000, open_dt: String(index), volume: 1 };
}
const data = [bar(100, 102, 99, 100), bar(102, 105, 100, 103, 1), bar(101, 102, 98, 101, 2), bar(106, 110, 104, 106, 3), bar(103, 104, 100, 103, 4)];

describe('Volatility and wick statistics', () => {
  it('uses trailing arithmetic TR means, not Wilder ATR, and includes gaps', () => {
    const expected = [null, null, 13 / 3, 19 / 3, 20 / 3];
    const result = computeVolatilityStatistics(data, 3, 'price');
    expected.forEach((value, index) => value === null ? expect(result.rangeMean[index]).toBeNull() : expect(result.rangeMean[index]).toBeCloseTo(value, 12));
    expect(result.rangeMedian).toEqual([null, null, 5, 5, 6]);
    expect(result.rangeMean[2]).not.toBeCloseTo(4.111111111111111); // previous Wilder value
    // The fourth TR is 9, not the candle's 6-point high-low range.
    expect(computeVolatilityStatistics(data, 1, 'price').rangeMean).toEqual([3, 5, 5, 9, 6]);
  });

  it('uses the central pair for even median windows', () => {
    const result = computeVolatilityStatistics(data, 2, 'price');
    expect(result.rangeMedian).toEqual([null, 4, 5, 7, 7.5]);
    expect(result.rangeMean[3]).toBe(7);
    expect(result.muw[4]).toBe(2.5); // upper wicks [4,1]
    expect(result.mlw[4]).toBe(2.5); // lower wicks [2,3]
  });

  it('returns all four wick means/medians rather than their standard deviations', () => {
    const result = computeVolatilityStatistics(data, 3, 'price');
    expect(result.auw[4]).toBeCloseTo(2); // wicks [1,4,1]
    expect(result.muw[4]).toBe(1);
    expect(result.alw[4]).toBeCloseTo(8 / 3); // wicks [3,2,3]
    expect(result.mlw[4]).toBe(3);
    const one = computeVolatilityStatistics(data, 1, 'price');
    expect(one.auw).toEqual([2, 2, 1, 4, 1]);
    expect(one.muw).toEqual(one.auw);
    expect(one.alw).toEqual([1, 2, 3, 2, 3]);
    expect(one.mlw).toEqual(one.alw);
  });

  it('reuses the existing Wick Statistics contracts in both units', () => {
    for (const unit of ['price', 'percent'] as const) {
      const { auw, muw, alw, mlw } = computeVolatilityStatistics(data, 3, unit);
      expect({ auw, muw, alw, mlw }).toEqual(computeWickStatistics(data, 3, unit));
    }
  });

  it('retains outliers in means while medians describe the typical candle and wick', () => {
    const rows = [bar(100, 101, 99, 100), bar(100, 101, 99, 100, 1), bar(100, 200, 99, 100, 2)];
    const result = computeVolatilityStatistics(rows, 3, 'price');
    expect(result.rangeMean[2]).toBeCloseTo(35);
    expect(result.rangeMedian[2]).toBe(2);
    expect(result.auw[2]).toBeCloseTo(34);
    expect(result.muw[2]).toBe(1);
  });

  it('includes zero wicks for bullish, bearish and doji candles', () => {
    const result = computeVolatilityStatistics([bar(99, 100, 99, 100), bar(101, 101, 100, 100), bar(100, 100, 100, 100)], 3, 'price');
    for (const key of ['auw', 'muw', 'alw', 'mlw'] as const) expect(result[key][2]).toBe(0);
    expect(result.rangeMean[2]).toBeCloseTo(2 / 3);
    expect(result.rangeMedian[2]).toBe(1);
  });

  it('normalizes every TR and wick by its own close before either statistic', () => {
    const rows = [bar(100, 110, 95, 100), bar(200, 220, 180, 200, 1)];
    const result = computeVolatilityStatistics(rows, 2, 'percent');
    // TR = 15,120 => 15%,60%; not mean(TR)/last close = 33.75%.
    expect(result.rangeMean[1]).toBeCloseTo(37.5);
    expect(result.rangeMedian[1]).toBeCloseTo(37.5);
    expect(result.auw[1]).toBeCloseTo(10);
    expect(result.muw[1]).toBeCloseTo(10);
    expect(result.alw[1]).toBeCloseTo(7.5);
    expect(result.mlw[1]).toBeCloseTo(7.5);
    expect(computeVolatilityStatistics(rows, 2, 'price').rangeMean[1]).toBeCloseTo(67.5);
  });

  it('keeps incomplete windows null, including arbitrary N larger than loaded history', () => {
    for (const values of Object.values(computeVolatilityStatistics(data, 14))) expect(values).toEqual(Array(5).fill(null));
    for (const values of Object.values(computeVolatilityStatistics(data, Number.MAX_SAFE_INTEGER))) expect(values).toEqual(Array(5).fill(null));
    expect(computeVolatilityStatistics([])).toEqual({ rangeMean: [], rangeMedian: [], auw: [], muw: [], alw: [], mlw: [] });
  });

  it.each(['open', 'high', 'low', 'close'] as const)('does not skip or impute invalid %s or bridge a missing previous close', field => {
    for (const invalid of [null, undefined, NaN, Infinity, -Infinity, 0, -1, '100']) {
      const rows = Array.from({ length: 7 }, (_, index) => bar(100, 102, 99, 100, index));
      rows[2] = { ...rows[2], [field]: invalid } as OHLCV;
      const result = computeVolatilityStatistics(rows, 2, 'price');
      expect(result.rangeMean).toEqual([null, 3, null, null, null, 3, 3]);
      expect(result.rangeMedian).toEqual([null, 3, null, null, null, 3, 3]);
      for (const key of ['auw', 'muw'] as const) expect(result[key]).toEqual([null, 2, null, null, 2, 2, 2]);
      for (const key of ['alw', 'mlw'] as const) expect(result[key]).toEqual([null, 1, null, null, 1, 1, 1]);
    }
  });

  it.each([{ high: 99 }, { low: 101 }])('rejects inconsistent OHLC geometry: %o', invalid => {
    for (const values of Object.values(computeVolatilityStatistics([{ ...data[0], ...invalid }], 1))) expect(values).toEqual([null]);
  });

  it.each([0, -1, 1.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1])('rejects invalid period %s', period => {
    expect(() => computeVolatilityStatistics(data, period)).toThrow(RangeError);
  });

  it('rejects an unsupported unit and never emits infinity for overflowed normalization', () => {
    expect(() => computeVolatilityStatistics(data, 1, 'unknown' as 'price')).toThrow(RangeError);
    const row = bar(Number.MIN_VALUE, 100, Number.MIN_VALUE, Number.MIN_VALUE);
    for (const values of Object.values(computeVolatilityStatistics([row], 1, 'percent'))) expect(values).toEqual([null]);
    const extremes = [bar(1, 1e308, 1, 1), bar(1, 5e307, 1, 1)];
    const result = computeVolatilityStatistics(extremes, 2, 'price');
    for (const key of ['rangeMean', 'rangeMedian', 'auw', 'muw'] as const) expect(result[key][1]).toBeCloseTo(7.5e307, -294);
  });

  it('is prefix invariant, never reads forming/future bars and does not mutate OHLC', () => {
    const frozen = Object.freeze(data.map(row => Object.freeze({ ...row })));
    for (const period of [1, 2, 3]) for (const unit of ['price', 'percent'] as const) {
      const complete = computeVolatilityStatistics(frozen, period, unit);
      for (let length = 1; length <= data.length; length++) {
        const prefix = computeVolatilityStatistics(frozen.slice(0, length), period, unit);
        for (const key of ['rangeMean', 'rangeMedian', 'auw', 'muw', 'alw', 'mlw'] as const) expect(prefix[key]).toEqual(complete[key].slice(0, length));
      }
      const withForming = [...data, bar(100, 1e9, 1, 100, 5)];
      expect(computeVolatilityStatistics(getCompletedCandles(withForming, 5), period, unit)).toEqual(complete);
    }
  });
});
