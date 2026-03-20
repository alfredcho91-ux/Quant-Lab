// 통계 분석 API

import { api, ensureApiSuccess, toApiClientError, unwrapApiResponse } from './config';
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

interface IndicatorProjectionPayload {
  current_price: number;
  projections: {
    rsi_30: number;
    rsi_70: number;
    stoch_20: number;
    stoch_80: number;
    stoch_hh?: number;
    stoch_ll?: number;
  };
}


export async function runBBMid(params: BBMidParams): Promise<{
  data: BBMidResult[];
  excursions: Record<string, BBMidExcursion>;
  start_side: string;
}> {
  try {
    const res = await api.post<{
      success: boolean;
      data: BBMidResult[];
      excursions: Record<string, BBMidExcursion>;
      start_side: string;
      error?: string;
      error_code?: string | null;
      details?: unknown;
    }>('/bb-mid', params);

    const payload = ensureApiSuccess(res, 'Failed to run BB Mid analysis.');
    return {
      data: payload.data,
      excursions: payload.excursions,
      start_side: payload.start_side,
    };
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to run BB Mid analysis.');
  }
}

export async function runComboFilter(params: ComboFilterParams): Promise<ComboFilterResult> {
  try {
    const res = await api.post<{
      success: boolean;
      data: ComboFilterResult;
      error?: string;
      error_code?: string | null;
      details?: unknown;
    }>('/combo-filter', params);

    const payload = ensureApiSuccess(res, 'Failed to run combo filter analysis.');
    return payload.data;
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to run combo filter analysis.');
  }
}

export async function runTrendIndicators(params: TrendIndicatorsParams): Promise<TrendIndicatorsResult> {
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
    data: Partial<Omit<TrendIndicatorsResult, 'success' | 'error'>> | undefined
  ): TrendIndicatorsResult => ({
    success: true,
    latest: data?.latest ?? emptyLatest,
    series: data?.series ?? {},
    interval: data?.interval ?? params.interval,
    coin: data?.coin ?? params.coin,
  });

  try {
    const res = await api.post(
      '/trend-indicators',
      params
    );
    const payload = unwrapApiResponse<Omit<TrendIndicatorsResult, 'success' | 'error'>>(
      res,
      'Failed to load trend indicators.'
    );
    return toResult(payload);
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load trend indicators.');
  }
}

export async function getIndicatorProjection(coin: string, interval: string): Promise<IndicatorProjection | null> {
  try {
    const res = await api.get<{ success: boolean; data: IndicatorProjectionPayload }>(
      `/indicators/projection?coin=${coin}&interval=${interval}`
    );
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
