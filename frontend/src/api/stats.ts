// 통계 분석 API

import {
  api,
  ApiResponse,
  ensureApiSuccess,
  toApiClientError,
  unwrapApiResponse,
} from './config';
import type {
  BBMidParams,
  BBMidResult,
  BBMidExcursion,
  TrendIndicatorsParams,
  TrendIndicatorsResult,
  IndicatorProjection,
} from '../types';

interface IndicatorProjectionPayload {
  current_price: number;
  current_rsi: number | null;
  vwaps: Array<{
    anchor: 'day' | 'week' | 'month' | 'quarter' | 'year';
    value: number | null;
  }>;
  rolling_vwaps: Array<{
    window: number;
    value: number | null;
  }>;
  vwap_deviation?: {
    anchor: 'month';
    length: number;
    source: string;
    vwap: number;
    standard_deviation: number;
    current_price: number;
    sigma: number | null;
    zone: string;
    bands: Record<string, number>;
  } | null;
  projections: {
    rsi_30: number;
    rsi_70: number;
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

export async function runTrendIndicators(params: TrendIndicatorsParams): Promise<TrendIndicatorsResult> {
  try {
    const res = await api.post<ApiResponse<Omit<TrendIndicatorsResult, 'success' | 'error'>>>(
      '/trend-indicators',
      params
    );
    const payload = unwrapApiResponse<Omit<TrendIndicatorsResult, 'success' | 'error'>>(
      res,
      'Failed to load trend indicators.'
    );
    return { success: true, ...payload };
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load trend indicators.');
  }
}

export async function getIndicatorProjection(coin: string, interval: string): Promise<IndicatorProjection> {
  try {
    const res = await api.get<ApiResponse<IndicatorProjectionPayload>>(
      `/indicators/projection?coin=${coin}&interval=${interval}`
    );
    const { current_price, current_rsi, vwaps, rolling_vwaps, vwap_deviation, projections } = unwrapApiResponse(
      res,
      'Failed to load indicator projections.'
    );
    return {
      current_price,
      current_rsi,
      vwaps,
      rolling_vwaps,
      rsi_30_price: projections.rsi_30,
      rsi_70_price: projections.rsi_70,
      vwap_deviation: vwap_deviation ?? null,
    };
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load indicator projections.');
  }
}
