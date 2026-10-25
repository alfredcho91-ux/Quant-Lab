// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { analyzeStopLossLab, getStopLossCandleStatistics, type CandleStatisticsResult, type Distribution, type LabConfig, type LabResult, type Metrics } from '../api/stopLossLab';
import { useStore } from '../store/useStore';
import StopLossLabPage from './StopLossLabPage';

vi.mock('../api/stopLossLab', () => ({ analyzeStopLossLab: vi.fn(), getStopLossCandleStatistics: vi.fn() }));
vi.mock('../components/EChart', () => ({ default: ({ option }: { option: unknown }) => <div data-testid="chart" data-option={JSON.stringify(option)} /> }));
vi.mock('../api/market', () => ({ getOHLCV: vi.fn(async () => ({ data: [], count: 0, source: 'fixture' })) }));

const d: Distribution = { count: 10, mean: 1, median: .5, std: .8, p50: .5, p75: .8, p90: 1.2, p95: 1.5, p99: 2, mean_median_ratio: 2, histogram: [{ lower: 0, upper: .1, count: 2, share_pct: 20 }], ecdf: [{ value: 0, probability_pct: 20 }, { value: 2, probability_pct: 100 }] };
const metrics: Metrics = { trade_count: 10, win_rate_pct: 50, average_r: .5, max_drawdown_pct: 2, cumulative_return_pct: 5, sufficient_sample: true, win_rate_ci95: [20, 80], ev_r_ci95: [-.1, 1.1] };
function result(config: LabConfig): LabResult {
  const distribution: LabResult['distributions'][string] = { candle_count: 10, metrics: { upper: { price: d, percent_open: d }, lower: { price: d, percent_open: d }, tr: { price: d, percent_open: d }, atr: { price: d, percent_open: d }, mtr: { price: d, percent_open: d }, atr_mtr_ratio: d } };
  const breakout = { depth_pct: d, returns_confirmed: 5, order_or_coverage_unknown: 1, return_rate_lower_pct: 50, return_minutes_upper_bound: d };
  return {
    config, data: { source: 'Synthetic fixture', as_of: Date.UTC(2026, 0, 15), fingerprint_sha256: 'synthetic-only', counts: { [config.execution_interval]: 100 }, execution_first: 0, execution_last: 100 },
    distributions: { '1d': distribution, '1w': distribution },
    weekend_distribution: { ...distribution, timezone: 'UTC', weekdays: ['Saturday', 'Sunday'], day_counts: { Saturday: 5, Sunday: 5 } },
    breakouts: { '1d': { Short: breakout, Long: breakout }, '1w': { Short: breakout, Long: breakout } },
    split_time: Date.UTC(2026, 0, 10), selected_id: 0,
    candidates: config.stop_values.map((stop, id) => ({
      id, entry: config.entry_values[0], stop, target: config.target_values[0], counts: { signals: 20, filled: 10, entry_order_unknown: 1 },
      overall: metrics, train: metrics, test: { ...metrics, trade_count: 3 }, train_quality_exclusions: 0,
      neighbourhood: { sampled_cells: 2, median_train_ev_r: .4, positive_fraction: 1 }, trades: [],
      groups: { year: { '2026': metrics }, regime: { bull: metrics } }, excursions: { mae_upper_pct: d, mfe_upper_pct: d },
    })),
    walk_forward: [{ train_end: Date.UTC(2026, 0, 10), test_end: Date.UTC(2026, 0, 15), candidate_id: 0, test: metrics }],
  };
}
function statistics(): CandleStatisticsResult {
  const distribution: LabResult['distributions'][string] = { candle_count: 10, metrics: { upper: { price: d, percent_open: d }, lower: { price: d, percent_open: d }, tr: { price: d, percent_open: d }, atr: { price: d, percent_open: d }, mtr: { price: d, percent_open: d }, atr_mtr_ratio: d } };
  return { config: { coin: 'BTC', start: '2026-01-01', end: '2026-01-10', lookback: 14 }, data: { source: 'fixture', as_of: Date.UTC(2026, 0, 11), fingerprint_sha256: 'fixture', candle_count: 10, first: Date.UTC(2026, 0, 1), last: Date.UTC(2026, 0, 11) }, distributions: { all: distribution, weekend: { ...distribution, candle_count: 2, timezone: 'UTC', weekdays: ['Saturday', 'Sunday'], day_counts: { Saturday: 1, Sunday: 1 } } } };
}
let client: QueryClient;
beforeEach(() => {
  vi.clearAllMocks();
  useStore.setState({ ...useStore.getInitialState(), language: 'en', selectedCoin: 'BTC' });
  client = new QueryClient({ defaultOptions: { mutations: { retry: false }, queries: { retry: false, gcTime: 0 } } });
  vi.mocked(analyzeStopLossLab).mockImplementation(async config => result(config));
  vi.mocked(getStopLossCandleStatistics).mockResolvedValue(statistics());
});
afterEach(() => { cleanup(); client.clear(); });
function setup() { render(<QueryClientProvider client={client}><StopLossLabPage /></QueryClientProvider>); }
const openLab = () => fireEvent.click(screen.getByRole('button', { name: 'Strategy experiment' }));
const run = () => fireEvent.click(screen.getByRole('button', { name: 'Run experiment' }));

