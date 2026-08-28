import { describe, expect, it } from 'vitest';

import { entryRvol20, formatRvol20 } from './tradeReportSnapshot';

describe('formatRvol20', () => {
  it('formats a canonical RVOL20 value as a neutral multiple', () => {
    expect(formatRvol20(1.82)).toBe('1.82x');
  });

  it('keeps unavailable data distinct from a zero value', () => {
    expect(formatRvol20(null)).toBe('—');
    expect(formatRvol20(undefined)).toBe('—');
    expect(formatRvol20(0)).toBe('0x');
  });

  it('resolves the stored entry snapshot instead of the close snapshot', () => {
    const entry = {
      id: 2,
      external_id: 'close',
      event_type: 'position_close',
      source: 'deepcoin_position',
      symbol: 'BTC/USDT',
      direction: 'Long',
      datetime: '2026-08-01T02:00:00Z',
      indicator_snapshot: { event_type: 'position_close', timeframes: { '4h': { status: 'complete', rvol20: 9.99 } } },
    } as never;
    const entryFill = {
      id: 1,
      external_id: 'fill',
      event_type: 'fill',
      source: 'deepcoin',
      datetime: '2026-08-01T00:00:00Z',
      direction: 'Long',
      symbol: 'BTC/USDT',
      notes: 'Deepcoin BTC/USDT fill: buy',
      indicator_snapshot: { event_type: 'fill', timeframes: { '4h': { status: 'complete', rvol20: 1.82 } } },
    } as never;
    expect(entryRvol20(entry, [entryFill, entry])).toBe(1.82);
  });
});
