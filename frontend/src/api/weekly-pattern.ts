// 주간 패턴 분석 API

import { api } from './config';
import type {
  WeeklyPatternParams,
  WeeklyPatternResult,
  WeeklyPatternManualParams,
  WeeklyPatternManualResult,
  WeeklyPatternBacktestParams,
  WeeklyPatternBacktestResult,
} from '../types';

export async function runWeeklyPattern(params: WeeklyPatternParams): Promise<WeeklyPatternResult | null> {
  try {
    const res = await api.post<{
      success: boolean;
      coin?: string;
      total_weeks?: number;
      warnings?: string[];
      filters?: {
        deep_drop_threshold: number;
        rsi_threshold: number;
        rsi_period?: number;
        atr_period?: number;
        vol_period?: number;
      };
      results?: {
        baseline?: any;
        deep_drop?: any;
        oversold?: any;
        contra?: any;
      };
      error?: string;
      error_type?: string;
      traceback?: string;
    }>('/weekly-pattern', params);
    
    if (res.data.success) {
      return res.data as WeeklyPatternResult;
    } else {
      return {
        success: false,
        coin: params.coin,
        total_weeks: 0,
        filters: {
          deep_drop_threshold: params.deep_drop_threshold,
          rsi_threshold: params.rsi_threshold,
        },
        results: {},
        error: res.data.error || 'Unknown error',
      };
    }
  } catch (err: any) {
    console.error('Weekly Pattern request failed:', err);
    return {
      success: false,
      coin: params.coin,
      total_weeks: 0,
      filters: {
        deep_drop_threshold: params.deep_drop_threshold,
        rsi_threshold: params.rsi_threshold,
      },
      results: {},
      error: err?.response?.data?.error || err?.message || 'Network error or server error',
    };
  }
}

export async function runWeeklyPatternManual(params: WeeklyPatternManualParams): Promise<WeeklyPatternManualResult | null> {
  try {
    const res = await api.post<WeeklyPatternManualResult>('/weekly-pattern-manual', params);
    return res.data;
  } catch (err) {
    console.error('Weekly Pattern Manual request failed:', err);
    return null;
  }
}

export async function runWeeklyPatternBacktest(params: WeeklyPatternBacktestParams): Promise<WeeklyPatternBacktestResult | null> {
  try {
    const res = await api.post<WeeklyPatternBacktestResult>('/weekly-pattern-backtest', params);
    return res.data;
  } catch (err) {
    console.error('Weekly Pattern Backtest request failed:', err);
    return null;
  }
}
