// 하이브리드 전략 분석 API

import { api } from './config';
import type { 
  HybridAnalysisParams, 
  HybridAnalysisResult, 
  HybridBacktestParams, 
  HybridBacktestResult,
  HybridLiveModeParams,
  HybridLiveModeResult
} from '../types';

/**
 * 하이브리드 전략 분석 실행
 */
export async function runHybridAnalysis(params: HybridAnalysisParams): Promise<HybridAnalysisResult> {
  const response = await api.post<HybridAnalysisResult>('/hybrid-analysis', params);
  return response.data;
}

/**
 * 하이브리드 전략 백테스팅 실행
 */
export async function runHybridBacktest(params: HybridBacktestParams): Promise<HybridBacktestResult> {
  const response = await api.post<HybridBacktestResult>('/hybrid-backtest', params);
  return response.data;
}

/**
 * 하이브리드 전략 라이브 모드 실행
 */
export async function runHybridLiveMode(params: HybridLiveModeParams): Promise<HybridLiveModeResult> {
  const response = await api.post<HybridLiveModeResult>('/hybrid-live', params);
  return response.data;
}
