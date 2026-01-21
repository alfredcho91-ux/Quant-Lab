// 통계 분석 API

import { api } from './config';
import type {
  BBMidParams,
  BBMidResult,
  BBMidExcursion,
  ComboFilterParams,
  ComboFilterResult,
  MultiTFSqueezeParams,
  SqueezeEvent,
  SqueezeStats,
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

export async function runMultiTFSqueeze(params: MultiTFSqueezeParams): Promise<{
  events: SqueezeEvent[];
  stats: SqueezeStats;
} | null> {
  try {
    const res = await api.post<{
      success: boolean;
      data: {
        events: SqueezeEvent[];
        stats: SqueezeStats;
      };
      error?: string;
    }>('/multi-tf-squeeze', params);
    
    if (res.data.success) {
      return res.data.data;
    }
    console.error('Multi-TF Squeeze error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Multi-TF Squeeze request failed:', err);
    return null;
  }
}
