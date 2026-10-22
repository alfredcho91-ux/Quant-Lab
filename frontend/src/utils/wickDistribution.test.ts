import { describe, expect, it } from 'vitest';
import { computeWickDistribution } from './wickStatistics';
import { wickBinLabel } from './wickStatisticsPresentation';

const candle = (upper: number, lower = upper, close = 100) => ({
  open: close, high: close + upper, low: close - lower, close,
});

describe('Per-candle wick distribution in 0.1 percentage-point bins', () => {
  it('uses lower-inclusive, upper-exclusive bins without rounding observations', () => {
    const values = [0, 0.099, 0.1, 0.199, 0.2, 0.3, 0.999, 1];
    const result = computeWickDistribution(values.map(value => candle(value)));
    expect(result.valid).toBe(8);
    expect(result.excluded).toBe(0);
    expect(result.bins.map(bin => [bin.index, bin.upperCount, bin.lowerCount])).toEqual([
      [0, 2, 2], [1, 2, 2], [2, 1, 1], [3, 1, 1], [9, 1, 1], [10, 1, 1],
    ]);
    expect(result.bins[0].upperPercent).toBe(25);
    expect(result.bins[0].lowerPercent).toBe(25);
  });

  it('corrects decimal subtraction at exact bin edges but not genuinely smaller values', () => {
    const result = computeWickDistribution([candle(0.1), candle(0.3), candle(0.099999)]);
    expect(result.bins.map(bin => [bin.index, bin.upperCount, bin.lowerCount])).toEqual([
      [0, 1, 1], [1, 1, 1], [3, 1, 1],
    ]);
  });

  it('normalizes each candle by its own close and counts raw wicks, not rolling statistics', () => {
    const result = computeWickDistribution([candle(0.1, 0, 100), candle(0.2, 0, 200)]);
    expect(result).toEqual({ total: 2, valid: 2, excluded: 0, bins: [
      { index: 0, upperCount: 0, lowerCount: 2, upperPercent: 0, lowerPercent: 100 },
      { index: 1, upperCount: 2, lowerCount: 0, upperPercent: 100, lowerPercent: 0 },
    ] });
  });

  it.each(['open', 'high', 'low', 'close'] as const)('excludes invalid %s from both denominators instead of treating it as zero', field => {
    for (const invalid of [null, undefined, NaN, Infinity, -Infinity, '100', 0, -1]) {
      const data = [candle(0), { ...candle(0), [field]: invalid } as ReturnType<typeof candle>];
      expect(computeWickDistribution(data)).toEqual({ total: 2, valid: 1, excluded: 1, bins: [
        { index: 0, upperCount: 1, lowerCount: 1, upperPercent: 100, lowerPercent: 100 },
      ] });
    }
  });

  it('excludes inconsistent geometry and unrepresentable normalization/bin indices', () => {
    const data = [
      { ...candle(0), high: 99 }, { ...candle(0), low: 101 },
      { open: Number.MIN_VALUE, close: Number.MIN_VALUE, low: Number.MIN_VALUE, high: 100 },
      candle(1e20, 0),
    ];
    expect(computeWickDistribution(data)).toEqual({ total: 4, valid: 0, excluded: 4, bins: [] });
    expect(computeWickDistribution([])).toEqual({ total: 0, valid: 0, excluded: 0, bins: [] });
  });

  it('keeps extreme outliers in sparse bins without clipping or allocating all intervening bins', () => {
    const result = computeWickDistribution([candle(0), candle(10_000, 0)]);
    expect(result.bins.map(bin => bin.index)).toEqual([0, 100_000]);
    expect(result.bins[1].upperCount).toBe(1);
    expect(result.bins[1].upperPercent).toBe(50);
    expect(result.bins[0].lowerPercent).toBe(100);
  });

  it('counts every valid candle once per side, includes zero wicks, and does not mutate input', () => {
    const data = Object.freeze([Object.freeze(candle(0, 0)), Object.freeze(candle(0.2, 0.4)), Object.freeze(candle(0.9, 0.1))]);
    const before = JSON.stringify(data);
    const result = computeWickDistribution(data);
    expect(result.bins.reduce((sum, bin) => sum + bin.upperCount, 0)).toBe(result.valid);
    expect(result.bins.reduce((sum, bin) => sum + bin.lowerCount, 0)).toBe(result.valid);
    expect(result.bins.reduce((sum, bin) => sum + bin.upperPercent, 0)).toBeCloseTo(100);
    expect(result.bins.reduce((sum, bin) => sum + bin.lowerPercent, 0)).toBeCloseTo(100);
    expect(JSON.stringify(data)).toBe(before);
  });

  it('formats decimal boundaries without floating-point label artifacts', () => {
    expect([0, 1, 9, 10, 100_000].map(wickBinLabel)).toEqual([
      '0.0–0.1%', '0.1–0.2%', '0.9–1.0%', '1.0–1.1%', '10000.0–10000.1%',
    ]);
  });
});
