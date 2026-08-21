// 전략 관련 API

import {
  api,
  ApiResponse,
  ensureApiSuccess,
  toApiClientError,
  unwrapApiResponse,
} from './config';
import type { Strategy, StrategyInfo, Preset, BacktestParams } from '../types';

export async function getStrategies(): Promise<Strategy[]> {
  try {
    const res = await api.get<ApiResponse<Strategy[]>>('/strategies');
    return unwrapApiResponse(res, 'Failed to load strategies.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load strategies.');
  }
}

export async function getStrategyInfo(
  strategyId: string,
  lang: string = 'ko',
  params?: {
    rsi_ob?: number;
    sma_main_len?: number;
    sma1_len?: number;
    sma2_len?: number;
  }
): Promise<StrategyInfo> {
  try {
    const res = await api.get<ApiResponse<StrategyInfo>>(`/strategy-info/${strategyId}`, {
      params: { lang, ...params },
    });
    return unwrapApiResponse(res, 'Failed to load strategy information.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load strategy information.');
  }
}

export async function getPresets(): Promise<Record<string, Preset>> {
  try {
    const res = await api.get<ApiResponse<Record<string, Preset>>>('/presets');
    return unwrapApiResponse(res, 'Failed to load presets.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to load presets.');
  }
}

export async function savePreset(
  name: string,
  coin: string,
  interval: string,
  stratId: string,
  direction: string,
  params: Partial<BacktestParams>
): Promise<boolean> {
  try {
    const res = await api.post<ApiResponse<null>>('/presets', {
      name,
      coin,
      interval,
      strat_id: stratId,
      direction,
      params,
    });
    ensureApiSuccess(res, 'Failed to save the preset.');
    return true;
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to save the preset.');
  }
}

export async function deletePreset(name: string): Promise<boolean> {
  try {
    const res = await api.delete<ApiResponse<null>>(`/presets/${name}`);
    ensureApiSuccess(res, 'Failed to delete the preset.');
    return true;
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to delete the preset.');
  }
}
