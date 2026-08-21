// 백테스트 API

import { api, ensureApiSuccess, toApiClientError } from './config';
import type { BacktestParams, BacktestResult } from '../types';

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
