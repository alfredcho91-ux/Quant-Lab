// 백테스트 API

import { api } from './config';
import type { BacktestParams, BacktestResult, AdvancedBacktestResult } from '../types';

export async function runBacktest(params: BacktestParams): Promise<BacktestResult | null> {
  try {
    const res = await api.post<{
      success: boolean;
      chart_data: BacktestResult['chart_data'];
      trades: BacktestResult['trades'];
      summary: BacktestResult['summary'];
      error?: string;
    }>('/backtest', params);
    
    if (res.data.success) {
      return {
        chart_data: res.data.chart_data,
        trades: res.data.trades,
        summary: res.data.summary,
      };
    }
    console.error('Backtest error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Backtest request failed:', err);
    return null;
  }
}

export async function runAdvancedBacktest(params: BacktestParams & {
  train_ratio?: number;
  monte_carlo_runs?: number;
}): Promise<AdvancedBacktestResult | null> {
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
    }>('/backtest-advanced', params);
    
    if (res.data.success) {
      return {
        chart_data: res.data.chart_data,
        trades: res.data.trades,
        in_sample: res.data.in_sample,
        out_of_sample: res.data.out_of_sample,
        full: res.data.full,
        monte_carlo: res.data.monte_carlo,
      };
    }
    console.error('Advanced Backtest error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Advanced Backtest request failed:', err);
    return null;
  }
}
