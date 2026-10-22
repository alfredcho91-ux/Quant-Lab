import { describe, expect, it } from 'vitest';
import type { OHLCV } from '../types';
import { computeVolatilityStatistics } from './volatilityStatistics';
import { getCompletedCandles } from './ohlcv';

function bar(open: number, high: number, low: number, close: number, index = 0): OHLCV {
  return { open, high, low, close, open_time: index * 60_000, open_dt: String(index), volume: 1 };
}
const data = [bar(100, 102, 99, 100), bar(102, 105, 100, 103, 1), bar(101, 102, 98, 101, 2), bar(106, 110, 104, 106, 3), bar(103, 104, 100, 103, 4)];

describe('Volatility and wick statistics', () => {
  it('matches the existing core Wilder ATR reference including gaps and first-TR initialization', () => {
    // Generated from core.indicator_primitives.compute_atr_wilder on this OHLC.
    const expected = [null, null, 4.111111111111111, 5.7407407407407405, 5.82716049382716];
    const result = computeVolatilityStatistics(data, 3, 'price');
    expected.forEach((value, index) => value === null ? expect(result.atr[index]).toBeNull() : expect(result.atr[index]).toBeCloseTo(value, 12));
    expect(result.mtr).toEqual([null, null, 5, 5, 6]);
    // The fourth TR is 9, not the candle's 6-point high-low range.
    expect(computeVolatilityStatistics(data, 1, 'price').atr).toEqual([3, 5, 5, 9, 6]);
  });

  it('uses the central pair for even MTR windows and retains outliers in ATR', () => {
    const result = computeVolatilityStatistics(data, 2, 'price');
    expect(result.mtr).toEqual([null, 4, 5, 7, 7.5]);
    expect(result.atr[3]).toBe(6.75); // RMA includes the 9-point gap TR.
  });

  it('computes trailing population standard deviation, not sample deviation', () => {
    const result = computeVolatilityStatistics(data, 3, 'price');
    expect(result.upperStd[4]).toBeCloseTo(Math.sqrt(2)); // wicks [1, 4, 1]
    expect(result.lowerStd[4]).toBeCloseTo(Math.sqrt(2 / 9));
    const one = computeVolatilityStatistics(data, 1, 'price');
    expect(one.upperStd).toEqual([0, 0, 0, 0, 0]);
    expect(one.lowerStd).toEqual([0, 0, 0, 0, 0]);
  });

  it('includes zero wicks for bullish, bearish and doji candles', () => {
    const result = computeVolatilityStatistics([bar(99, 100, 99, 100), bar(101, 101, 100, 100), bar(100, 100, 100, 100)], 3, 'price');
    expect(result.upperStd[2]).toBe(0);
    expect(result.lowerStd[2]).toBe(0);
    expect(result.mtr[2]).toBe(1);
  });

  it('normalizes ATR/MTR after aggregation but each wick before its standard deviation', () => {
    const rows = [bar(100, 110, 95, 100), bar(200, 220, 180, 200, 1)];
    const result = computeVolatilityStatistics(rows, 2, 'percent');
    // TR = 15,120; RMA = 67.5; median = 67.5; current close = 200.
    expect(result.atr[1]).toBeCloseTo(33.75);
    expect(result.mtr[1]).toBeCloseTo(33.75);
    expect(result.upperStd[1]).toBe(0); // 10%, 10%, despite different prices
    expect(result.lowerStd[1]).toBeCloseTo(2.5); // 5%, 10%
  });

  it('keeps incomplete windows null, including arbitrary N larger than loaded history', () => {
    for (const values of Object.values(computeVolatilityStatistics(data, 14))) expect(values).toEqual(Array(5).fill(null));
    for (const values of Object.values(computeVolatilityStatistics(data, Number.MAX_SAFE_INTEGER))) expect(values).toEqual(Array(5).fill(null));
    expect(computeVolatilityStatistics([])).toEqual({ atr: [], mtr: [], upperStd: [], lowerStd: [] });
  });

  it.each(['open', 'high', 'low', 'close'] as const)('does not skip or impute invalid %s; restarts ATR without bridging a missing previous close', field => {
    for (const invalid of [null, undefined, NaN, Infinity, -Infinity, 0, -1, '100']) {
      const rows = Array.from({ length: 7 }, (_, index) => bar(100, 102, 99, 100, index));
      rows[2] = { ...rows[2], [field]: invalid } as OHLCV;
      const result = computeVolatilityStatistics(rows, 2, 'price');
      expect(result.atr).toEqual([null, 3, null, null, null, 3, 3]);
      expect(result.mtr).toEqual([null, 3, null, null, null, 3, 3]);
      expect(result.upperStd).toEqual([null, 0, null, null, 0, 0, 0]);
      expect(result.lowerStd).toEqual([null, 0, null, null, 0, 0, 0]);
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
    expect(computeVolatilityStatistics([row], 1, 'percent')).toEqual({ atr: [null], mtr: [null], upperStd: [null], lowerStd: [null] });
    const extremes = [bar(1, 1e308, 1, 1), bar(1, 5e307, 1, 1)];
    expect(computeVolatilityStatistics(extremes, 2, 'price').upperStd[1]).toBeCloseTo(2.5e307, -294);
  });

  it('is prefix invariant, never reads forming/future bars and does not mutate OHLC', () => {
    const frozen = Object.freeze(data.map(row => Object.freeze({ ...row })));
    for (const period of [1, 2, 3]) for (const unit of ['price', 'percent'] as const) {
      const complete = computeVolatilityStatistics(frozen, period, unit);
      for (let length = 1; length <= data.length; length++) {
        const prefix = computeVolatilityStatistics(frozen.slice(0, length), period, unit);
        for (const key of ['atr', 'mtr', 'upperStd', 'lowerStd'] as const) expect(prefix[key]).toEqual(complete[key].slice(0, length));
      }
      const withForming = [...data, bar(100, 1e9, 1, 100, 5)];
      expect(computeVolatilityStatistics(getCompletedCandles(withForming, 5), period, unit)).toEqual(complete);
    }
  });
});
