// 백테스트 API

import { api, ensureApiSuccess, toApiClientError } from './config';
import type { BacktestParams, BacktestResult, AdvancedBacktestResult } from '../types';

export async function runBacktest(params: BacktestParams): Promise<BacktestResult> {
  try {
    const res = await api.post<{
      success: boolean;
      chart_data: BacktestResult['chart_data'];
      trades: BacktestResult['trades'];
      summary: BacktestResult['summary'];
      error?: string;
      error_code?: string | null;
      details?: unknown;
    }>('/backtest', params);

    const payload = ensureApiSuccess(res, 'Backtest failed.');
    return {
      chart_data: payload.chart_data,
      trades: payload.trades,
      summary: payload.summary,
    };
  } catch (error: unknown) {
    throw toApiClientError(error, 'Backtest failed.');
  }
}

export async function runAdvancedBacktest(params: BacktestParams & {
  train_ratio?: number;
  monte_carlo_runs?: number;
}): Promise<AdvancedBacktestResult> {
  try {
    const res = await api.post<{
      success: boolean;
      chart_data: AdvancedBacktestResult['chart_data'];
      trades: AdvancedBacktestResult['trades'];
      in_sample: AdvancedBacktestResult['in_sample'];
      out_of_sample: AdvancedBacktestResult['out_of_sample'];
      full: AdvancedBacktestResult['full'];
      monte_carlo: AdvancedBacktestResult['monte_carlo'];
      error?: string;
      error_code?: string | null;
      details?: unknown;
    }>('/backtest-advanced', params);

    const payload = ensureApiSuccess(res, 'Advanced backtest failed.');
    return {
      chart_data: payload.chart_data,
      trades: payload.trades,
      in_sample: payload.in_sample,
      out_of_sample: payload.out_of_sample,
      full: payload.full,
      monte_carlo: payload.monte_carlo,
    };
  } catch (error: unknown) {
    throw toApiClientError(error, 'Advanced backtest failed.');
  }
}
