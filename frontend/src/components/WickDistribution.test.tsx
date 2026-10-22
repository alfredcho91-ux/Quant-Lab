// @vitest-environment jsdom
import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { OHLCV } from '../types';
import { WickDistribution } from './WickDistribution';

const candle = (upper: number, lower = 0): OHLCV => ({
  open_time: 1, open_dt: 'fixture', open: 100, high: 100 + upper, low: 100 - lower, close: 100, volume: 1,
});
afterEach(cleanup);

describe('Wick distribution display', () => {
  it('shows paired counts, shares and proportional bars for the same valid population', () => {
    render(<WickDistribution data={[candle(0), candle(0.1, 0.2), { ...candle(0), close: 0 }]} isKo />);
    expect(screen.getByText('전체 3봉 · 유효 2봉 · 제외 1봉')).toBeTruthy();
    const table = screen.getByRole('table', { name: '윗꼬리·아랫꼬리 0.1% 분포' });
    const row = within(table).getByRole('rowheader', { name: '0.0–0.1%' }).closest('tr')!;
    expect(within(row).getAllByRole('cell').map(cell => cell.textContent)).toEqual(['1개 · 50.00%', '1개 · 50.00%']);
    expect(row.querySelectorAll('[style="width: 50%;"]')).toHaveLength(2);
    expect(within(table).getAllByRole('rowheader')).toHaveLength(3);
  });

  it('replaces rather than accumulates candles and supports English labels', () => {
    const view = render(<WickDistribution data={[candle(0), candle(0.1)]} isKo />);
    view.rerender(<WickDistribution data={[candle(0.4)]} isKo={false} />);
    expect(screen.getByText('1 total · 1 valid · 0 excluded')).toBeTruthy();
    expect(screen.getByRole('table', { name: 'Upper and lower wick 0.1% distribution' })).toBeTruthy();
    expect(screen.queryByRole('rowheader', { name: '0.1–0.2%' })).toBeNull();
    expect(screen.getByRole('rowheader', { name: '0.4–0.5%' })).toBeTruthy();
    expect(screen.getAllByText('1 · 100.00%')).toHaveLength(2);
  });

  it('does not show invented percentages or a table when no valid completed candles exist', () => {
    const view = render(<WickDistribution data={[]} isKo />);
    expect(screen.getByRole('status').textContent).toBe('분포를 계산할 유효 완료 봉이 없습니다.');
    expect(screen.queryByRole('table')).toBeNull();
    view.rerender(<WickDistribution data={[{ ...candle(0), high: NaN }]} isKo={false} />);
    expect(screen.getByText('1 total · 0 valid · 1 excluded')).toBeTruthy();
    expect(screen.getByRole('status').textContent).toBe('No valid completed candles for this distribution.');
    expect(view.container.textContent).not.toMatch(/NaN|Infinity/);
  });
});
