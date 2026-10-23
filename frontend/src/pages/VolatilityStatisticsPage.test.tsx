// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getOHLCV } from '../api/market';
import { useStore } from '../store/useStore';
import App from '../App';
import VolatilityStatisticsPage from './VolatilityStatisticsPage';
import type { OHLCV } from '../types';

vi.mock('../api/market', () => ({
  getOHLCV: vi.fn(), getMarketPrices: vi.fn(async () => ({})), getFearGreedIndex: vi.fn(async () => null),
}));
vi.mock('../components/EChart', () => ({ default: () => null }));
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
    expect(await screen.findByRole('heading', { name: 'Stop-Loss Lab' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Candle statistics' }));
    expect(screen.getByRole('heading', { name: 'Volatility & Wick Statistics' })).toBeTruthy();
    await act(async () => { useStore.getState().setLanguage('ko'); });
    expect(screen.getByRole('heading', { name: '변동성·꼬리 통계' })).toBeTruthy();
    expect(screen.getByRole('button', { name: '손절 실험실', pressed: false })).toBeTruthy();
  });

  it('uses one OHLC request, excludes the forming candle, and displays real sample count', async () => {
    setup();
    await screen.findByRole('table', { name: 'Per-candle volatility statistics' });
    expect(getOHLCV).toHaveBeenCalledWith('BTC', '4h', false, 501);
    expect(getOHLCV).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/500 requested · 20 completed/)).toBeTruthy();
    expect(within(screen.getByRole('region', { name: 'Candle volatility mean' })).getByText('3.00%')).toBeTruthy();
    expect(within(screen.getByRole('region', { name: 'Upper wick mean' })).getByText('2.00%')).toBeTruthy();
    expect(within(screen.getByRole('region', { name: 'Upper wick median' })).getByText('2.00%')).toBeTruthy();
    expect(within(screen.getByRole('region', { name: 'Lower wick mean' })).getByText('1.00%')).toBeTruthy();
    expect(within(screen.getByRole('region', { name: 'Lower wick median' })).getByText('1.00%')).toBeTruthy();
  });

  it('labels four timeframes in Korean without changing query values, including the collapsed sidebar', async () => {
    useStore.setState({ language: 'ko' });
    window.history.replaceState(null, '', '/volatility-statistics');
    setup(<App />);
    fireEvent.click(await screen.findByRole('button', { name: '기존 봉별 통계' }));
    await screen.findByRole('table', { name: '봉별 변동성·꼬리 통계' });
    const labels = [['4h', '4시간봉'], ['1d', '날봉'], ['1w', '주봉'], ['1M', '달봉']] as const;
    for (const [code, label] of labels) {
      const option = screen.getByRole('option', { name: label }) as HTMLOptionElement;
      expect(option.value).toBe(code);
      fireEvent.change(option.closest('select')!, { target: { value: code } });
      await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('BTC', code, false, 501));
      expect(screen.getByText(`BTC · ${label} · 봉 변동성·윗꼬리·아랫꼬리의 평균과 중위값`)).toBeTruthy();
      expect(useStore.getState().selectedInterval).toBe(code);
    }
    fireEvent.click(screen.getByRole('button', { name: '사이드바 접기' }));
    for (const [code, label] of labels) expect((screen.getByRole('option', { name: label }) as HTMLOptionElement).value).toBe(code);
    act(() => useStore.getState().setLanguage('en'));
    for (const [code] of labels) expect(screen.getByRole('option', { name: code })).toBeTruthy();
    expect(screen.getByText('BTC · 1M · Means and medians of candle volatility, upper wicks and lower wicks')).toBeTruthy();
  });

  it('allows custom N/count, applies explicitly, and recalculates units without another request', async () => {
    setup(); await screen.findByRole('table');
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Completed candles to load' }), { target: { value: '7' } });
    expect(getOHLCV).toHaveBeenCalledTimes(1);
    apply('3', '7');
    await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('BTC', '4h', false, 8));
    await screen.findByText(/N=3 · 7 requested · 7 completed/);
    expect(within(screen.getByRole('region', { name: 'Candle volatility mean' })).getByText('3.00')).toBeTruthy();
    const requests = vi.mocked(getOHLCV).mock.calls.length;
    apply('1', '7', 'percent');
    expect(within(screen.getByRole('region', { name: 'Candle volatility median' })).getByText('3.00%')).toBeTruthy();
    expect(getOHLCV).toHaveBeenCalledTimes(requests);
  });

  it('enforces integer/API bounds and supports the maximum completed count without silently capping N', async () => {
    setup(); await screen.findByRole('table');
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
    expect(within(screen.getByRole('region', { name: 'Candle volatility mean' })).getByText('—')).toBeTruthy();
  });

  it('replaces query data on coin/timeframe changes and cannot display a late previous selection', async () => {
    setup(); await screen.findByRole('table');
    let resolve!: (value: Awaited<ReturnType<typeof getOHLCV>>) => void;
    vi.mocked(getOHLCV).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
    act(() => useStore.getState().setSelectedCoin('ETH'));
    await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('ETH', '4h', false, 501));
    expect(screen.queryByRole('table')).toBeNull();
    act(() => useStore.getState().setSelectedInterval('1h'));
    await waitFor(() => expect(getOHLCV).toHaveBeenLastCalledWith('ETH', '1h', false, 501));
    await screen.findByRole('table');
    await act(async () => { resolve({ data: [], source: 'Old selection', count: 0 }); });
    expect(screen.queryByText(/Old selection/)).toBeNull();
    expect(screen.getByRole('table')).toBeTruthy();
  });

  it('replaces graphs with newest-first table values, explicit units and null warm-up cells', async () => {
    const view = setup();
    const table = await screen.findByRole('table', { name: 'Per-candle volatility statistics' });
    const rows = within(table).getAllByRole('row').slice(2);
    expect(rows).toHaveLength(20);
    expect(within(rows[0]).getByRole('rowheader').textContent).toBe('fixture-19');
    expect(within(rows[0]).getAllByRole('cell').map(cell => cell.textContent)).toEqual(['100.00', '3.00', '3.00', '2.00', '2.00', '1.00', '1.00']);
    expect(within(rows[19]).getByRole('rowheader').textContent).toBe('fixture-0');
    expect(within(rows[19]).getAllByRole('cell').map(cell => cell.textContent)).toEqual(['100.00', '—', '—', '—', '—', '—', '—']);
    expect(within(table).getByRole('columnheader', { name: 'Candle volatility mean (%)' })).toBeTruthy();
    expect(within(table).getByRole('columnheader', { name: 'Upper wick median (%)' })).toBeTruthy();
    expect(within(table).getByRole('columnheader', { name: 'Lower wick median (%)' })).toBeTruthy();
    expect(screen.queryByText(/standard deviation|표준편차/)).toBeNull();
    expect(screen.queryByRole('rowheader', { name: 'fixture-20' })).toBeNull();
    expect(view.container.querySelector('canvas')).toBeNull();
    expect((screen.getByRole('button', { name: 'Previous page' }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole('button', { name: 'Next page' }) as HTMLButtonElement).disabled).toBe(true);
    apply('1');
    expect(within(table).getByRole('columnheader', { name: 'Candle volatility mean' })).toBeTruthy();
    expect(within(rows[19]).getAllByRole('cell').map(cell => cell.textContent)).toEqual(['100.00', '3.00', '3.00', '2.00', '2.00', '1.00', '1.00']);
  });

  it('pages through every candle without extra requests, missing rows or recalculating on page subsets', async () => {
    const many = Array.from({ length: 106 }, (_, index) => ({ ...feed[0], open_time: index * 60_000, open_dt: `page-${index}` }));
    vi.mocked(getOHLCV).mockResolvedValue({ data: many, source: 'Synthetic fixture', count: 106 });
    setup();
    const table = await screen.findByRole('table');
    const pageRows = () => within(table).getAllByRole('row').slice(2);
    expect(pageRows()).toHaveLength(50);
    expect(within(pageRows()[0]).getByRole('rowheader').textContent).toBe('page-104');
    expect(within(pageRows()[49]).getByRole('rowheader').textContent).toBe('page-55');
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    expect(within(pageRows()[0]).getByRole('rowheader').textContent).toBe('page-54');
    expect(within(pageRows()[49]).getByRole('rowheader').textContent).toBe('page-5');
    // The oldest row on this page still has warm-up nulls from the full history.
    expect(within(pageRows()[49]).getAllByRole('cell')[1].textContent).toBe('—');
    // The newest row uses earlier candles beyond this page, not a new warm-up.
    expect(within(pageRows()[0]).getAllByRole('cell')[1].textContent).toBe('3.00');
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    expect(pageRows()).toHaveLength(5);
    expect(within(pageRows()[0]).getByRole('rowheader').textContent).toBe('page-4');
    expect(within(pageRows()[4]).getByRole('rowheader').textContent).toBe('page-0');
    expect((screen.getByRole('button', { name: 'Next page' }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole('button', { name: 'Previous page' }));
    expect(screen.getByText('51–100 of 105 candles · Page 2 of 3')).toBeTruthy();
    expect(getOHLCV).toHaveBeenCalledTimes(1);
    apply('3');
    expect(screen.getByText('1–50 of 105 candles · Page 1 of 3')).toBeTruthy();
    expect(getOHLCV).toHaveBeenCalledTimes(1);
    act(() => useStore.getState().setLanguage('ko'));
    expect(screen.getByRole('table', { name: '봉별 변동성·꼬리 통계' })).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: '봉 시작 시각' })).toBeTruthy();
    expect(screen.getByRole('button', { name: '다음 페이지' })).toBeTruthy();
  });

  it('places distinct arithmetic means and medians in all six summary and table fields', async () => {
    const rows = [1, 1, 100, 1e6].map((upper, index) => ({ ...feed[index], high: 100 + upper, low: 99 }));
    vi.mocked(getOHLCV).mockResolvedValue({ data: rows, source: 'Synthetic fixture', count: 4 });
    setup();
    const table = await screen.findByRole('table');
    apply('3');
    const latest = within(table).getAllByRole('row')[2];
    expect(within(latest).getAllByRole('cell').map(cell => cell.textContent)).toEqual(['100.00', '35.00', '2.00', '34.00', '1.00', '1.00', '1.00']);
    const expected = [
      ['Candle volatility mean', '35.00'], ['Candle volatility median', '2.00'],
      ['Upper wick mean', '34.00'], ['Upper wick median', '1.00'],
      ['Lower wick mean', '1.00'], ['Lower wick median', '1.00'],
    ];
    for (const [name, value] of expected) expect(within(screen.getByRole('region', { name })).getByText(value)).toBeTruthy();
    expect(getOHLCV).toHaveBeenCalledTimes(1);
  });

  it('shows valid zero ranges and wicks as zero rather than unavailable', async () => {
    vi.mocked(getOHLCV).mockResolvedValue({ data: feed.slice(0, 2).map(row => ({ ...row, open: 100, high: 100, low: 100, close: 100 })), source: 'Synthetic fixture', count: 2 });
    setup();
    const table = await screen.findByRole('table');
    apply('1');
    expect(within(within(table).getAllByRole('row')[2]).getAllByRole('cell').map(cell => cell.textContent)).toEqual(['100.00', ...Array(6).fill('0.00')]);
  });

  it('resets the table page on a different market selection', async () => {
    const many = Array.from({ length: 61 }, (_, index) => ({ ...feed[0], open_time: index * 60_000, open_dt: `before-${index}` }));
    vi.mocked(getOHLCV).mockResolvedValueOnce({ data: many, source: 'Synthetic fixture', count: 61 });
    setup(); await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    expect(screen.getByText('51–60 of 60 candles · Page 2 of 2')).toBeTruthy();
    act(() => useStore.getState().setSelectedCoin('ETH'));
    await screen.findByRole('rowheader', { name: 'fixture-19' });
    expect(screen.getByText('1–20 of 20 candles · Page 1 of 1')).toBeTruthy();
    expect(screen.queryByRole('rowheader', { name: 'before-9' })).toBeNull();
  });

  it('shows empty and network-error states without invented summaries', async () => {
    vi.mocked(getOHLCV).mockResolvedValueOnce({ data: [feed[0]], source: 'Fixture', count: 1 });
    const view = setup();
    await screen.findByText('No completed candles available.');
    expect(screen.queryByRole('table')).toBeNull();
    vi.mocked(getOHLCV).mockRejectedValue(new Error('Synthetic network failure'));
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(await screen.findByRole('alert', {}, { timeout: 4000 })).toBeTruthy();
    expect(view.container.textContent).toContain('Synthetic network failure');
    expect(screen.queryByRole('table')).toBeNull();
  });
});
