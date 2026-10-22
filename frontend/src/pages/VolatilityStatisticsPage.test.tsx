// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getOHLCV } from '../api/market';
import EChart from '../components/EChart';
import { useStore } from '../store/useStore';
import App from '../App';
import VolatilityStatisticsPage from './VolatilityStatisticsPage';
import type { OHLCV } from '../types';

vi.mock('../api/market', () => ({
  getOHLCV: vi.fn(), getMarketPrices: vi.fn(async () => ({})), getFearGreedIndex: vi.fn(async () => null),
}));
vi.mock('../components/EChart', () => ({ default: vi.fn(() => <div role="img" aria-label="Statistics plot" />) }));
const clients: QueryClient[] = [];
const feed: OHLCV[] = Array.from({ length: 21 }, (_, index) => ({
  open_time: Date.UTC(2026, 0, 1) + index * 60_000, open_dt: `fixture-${index}`,
  open: 100, high: index === 20 ? 1e6 : 102, low: 99, close: 100, volume: 1,
}));
function setup(element = <VolatilityStatisticsPage />) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  return render(<QueryClientProvider client={client}>{element}</QueryClientProvider>);
}
function apply(period: string, count = '500', unit = 'price') {
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Calculation period N' }), { target: { value: period } });
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Completed candles to load' }), { target: { value: count } });
  fireEvent.change(screen.getByRole('combobox', { name: 'Unit' }), { target: { value: unit } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply settings' }));
}
beforeEach(() => {
  vi.clearAllMocks(); sessionStorage.clear();
  useStore.setState({ ...useStore.getInitialState(), language: 'en', selectedCoin: 'BTC', selectedInterval: '4h' });
  vi.mocked(getOHLCV).mockImplementation(async (_coin, _interval, _csv, limit) => ({ data: feed.slice(-(limit ?? 21)), source: 'Synthetic fixture', count: Math.min(limit ?? 21, 21) }));
});
afterEach(() => { cleanup(); clients.splice(0).forEach(client => client.clear()); });

describe('Volatility statistics page', () => {
  it('renders the direct route and bilingual sidebar navigation', async () => {
    window.history.replaceState(null, '', '/volatility-statistics');
    setup(<App />);
    expect(await screen.findByRole('heading', { name: 'Volatility & Wick Statistics' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Volatility & Wick Statistics' })).toBeTruthy();
    await act(async () => { useStore.getState().setLanguage('ko'); });
    expect(screen.getByRole('heading', { name: '변동성·꼬리 통계' })).toBeTruthy();
    expect(screen.getByRole('button', { name: '변동성·꼬리 통계' })).toBeTruthy();
  });

  it('uses one OHLC request, excludes the forming candle, and displays real sample count', async () => {
    setup();
    await screen.findByRole('img', { name: 'Statistics plot' });
    expect(getOHLCV).toHaveBeenCalledWith('BTC', '4h', false, 501);
    expect(getOHLCV).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/500 requested · 20 completed/)).toBeTruthy();
    expect(within(screen.getByRole('region', { name: 'ATR · Average True Range' })).getByText('3.00%')).toBeTruthy();
    expect(within(screen.getByRole('region', { name: 'Upper wick standard deviation' })).getByText('0.00%p')).toBeTruthy();
  });

  it('allows custom N/count, applies explicitly, and recalculates units without another request', async () => {
    setup(); await screen.findByRole('img');
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Completed candles to load' }), { target: { value: '7' } });
    expect(getOHLCV).toHaveBeenCalledTimes(1);
    apply('3', '7');
    await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('BTC', '4h', false, 8));
    await screen.findByText(/N=3 · 7 requested · 7 completed/);
    expect(within(screen.getByRole('region', { name: 'ATR · Average True Range' })).getByText('3.00')).toBeTruthy();
    const requests = vi.mocked(getOHLCV).mock.calls.length;
    apply('1', '7', 'percent');
    expect(within(screen.getByRole('region', { name: 'MTR · Median True Range' })).getByText('3.00%')).toBeTruthy();
    expect(getOHLCV).toHaveBeenCalledTimes(requests);
  });

  it('enforces integer/API bounds and supports the maximum completed count without silently capping N', async () => {
    setup(); await screen.findByRole('img');
    for (const [period, count] of [['0', '500'], ['1.5', '500'], ['14', '10000'], ['14', '0'], ['', '500']]) {
      apply(period, count);
      expect((screen.getByRole('button', { name: 'Apply settings' }) as HTMLButtonElement).disabled).toBe(true);
      expect(screen.getByRole('alert')).toBeTruthy();
      expect(getOHLCV).toHaveBeenCalledTimes(1);
    }
    apply('100000', '9999');
    await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('BTC', '4h', false, 10000));
    await screen.findByText(/N=100000 · 9999 requested · 20 completed/);
    expect(screen.getByRole('status').textContent).toContain('fewer completed candles');
    expect(within(screen.getByRole('region', { name: 'ATR · Average True Range' })).getByText('—')).toBeTruthy();
  });

  it('replaces query data on coin/timeframe changes and cannot display a late previous selection', async () => {
    setup(); await screen.findByRole('img');
    let resolve!: (value: Awaited<ReturnType<typeof getOHLCV>>) => void;
    vi.mocked(getOHLCV).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
    act(() => useStore.getState().setSelectedCoin('ETH'));
    await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('ETH', '4h', false, 501));
    expect(screen.queryByRole('img')).toBeNull();
    act(() => useStore.getState().setSelectedInterval('1h'));
    await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('ETH', '1h', false, 501));
    await screen.findByRole('img');
    await act(async () => { resolve({ data: [], source: 'Old selection', count: 0 }); });
    expect(screen.queryByText(/Old selection/)).toBeNull();
    expect(screen.getByRole('img')).toBeTruthy();
  });

  it('links both panel time axes, keeps gaps null, and exposes native legend/zoom controls', async () => {
    setup(); await screen.findByRole('img');
    const calls = vi.mocked(EChart).mock.calls;
    const option = calls[calls.length - 1][0].option;
    expect(option).toMatchObject({
      axisPointer: { link: [{ xAxisIndex: 'all' }] },
      dataZoom: [{ type: 'inside', xAxisIndex: [0, 1] }, { type: 'slider', xAxisIndex: [0, 1] }],
    });
    const series = option.series as Array<{ data: unknown[]; connectNulls?: boolean }>;
    expect(series).toHaveLength(5);
    expect(series[0].data).toHaveLength(20);
    for (const line of series.slice(1)) {
      expect(line.connectNulls).toBe(false);
      expect(line.data.slice(0, 13)).toEqual(Array(13).fill(null));
    }
  });

  it('shows empty and network-error states without invented summaries', async () => {
    vi.mocked(getOHLCV).mockResolvedValueOnce({ data: [feed[0]], source: 'Fixture', count: 1 });
    const view = setup();
    await screen.findByText('No completed candles available.');
    expect(screen.queryByRole('img')).toBeNull();
    vi.mocked(getOHLCV).mockRejectedValue(new Error('Synthetic network failure'));
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(await screen.findByRole('alert', {}, { timeout: 4000 })).toBeTruthy();
    expect(view.container.textContent).toContain('Synthetic network failure');
    expect(screen.queryByRole('img')).toBeNull();
  });
});
