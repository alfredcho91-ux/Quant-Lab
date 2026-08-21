// 시장 데이터 API

import {
  api,
  ApiResponse,
  ApiClientError,
  ensureApiSuccess,
  toApiClientError,
  unwrapApiResponse,
} from './config';
import type {
  FearGreedIndex,
  MarketPrice,
  OHLCV,
  SRLevel,
  TradeReportData,
  VPVRData,
  VPVRSourceData,
} from '../types';
import { isOHLCV } from '../utils/ohlcv';

interface OHLCVResponse {
  data: OHLCV[];
  source: string;
  count: number;
}

export async function getMarketPrices(): Promise<Record<string, MarketPrice>> {
  try {
    const res = await api.get<ApiResponse<Record<string, MarketPrice>>>('/market/prices');
    return unwrapApiResponse(res, 'Failed to load market prices.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load market prices.');
  }
}

export async function getFearGreedIndex(): Promise<FearGreedIndex> {
  try {
    const res = await api.get<ApiResponse<FearGreedIndex>>('/market/fear-greed');
    return unwrapApiResponse(res, 'Failed to load the fear and greed index.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load the fear and greed index.');
  }
}

export async function getTimeframes(coin: string): Promise<{
  all: string[];
  binance: string[];
  csv: string[];
}> {
  try {
    const res = await api.get<ApiResponse<{ all: string[]; binance: string[]; csv: string[] }>>(
      `/timeframes/${coin}`
    );
    return unwrapApiResponse(res, 'Failed to load available timeframes.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load available timeframes.');
  }
}

export async function getOHLCV(
  coin: string,
  interval: string,
  useCsv: boolean = false,
  limit: number = 3000,
  endTime?: number,
): Promise<OHLCVResponse> {
  try {
    const res = await api.get<{
      success: boolean;
      data?: unknown;
      source: string;
      count: number;
      error?: string;
      error_code?: string | null;
      details?: unknown;
    }>(`/ohlcv/${coin}/${interval}`, {
      params: { use_csv: useCsv, limit, end_time: endTime },
      timeout: 30000,
    });
    const payload = ensureApiSuccess(res, 'Failed to load OHLCV data.');

    if (!Array.isArray(payload.data) || !payload.data.every(isOHLCV)) {
      throw new ApiClientError('OHLCV response contains invalid candle data.');
    }

    return {
      data: payload.data,
      source: payload.source,
      count: payload.count,
    };
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load OHLCV data.');
  }
}

export async function getTradeReport(
  coin: string,
  interval: string,
  options: {
    limit?: number;
    end_time?: number;
    as_of?: number;
    profile_candles?: number;
  },
): Promise<TradeReportData> {
  try {
    const res = await api.get<ApiResponse<TradeReportData>>(
      `/indicators/trade-report/${coin}/${interval}`,
      { params: options, timeout: 30000 },
    );
    const payload = unwrapApiResponse(res, 'Failed to load the trade report.');
    if (!Array.isArray(payload.candles) || !payload.candles.every(isOHLCV)) {
      throw new ApiClientError('Trade report response contains invalid candle data.');
    }
    return payload;
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load the trade report.');
  }
}

export async function getVPVRSource(
  coin: string,
  interval: string,
  candles?: number
): Promise<VPVRSourceData> {
  try {
    const res = await api.get<ApiResponse<VPVRSourceData>>(
      `/indicators/vpvr-source/${coin}/${interval}`,
      { params: { candles }, timeout: 20000 }
    );
    return unwrapApiResponse(res, 'Failed to load Binance VPVR source data.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load Binance VPVR source data.');
  }
}

export async function getVPVR(
  coin: string,
  interval: string,
  options?: { candles?: number; bin_count?: number; price_range?: number }
): Promise<VPVRData> {
  try {
    const res = await api.get<ApiResponse<VPVRData>>(
      `/indicators/vpvr/${coin}/${interval}`,
      { params: options, timeout: 20000 }
    );
    return unwrapApiResponse(res, 'Failed to calculate the Binance volume profile.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to calculate the Binance volume profile.');
  }
}

export async function getSupportResistance(
  coin: string,
  interval: string,
  options?: {
    lookback?: number;
    tolerance_pct?: number;
    min_touches?: number;
    show_pivots?: boolean;
    htf_option?: string;
  }
): Promise<SRLevel[]> {
  try {
    const res = await api.get<ApiResponse<SRLevel[]>>(`/support-resistance/${coin}/${interval}`, {
      params: options,
    });
    return unwrapApiResponse(res, 'Failed to load support and resistance levels.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load support and resistance levels.');
  }
}
