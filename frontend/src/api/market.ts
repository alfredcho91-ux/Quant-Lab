// 시장 데이터 API

import { api, ApiResponse } from './config';
import type { MarketPrice, FearGreedIndex, SRLevel } from '../types';

export async function getMarketPrices(): Promise<Record<string, MarketPrice> | null> {
  try {
    const res = await api.get<ApiResponse<Record<string, MarketPrice>>>('/market/prices');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function getFearGreedIndex(): Promise<FearGreedIndex | null> {
  try {
    const res = await api.get<ApiResponse<FearGreedIndex>>('/market/fear-greed');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function getTimeframes(coin: string): Promise<{
  all: string[];
  binance: string[];
  csv: string[];
} | null> {
  try {
    const res = await api.get<ApiResponse<{ all: string[]; binance: string[]; csv: string[] }>>(
      `/timeframes/${coin}`
    );
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function getOHLCV(
  coin: string,
  interval: string,
  useCsv: boolean = false,
  limit: number = 3000
): Promise<{ data: unknown[]; source: string; count: number } | null> {
  try {
    const res = await api.get(`/ohlcv/${coin}/${interval}`, {
      params: { use_csv: useCsv, limit },
      timeout: 30000,  // 30초 타임아웃 (개별 요청용)
    });
    return res.data.success ? res.data : null;
  } catch (err: any) {
    console.error('getOHLCV error:', err?.message || err);
    if (err?.code === 'ECONNABORTED') {
      console.error('getOHLCV timeout - API가 응답하지 않습니다');
    }
    return null;
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
): Promise<SRLevel[] | null> {
  try {
    const res = await api.get<ApiResponse<SRLevel[]>>(`/support-resistance/${coin}/${interval}`, {
      params: options,
    });
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}
