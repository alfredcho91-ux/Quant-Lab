// 전략 관련 API

import { api, ApiResponse } from './config';
import type { Strategy, StrategyInfo, Preset, BacktestParams } from '../types';

export async function getStrategies(): Promise<Strategy[] | null> {
  try {
    const res = await api.get<ApiResponse<Strategy[]>>('/strategies');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
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
): Promise<StrategyInfo | null> {
  try {
    const res = await api.get<ApiResponse<StrategyInfo>>(`/strategy-info/${strategyId}`, {
      params: { lang, ...params },
    });
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function getPresets(): Promise<Record<string, Preset> | null> {
  try {
    const res = await api.get<ApiResponse<Record<string, Preset>>>('/presets');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
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
    return res.data.success;
  } catch {
    return false;
  }
}

export async function deletePreset(name: string): Promise<boolean> {
  try {
    const res = await api.delete<ApiResponse<null>>(`/presets/${name}`);
    return res.data.success;
  } catch {
    return false;
  }
}
