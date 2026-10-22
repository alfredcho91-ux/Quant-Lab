// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import TrendChartPage from './TrendChartPage';
import { TrendPriceChart } from '../components/TrendPriceChart';
import { useTrendPriceChart } from '../hooks/useTrendPriceChart';
import { useStore } from '../store/useStore';
import { normalizeWickSettings } from '../utils/wickStatistics';
import type { OHLCV } from '../types';

const createMock = vi.hoisted(() => vi.fn());
vi.mock('lightweight-charts', () => ({
  createChart: createMock, CandlestickSeries: 'Candlestick', LineSeries: 'Line',
  ColorType: { Solid: 'solid' }, CrosshairMode: { Normal: 0 },
  LineStyle: { Solid: 0, Dotted: 1, Dashed: 2, LargeDashed: 3 },
}));
vi.mock('../hooks/useTrendPriceChart', () => ({ useTrendPriceChart: vi.fn() }));
vi.mock('../hooks/usePageCommon', () => ({ usePageCommon: () => ({ isKo: false }) }));

function newChart() {
  const listeners: { crosshair?: (event: { time?: number; seriesData: Map<unknown, unknown> }) => void } = {};
  const scale = { subscribeVisibleLogicalRangeChange: vi.fn(), fitContent: vi.fn() };
  const pane = () => ({ getHeight: () => 320, setHeight: vi.fn(), priceScale: () => ({ applyOptions: vi.fn() }) });
  const panes = [pane(), pane()];
  return {
    addSeries: vi.fn((_definition: string, _options: Record<string, unknown>, _paneIndex = 0) => ({
      setData: vi.fn((_data: Array<{time: number; value?: number}>) => {}), createPriceLine: vi.fn(), priceToCoordinate: () => 100,
    })),
    panes: () => panes, timeScale: () => scale, resize: vi.fn(), remove: vi.fn(), listeners,
    subscribeCrosshairMove: vi.fn((callback: NonNullable<typeof listeners.crosshair>) => { listeners.crosshair = callback; }),
  };
}
const latestChart = () => createMock.mock.results[createMock.mock.results.length - 1]?.value as ReturnType<typeof newChart>;
function bars(step = 60_000): OHLCV[] {
  return [1, 3, 5, 7].map((upper, index) => ({
    open_time: Date.UTC(2026, 0, 1) + index * step, open_dt: String(index),
    open: 100, high: 100 + upper, low: 98, close: 100, volume: 1,
  }));
}
function mockFeed(data: OHLCV[]) {
  return { trendChartData: data, chartPriceLevels: [], isRefreshing: false,
    isTrendChartError: false, isTrendChartLoading: false, refresh: vi.fn(),
    selectedProjection: undefined, vpvrData: undefined } as unknown as ReturnType<typeof useTrendPriceChart>;
}

