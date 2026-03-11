// 통계 분석 API

import { api } from './config';
import type { ApiResponse } from './config';
import type {
  BBMidParams,
  BBMidResult,
  BBMidExcursion,
  ComboFilterParams,
  ComboFilterResult,
  TrendIndicatorsParams,
  TrendIndicatorsResult,
  TrendIndicatorsLatest,
  IndicatorProjection,
} from '../types';


export async function runBBMid(params: BBMidParams): Promise<{
  data: BBMidResult[];
  excursions: Record<string, BBMidExcursion>;
  start_side: string;
} | null> {
  try {
    const res = await api.post<{
      success: boolean;
      data: BBMidResult[];
      excursions: Record<string, BBMidExcursion>;
      start_side: string;
      error?: string;
    }>('/bb-mid', params);
    
    if (res.data.success) {
      return {
        data: res.data.data,
        excursions: res.data.excursions,
        start_side: res.data.start_side,
      };
    }
    console.error('BB Mid error:', res.data.error);
    return null;
  } catch (err) {
    console.error('BB Mid request failed:', err);
    return null;
  }
}

export async function runComboFilter(params: ComboFilterParams): Promise<ComboFilterResult | null> {
  try {
    const res = await api.post<{
      success: boolean;
      data: ComboFilterResult;
      error?: string;
    }>('/combo-filter', params);
    
    if (res.data.success) {
      return res.data.data;
    }
    console.error('Combo Filter error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Combo Filter request failed:', err);
    return null;
  }
}

export async function runTrendIndicators(params: TrendIndicatorsParams): Promise<TrendIndicatorsResult | null> {
  const emptyLatest: TrendIndicatorsLatest = {
    close: null,
    rsi: null,
    macd_hist: null,
    adx: null,
    atr: null,
    atr_pct: null,
    sma20: null,
    sma50: null,
    sma200: null,
    slow_stoch_5k: null,
    slow_stoch_5d: null,
    slow_stoch_10k: null,
    slow_stoch_10d: null,
    slow_stoch_20k: null,
    slow_stoch_20d: null,
    vwap_20: null,
    supertrend: null,
    supertrend_dir: null,
  };

  const toResult = (
    data: Partial<Omit<TrendIndicatorsResult, 'success' | 'error'>> | undefined,
    success: boolean,
    error?: string
  ): TrendIndicatorsResult => ({
    success,
    latest: data?.latest ?? emptyLatest,
    series: data?.series ?? {},
    interval: data?.interval ?? params.interval,
    coin: data?.coin ?? params.coin,
    ...(error ? { error } : {}),
  });

  try {
    const res = await api.post<ApiResponse<Omit<TrendIndicatorsResult, 'success' | 'error'>>>(
      '/trend-indicators',
      params
    );
    if (res.data.success && res.data.data) {
      return toResult(res.data.data, true);
    }
    if (res.data.data) return toResult(res.data.data, false, res.data.error || 'Partial trend payload');
    console.error('Trend Indicators error:', res.data.error);
    return toResult(undefined, false, res.data.error || 'Failed to load trend indicators');
  } catch (err) {
    console.error('Trend Indicators request failed:', err);
    return null;
  }
}

export async function getIndicatorProjection(coin: string, interval: string): Promise<IndicatorProjection | null> {
  try {
    const res = await api.get<{success: boolean, data: {current_price: number, projections: any}}>(`/indicators/projection?coin=${coin}&interval=${interval}`);
    if (res.data && res.data.success) {
      const { current_price, projections } = res.data.data;
      return {
        current_price,
        rsi_30_price: projections.rsi_30,
        rsi_70_price: projections.rsi_70,
        stoch_20_price: projections.stoch_20,
        stoch_80_price: projections.stoch_80,
        stoch_hh: projections.stoch_hh,
        stoch_ll: projections.stoch_ll
      };
    }
    return null;
  } catch (err) {
    console.error('Indicator Projection request failed:', err);
    return null;
  }
}
