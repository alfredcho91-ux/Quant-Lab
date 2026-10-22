import { describe, expect, it } from 'vitest';
import type { OHLCV } from '../types';
import { computeWickStatistics, normalizeWickSettings } from './wickStatistics';
import { wickLineData } from './wickStatisticsPresentation';
import { getCompletedCandles } from './ohlcv';

function candle(index: number, upper: number, lower: number, direction = 'doji', close = 100): OHLCV {
  const open = direction === 'bull' ? close - 2 : direction === 'bear' ? close + 2 : close;
  return { open_time: Date.UTC(2026, 0, 1) + index * 60_000, open_dt: String(index),
    open, high: Math.max(open, close) + upper, low: Math.min(open, close) - lower, close, volume: 1 };
}
const bars = [candle(0, 0, 0, 'bull'), candle(1, 2, 1, 'bear'), candle(2, 4, 3), candle(3, 6, 5), candle(4, 100, 80)];

describe('Wick Statistics', () => {
  it.each(['bull', 'bear', 'doji'])('measures body-relative wicks on %s candles', direction => {
    expect(computeWickStatistics([candle(0, 7, 3, direction)], 1)).toEqual({ auw: [7], muw: [7], alw: [3], mlw: [3] });
  });
  it('includes zero-length wicks, including a completely flat doji', () => {
    const result = computeWickStatistics([candle(0, 0, 0), candle(1, 4, 2)], 2);
    expect(result).toEqual({ auw: [null, 2], muw: [null, 2], alw: [null, 1], mlw: [null, 1] });
  });
  it('uses a trailing odd median and resists an outlier without discarding it from the mean', () => {
    const result = computeWickStatistics(bars, 3);
    expect(result.auw.slice(0, 4)).toEqual([null, null, 2, 4]);
    expect(result.auw[4]).toBeCloseTo(110 / 3);
    expect(result.muw).toEqual([null, null, 2, 4, 6]);
    expect(result.alw[4]).toBeCloseTo(88 / 3);
    expect(result.mlw).toEqual([null, null, 1, 3, 5]);
  });
  it('averages the two central observations for even periods', () => {
    expect(computeWickStatistics(bars, 4).muw).toEqual([null, null, null, 3, 5]);
    expect(computeWickStatistics(bars, 4).mlw).toEqual([null, null, null, 2, 4]);
  });
  it('defaults to 14 and produces no partial-window estimates or fabricated zeros', () => {
    expect(computeWickStatistics(bars).auw).toEqual(bars.map(() => null));
    expect(computeWickStatistics([], 14)).toEqual({ auw: [], muw: [], alw: [], mlw: [] });
    expect(computeWickStatistics(bars, Number.MAX_SAFE_INTEGER).muw).toEqual(bars.map(() => null));
    expect(computeWickStatistics(Array.from({ length: 14 }, (_, i) => candle(i, 2, 3))).auw[13]).toBeCloseTo(2);
  });
  it('normalizes each bar by its own close before computing either statistic', () => {
    const data = [candle(0, 10, 5, 'doji', 100), candle(1, 20, 20, 'doji', 200)];
    const percent = computeWickStatistics(data, 2, 'percent');
    expect(percent).toEqual({ auw: [null, 10], muw: [null, 10], alw: [null, 7.5], mlw: [null, 7.5] });
    expect(computeWickStatistics(data, 2).auw[1]).toBeCloseTo(15);
  });
  it.each(['open', 'high', 'low', 'close'] as const)('never imputes or skips a missing/invalid %s', field => {
    for (const bad of [null, undefined, NaN, Infinity, -Infinity, '100', 0, -1]) {
      const data = [candle(0, 2, 3), { ...candle(1, 2, 3), [field]: bad } as OHLCV, candle(2, 2, 3), candle(3, 2, 3)];
      for (const unit of ['price', 'percent'] as const) {
        const result = computeWickStatistics(data, 2, unit);
        for (const values of Object.values(result)) {
          expect(values.slice(0, 3)).toEqual([null, null, null]);
          expect(values[3]).not.toBeNull();
        }
      }
    }
  });
  it.each([{ high: 99 }, { low: 101 }, { high: 90, low: 110 }])('marks inconsistent OHLC geometry as unavailable: %o', invalid => {
    expect(computeWickStatistics([{ ...candle(0, 2, 3), ...invalid }], 1)).toEqual({ auw: [null], muw: [null], alw: [null], mlw: [null] });
  });
  it.each([0, -1, 1.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1])('rejects invalid period %s', period => {
    expect(() => computeWickStatistics(bars, period)).toThrow(RangeError);
  });
  it('handles extreme finite observations without overflowing an average or even median', () => {
    const extreme = Array.from({ length: 4 }, (_, i) => ({ ...candle(i, 0, 0), high: Number.MAX_VALUE }));
    expect(computeWickStatistics(extreme, 3).auw[2]).toBe(Number.MAX_VALUE);
    expect(computeWickStatistics(extreme, 4).muw[3]).toBe(Number.MAX_VALUE);
    expect(computeWickStatistics([{ ...candle(0, 0, 0), close: Number.MIN_VALUE, open: Number.MIN_VALUE, low: Number.MIN_VALUE, high: 100 }], 1, 'percent').auw).toEqual([null]);
  });
  it('is prefix-invariant, never uses future candles and does not mutate input', () => {
    const input = bars.map(row => Object.freeze({ ...row }));
    const saved = JSON.stringify(input);
    for (const period of [1, 2, 3, 4]) {
      for (const unit of ['price', 'percent'] as const) {
        const complete = computeWickStatistics(input, period, unit);
        for (let length = 1; length <= input.length; length++) {
          const prefix = computeWickStatistics(input.slice(0, length), period, unit);
          for (const key of ['auw', 'muw', 'alw', 'mlw'] as const) expect(prefix[key]).toEqual(complete[key].slice(0, length));
        }
      }
    }
    expect(JSON.stringify(input)).toBe(saved);
  });
  it('respects the chart policy: discard the forming last candle before calculation', () => {
    const feed = [...bars, candle(5, 1_000_000, 90)];
    expect(computeWickStatistics(getCompletedCandles(feed, 200), 3)).toEqual(computeWickStatistics(bars, 3));
  });
  it('uses the candle timestamps, keeps whitespace and hides the line crossing an invalid window', () => {
    const rendered = wickLineData(bars, [null, 0, null, 2, 3]);
    expect(rendered.map(row => row.time)).toEqual(bars.map(row => row.open_time / 1000));
    expect(rendered[0]).toEqual({ time: bars[0].open_time / 1000 });
    expect(rendered[1]).toEqual({ time: bars[1].open_time / 1000, value: 0, color: 'transparent' });
    expect(rendered[3]).toEqual({ time: bars[3].open_time / 1000, value: 2 });
  });
  it('normalizes old, partial and corrupt persisted settings', () => {
    expect(normalizeWickSettings(undefined).period).toBe(14);
    expect(normalizeWickSettings({ period: 0, unit: 'usd', visible: { auw: false, muw: 'true' } })).toEqual({
      period: 14, unit: 'price', visible: { auw: false, muw: true, alw: true, mlw: true },
    });
  });
});