beforeEach(() => {
  localStorage.clear();
  useStore.setState({ ...useStore.getInitialState(), language: 'en', wickStatistics: normalizeWickSettings({ period: 2 }) });
  createMock.mockReset();
  createMock.mockImplementation(newChart);
  vi.mocked(useTrendPriceChart).mockImplementation((_coin, interval) => mockFeed(bars(interval === '1h' ? 3_600_000 : 60_000)));
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => { callback(0); return 1; });
  vi.stubGlobal('cancelAnimationFrame', vi.fn());
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe('Wick Statistics on the existing trend chart', () => {
  it('adds exactly four line series in native pane 1 with candle-aligned timestamps and warm-up whitespace', () => {
    render(<TrendChartPage />);
    const chart = latestChart();
    expect(chart.addSeries.mock.calls).toHaveLength(5);
    for (let index = 1; index <= 4; index++) {
      expect(chart.addSeries.mock.calls[index]).toEqual(['Line', expect.objectContaining({ visible: true, priceLineVisible: false }), 1]);
      const plotted = chart.addSeries.mock.results[index].value.setData.mock.calls[0][0];
      expect(plotted.map((item: {time: number}) => item.time)).toEqual(bars().map(bar => bar.open_time / 1000));
      expect(plotted[0]).toEqual({ time: bars()[0].open_time / 1000 });
    }
    expect(chart.addSeries.mock.results[1].value.setData.mock.calls[0][0][1].value).toBe(2);
    expect(chart.panes()[1].setHeight).toHaveBeenCalled();
    expect(chart.timeScale().fitContent).toHaveBeenCalledTimes(1);
  });
  it('updates the shared crosshair legend at the hovered bar, including null rather than false zero', () => {
    render(<TrendChartPage />);
    const chart = latestChart();
    act(() => chart.listeners.crosshair?.({ time: bars()[1].open_time / 1000, seriesData: new Map() }));
    expect(screen.getByText('AUW 2.00')).toBeTruthy();
    act(() => chart.listeners.crosshair?.({ time: bars()[0].open_time / 1000, seriesData: new Map() }));
    expect(screen.getByText('AUW —')).toBeTruthy();
    act(() => chart.listeners.crosshair?.({ seriesData: new Map() }));
    expect(screen.getByText('AUW 6.00')).toBeTruthy();
  });
  it('recalculates period/unit, accepts positive integers and never applies invalid drafts', () => {
    render(<TrendChartPage />);
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Period' }), { target: { value: '4' } });
    let plotted = latestChart().addSeries.mock.results[1].value.setData.mock.calls[0][0];
    expect(plotted.slice(0, 3).every((item: {value?:number}) => item.value === undefined)).toBe(true);
    expect(plotted[3].value).toBe(4);
    fireEvent.change(screen.getByRole('combobox', { name: 'Unit' }), { target: { value: 'percent' } });
    expect(latestChart().addSeries.mock.calls[1][1]).toMatchObject({ priceFormat: { type: 'percent' } });
    plotted = latestChart().addSeries.mock.results[1].value.setData.mock.calls[0][0];
    expect(plotted[3].value).toBe(4);
    for (const invalid of ['', '0', '-2', '2.5']) {
      fireEvent.change(screen.getByRole('spinbutton', { name: 'Period' }), { target: { value: invalid } });
      expect(screen.getByRole('alert').textContent).toContain('positive integer');
      expect(useStore.getState().wickStatistics.period).toBe(4);
    }
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Period' }), { target: { value: '1000' } });
    expect(useStore.getState().wickStatistics.period).toBe(1000);
    expect(screen.getByText('AUW —')).toBeTruthy();
  });
  it('toggles each series independently, including hiding all four', () => {
    render(<TrendChartPage />);
    for (const label of ['AUW', 'MUW', 'ALW', 'MLW']) {
      fireEvent.click(screen.getByRole('checkbox', { name: new RegExp(label) }));
    }
    expect(useStore.getState().wickStatistics.visible).toEqual({ auw: false, muw: false, alw: false, mlw: false });
    for (const call of latestChart().addSeries.mock.calls.slice(1)) expect(call[1]).toMatchObject({ visible: false });
    fireEvent.click(screen.getByRole('checkbox', { name: /MUW/ }));
    expect(latestChart().addSeries.mock.calls[2][1]).toMatchObject({ visible: true });
    expect(latestChart().addSeries.mock.calls[1][1]).toMatchObject({ visible: false });
  });
  it('distributes all loaded completed candles independently of rolling period, unit and visibility', () => {
    render(<TrendChartPage />);
    const contents = () => screen.getByRole('table', { name: 'Upper and lower wick 0.1% distribution' }).textContent;
    expect(screen.getByText('4 total · 4 valid · 0 excluded')).toBeTruthy();
    const original = contents();
    for (const name of ['1.0–1.1%', '3.0–3.1%', '5.0–5.1%', '7.0–7.1%']) {
      expect(screen.getByRole('rowheader', { name })).toBeTruthy();
    }
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Period' }), { target: { value: '1000' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'Unit' }), { target: { value: 'percent' } });
    for (const label of ['AUW', 'MUW', 'ALW', 'MLW']) fireEvent.click(screen.getByRole('checkbox', { name: new RegExp(label) }));
    expect(contents()).toBe(original);
    vi.mocked(useTrendPriceChart).mockReturnValue(mockFeed([bars()[0]]));
    act(() => useStore.getState().setSelectedInterval('1h'));
    expect(screen.getByText('1 total · 1 valid · 0 excluded')).toBeTruthy();
    expect(screen.queryByRole('rowheader', { name: '7.0–7.1%' })).toBeNull();
  });
  it('switches timeframe and coin using the existing query, replacing rather than mixing timestamps', () => {
    render(<TrendChartPage />);
    act(() => useStore.getState().setSelectedInterval('1h'));
    act(() => useStore.getState().setSelectedCoin('ETH'));
    expect(useTrendPriceChart).toHaveBeenLastCalledWith('ETH', '1h');
    const chart = latestChart();
    const candleTimes = chart.addSeries.mock.results[0].value.setData.mock.calls[0][0].map((item: {time: number}) => item.time);
    const wickTimes = chart.addSeries.mock.results[1].value.setData.mock.calls[0][0].map((item: {time: number}) => item.time);
    expect(wickTimes).toEqual(candleTimes);
    expect(wickTimes[1] - wickTimes[0]).toBe(3600);
  });
  it('persists period, unit and visibility in the existing store and restores them after hydration', async () => {
    const view = render(<TrendChartPage />);
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Period' }), { target: { value: '3' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'Unit' }), { target: { value: 'percent' } });
    fireEvent.click(screen.getByRole('checkbox', { name: /ALW/ }));
    const saved = localStorage.getItem('quant-lab-storage')!;
    view.unmount();
    useStore.setState({ wickStatistics: normalizeWickSettings(null) });
    localStorage.setItem('quant-lab-storage', saved);
    await act(async () => { await useStore.persist.rehydrate(); });
    render(<TrendChartPage />);
    expect((screen.getByRole('spinbutton', { name: 'Period' }) as HTMLInputElement).value).toBe('3');
    expect((screen.getByRole('combobox', { name: 'Unit' }) as HTMLSelectElement).value).toBe('percent');
    expect((screen.getByRole('checkbox', { name: /ALW/ }) as HTMLInputElement).checked).toBe(false);
  });
  it('restores defaults for old/corrupt saved state without changing existing backtest parameters', () => {
    const merge = useStore.persist.getOptions().merge!;
    const initial = useStore.getInitialState();
    expect(merge({ language: 'en' }, initial).wickStatistics.period).toBe(14);
    const state = merge({ wickStatistics: { period: -1, visible: { auw: false } } }, initial);
    expect(state.wickStatistics).toEqual({ period: 14, unit: 'price', visible: { auw: false, muw: true, alw: true, mlw: true } });
    expect(state.backtestParams.atr_length).toBe(initial.backtestParams.atr_length);
  });
  it('keeps other users of TrendPriceChart unchanged when no wick group is requested', () => {
    const view = render(<TrendPriceChart data={bars()} priceLevels={[]} verticalZoom={1} isKo={false} />);
    const chart = latestChart();
    expect(chart.addSeries).toHaveBeenCalledTimes(1);
    view.unmount();
    expect(chart.remove).toHaveBeenCalledTimes(1);
    expect(cancelAnimationFrame).toHaveBeenCalled();
  });
});
