// 스캐너 API

import { api } from './config';
import type { PatternScanParams, PatternStat, ScannerResult } from '../types';

export async function runPatternScanner(params: PatternScanParams): Promise<{
  data: Record<string, Record<string, PatternStat>>;
  mode: string;
  position: string;
} | null> {
  try {
    const res = await api.post<{
      success: boolean;
      data: Record<string, Record<string, PatternStat>>;
      mode: string;
      position: string;
      error?: string;
    }>('/pattern-scanner', params);
    
    if (res.data.success) {
      return {
        data: res.data.data,
        mode: res.data.mode,
        position: res.data.position,
      };
    }
    console.error('Pattern Scanner error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Pattern Scanner request failed:', err);
    return null;
  }
}

export async function runStrategyScanner(params: {
  coin: string;
  interval: string;
  strategies?: string[];
  use_csv?: boolean;
}): Promise<ScannerResult | null> {
  try {
    const res = await api.post<{
      success: boolean;
      signals: ScannerResult['signals'];
      preset_signals: ScannerResult['preset_signals'];
      market_context: ScannerResult['market_context'];
      error?: string;
    }>('/scanner', params);
    
    if (res.data.success) {
      return {
        signals: res.data.signals,
        preset_signals: res.data.preset_signals,
        market_context: res.data.market_context,
      };
    }
    console.error('Scanner error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Scanner request failed:', err);
    return null;
  }
}
