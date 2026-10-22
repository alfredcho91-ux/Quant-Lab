import type { OHLCV } from '../types';
import type { WickStatistic, WickStatisticsSettings } from '../types/indicators';

type WickCandle = Pick<OHLCV, 'open' | 'high' | 'low' | 'close'>;

export interface WickDistributionBin {
  index: number;
  upperCount: number;
  lowerCount: number;
  upperPercent: number;
  lowerPercent: number;
}

export interface WickDistribution {
  total: number;
  valid: number;
  excluded: number;
  bins: WickDistributionBin[];
}

export const DEFAULT_WICK_SETTINGS: WickStatisticsSettings = {
  period: 14,
  unit: 'price',
  visible: { auw: true, muw: true, alw: true, mlw: true },
};

export function isWickPeriod(value: number): boolean {
  return Number.isSafeInteger(value) && value > 0;
}

export function normalizeWickSettings(value: unknown): WickStatisticsSettings {
  const input = (value && typeof value === 'object' ? value : {}) as Partial<WickStatisticsSettings>;
  return {
    period: typeof input.period === 'number' && isWickPeriod(input.period) ? input.period : 14,
    unit: input.unit === 'percent' ? 'percent' : 'price',
    visible: Object.fromEntries(Object.keys(DEFAULT_WICK_SETTINGS.visible).map(key => [
      key, typeof input.visible?.[key as WickStatistic] === 'boolean' ? input.visible[key as WickStatistic] : true,
    ])) as Record<WickStatistic, boolean>,
  };
}

export function candleWicks(row: WickCandle, unit: WickStatisticsSettings['unit']): [number, number] | null {
  if (!row || ![row.open, row.high, row.low, row.close].every(value => typeof value === 'number' && Number.isFinite(value) && value > 0)
    || row.high < Math.max(row.open, row.close) || row.low > Math.min(row.open, row.close)) return null;
  const upper = row.high - Math.max(row.open, row.close);
  const lower = Math.min(row.open, row.close) - row.low;
  const values: [number, number] = unit === 'percent' ? [upper / row.close * 100, lower / row.close * 100] : [upper, lower];
  return values.every(Number.isFinite) ? values : null;
}

// Bin width is 0.1 percentage points, not rounding to the nearest tenth.
function wickBinIndex(percent: number, firstPrice: number, secondPrice: number, close: number): number | null {
  const scaled = percent * 10;
  if (!Number.isFinite(scaled)) return null;
  const nearest = Math.round(scaled);
  // OHLC subtraction can place an exact decimal boundary a few ulps below it.
  // Correct only the arithmetic error scale, not a user-visible rounding band.
  const tolerance = 4 * Number.EPSILON * Math.max(1, Math.abs(scaled), Math.abs(firstPrice / close * 1000), Math.abs(secondPrice / close * 1000));
  const index = Math.abs(scaled - nearest) <= tolerance ? nearest : Math.floor(scaled);
  return Number.isSafeInteger(index) && index >= 0 && index < Number.MAX_SAFE_INTEGER ? index : null;
}

/** Empirical per-candle distribution of all supplied completed bars, not the
 * rolling means/medians. Empty bins are omitted; extreme values stay sparse.
 */
export function computeWickDistribution(candles: readonly WickCandle[]): WickDistribution {
  const counts = new Map<number, { upperCount: number; lowerCount: number }>();
  let valid = 0;
  for (const row of candles) {
    const values = candleWicks(row, 'percent');
    if (!values) continue;
    const upper = wickBinIndex(values[0], row.high, Math.max(row.open, row.close), row.close);
    const lower = wickBinIndex(values[1], Math.min(row.open, row.close), row.low, row.close);
    if (upper === null || lower === null) continue;
    valid++;
    for (const [index, key] of [[upper, 'upperCount'], [lower, 'lowerCount']] as const) {
      const bin = counts.get(index) ?? { upperCount: 0, lowerCount: 0 };
      bin[key]++;
      counts.set(index, bin);
    }
  }
  return {
    total: candles.length, valid, excluded: candles.length - valid,
    bins: [...counts].sort(([a], [b]) => a - b).map(([index, count]) => ({
      index, ...count, upperPercent: count.upperCount / valid * 100, lowerPercent: count.lowerCount / valid * 100,
    })),
  };
}

/** One result per input candle. Callers supply completed, chronological OHLC.
 * Invalid rows stay in the window as null; they are never skipped or filled.
 */
export function computeWickStatistics(
  candles: readonly WickCandle[],
  period = 14,
  unit: WickStatisticsSettings['unit'] = 'price',
): Record<WickStatistic, Array<number | null>> {
  if (!isWickPeriod(period)) throw new RangeError('Wick period must be a positive safe integer');
  if (unit !== 'price' && unit !== 'percent') throw new RangeError('Unknown wick unit');
  const result: Record<WickStatistic, Array<number | null>> = {
    auw: Array(candles.length).fill(null), muw: Array(candles.length).fill(null),
    alw: Array(candles.length).fill(null), mlw: Array(candles.length).fill(null),
  };
  if (period > candles.length) return result;

  const wicks = candles.map(row => candleWicks(row, unit));
  for (let end = period - 1; end < wicks.length; end++) {
    const window = wicks.slice(end - period + 1, end + 1);
    if (window.some(value => value === null)) continue;
    const upper = window.map(value => value![0]).sort((a, b) => a - b);
    const lower = window.map(value => value![1]).sort((a, b) => a - b);
    // Sorted, nonnegative values: normalize before summing to avoid overflow.
    // Calculations retain full precision; only chart labels are rounded.
    const mean = (values: number[]) => {
      const maximum = values[values.length - 1];
      return maximum === 0 ? 0 : (values.reduce((sum, value) => sum + value / maximum, 0) / period) * maximum;
    };
    const median = (values: number[]) => period % 2 === 1 ? values[Math.floor(period / 2)]
      : values[period / 2 - 1] / 2 + values[period / 2] / 2;
    result.auw[end] = mean(upper);
    result.muw[end] = median(upper);
    result.alw[end] = mean(lower);
    result.mlw[end] = median(lower);
  }
  return result;
}