describe('Stop-Loss Lab', () => {
  it('does not fetch on load and exposes actual configuration controls', () => {
    setup();
    expect(analyzeStopLossLab).not.toHaveBeenCalled();
    expect(getStopLossCandleStatistics).not.toHaveBeenCalled();
    expect(screen.getByRole('heading', { name: 'Candle statistics' })).toBeTruthy();
    openLab();
    const advanced = screen.getByText('Advanced settings').closest('details')!;
    expect(advanced.open).toBe(false);
    fireEvent.click(screen.getByText('Advanced settings'));
    expect(advanced.open).toBe(true);
    expect((screen.getByLabelText('Lookback N') as HTMLInputElement).value).toBe('14');
    expect(screen.getByLabelText('Maximum entries per period')).toBeTruthy();
  });

  it('loads daily statistics independently and switches to the weekend sample without rerunning', async () => {
    setup();
    fireEvent.change(screen.getByLabelText('Statistics start date UTC'), { target: { value: '2026-01-01' } });
    fireEvent.change(screen.getByLabelText('Statistics end date UTC'), { target: { value: '2026-01-10' } });
    fireEvent.click(screen.getByRole('button', { name: 'Load statistics' }));
    expect(await screen.findByRole('region', { name: 'Candle statistics results' })).toBeTruthy();
    expect(analyzeStopLossLab).not.toHaveBeenCalled();
    expect(getStopLossCandleStatistics).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText('Sample'), { target: { value: 'weekend' } });
    expect(screen.getByRole('heading', { name: 'Weekend candle statistics' })).toBeTruthy();
    expect(screen.getByText((_, node) => node?.textContent === 'Saturday / Sunday: 1 / 1')).toBeTruthy();
    expect(getStopLossCandleStatistics).toHaveBeenCalledTimes(1);
  });

  it('submits the exact grid and renders distributions, clickable cells and purged evaluation', async () => {
    setup();
    openLab();
    fireEvent.change(screen.getByLabelText('Stop values (comma separated)'), { target: { value: '0.3, 0.5' } });
    run();
    await screen.findByRole('table', { name: 'Stop-target heatmap' });
    const submitted = vi.mocked(analyzeStopLossLab).mock.calls[0][0];
    expect(submitted.stop_values).toEqual([.3, .5]);
    expect(submitted.fee_bps).toBe(5);
    expect(screen.getByRole('heading', { name: /Key result/ })).toBeTruthy();
    expect(screen.queryByRole('heading', { name: /Weekend statistics/ })).toBeNull();
    expect(screen.getByText('Risk/reward comparison')).toBeTruthy();
    expect(screen.getByText('Robustness analysis')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Cell 1' }));
    expect(screen.getByRole('button', { name: 'Cell 1' }).getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByRole('heading', { name: /Selected cell details #1/ })).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Evaluation slice'), { target: { value: 'train' } });
    expect(within(screen.getByRole('button', { name: 'Cell 1' })).getByText('N=10')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Evaluation slice'), { target: { value: 'test' } });
    expect(within(screen.getByRole('button', { name: 'Cell 1' })).getByText('N=3')).toBeTruthy();
    expect(analyzeStopLossLab).toHaveBeenCalledTimes(1);
  });

  it('binds late results to submitted settings, never relabels them as edited draft', async () => {
    let resolve!: (value: LabResult) => void;
    vi.mocked(analyzeStopLossLab).mockImplementation(() => new Promise(done => { resolve = done; }));
    setup(); openLab(); run();
    await waitFor(() => expect(analyzeStopLossLab).toHaveBeenCalledTimes(1));
    expect(client.isMutating()).toBe(1);
    const submitted = vi.mocked(analyzeStopLossLab).mock.calls[0][0];
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'ETH' } });
    fireEvent.change(screen.getByLabelText('Stop values (comma separated)'), { target: { value: '0.7' } });
    await act(async () => { resolve(result(submitted)); });
    await waitFor(() => expect(client.isMutating()).toBe(0));
    expect(screen.getByRole('status').textContent).toContain('previous submitted settings');
    expect(screen.getByRole('heading', { name: /Results for submitted settings · BTC/ })).toBeTruthy();
    expect((screen.getByLabelText('Symbol') as HTMLSelectElement).value).toBe('ETH');
    expect((screen.getByLabelText('Stop values (comma separated)') as HTMLInputElement).value).toBe('0.7');
  });

  it('rejects malformed and excessive grids without sending requests', () => {
    setup();
    openLab();
    fireEvent.change(screen.getByLabelText('Stop values (comma separated)'), { target: { value: '0.5,' } });
    run(); expect(screen.getByRole('alert').textContent).toContain('unique comma-separated');
    fireEvent.change(screen.getByLabelText('Stop values (comma separated)'), { target: { value: '.1,.2,.3,.4,.5,.6,.7,.8,.9,1' } });
    fireEvent.change(screen.getByLabelText('Target values (comma separated)'), { target: { value: '1,2,3,4,5,6,7,8,9,10' } });
    fireEvent.change(screen.getByLabelText('Entry values (comma separated)'), { target: { value: '0,.1' } });
    run(); expect(screen.getByRole('alert').textContent).toContain('Budget exceeded');
    expect(analyzeStopLossLab).not.toHaveBeenCalled();
  });

  it('shows unavailable market data as an error, not invented backtest results', async () => {
    vi.mocked(analyzeStopLossLab).mockRejectedValue(new Error('No completed market data'));
    setup(); openLab(); run();
    expect((await screen.findByRole('alert')).textContent).toContain('No completed market data');
    expect(screen.queryByRole('table', { name: 'Stop-target heatmap' })).toBeNull();
  });

  it('keeps legacy close-based table accessible and translates the new UI', async () => {
    setup();
    fireEvent.click(screen.getByText('Legacy candle statistics (advanced)'));
    expect(await screen.findByRole('heading', { name: 'Volatility & Wick Statistics' })).toBeTruthy();
    expect(screen.getByText(/legacy table uses close-based/i)).toBeTruthy();
    act(() => useStore.getState().setLanguage('ko'));
    expect(screen.getByRole('heading', { name: '손절 실험실' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: '전략 실험' }));
    expect(screen.getByRole('button', { name: '실험 실행' })).toBeTruthy();
  });
});
