/**
 * AI Lab API Client
 */
import { api, ensureApiSuccess, toApiClientError } from './config';
import type { BacktestResult } from '../types';

export interface AIResearchRequest {
  prompt: string;
  api_key?: string;
  provider?: 'gemini';
  model?: string;
  temperature?: number;
  history?: Array<{ role: string; content: string }>;
}

export interface ConditionalProbabilityAnalysis {
  analysis_type: 'conditional_probability';
  coin: string;
  interval: string;
  source: string;
  condition: {
    target_side: 'bull' | 'bear';
    condition_text: string;
    components?: Array<Record<string, unknown>>;
    ignored_conditions?: string[];
    expression_tokens?: string[];
  };
  summary: {
    sample_count: number;
    success_count: number;
    failure_count: number;
    probability_rate?: number | null;
    ci_lower?: number | null;
    ci_upper?: number | null;
    p_value?: number | null;
    p_value_reliability?: 'Very High' | 'High' | 'Medium' | 'Low' | 'N/A';
    reliability: string;
    gati_index: number;
  };
  outcome_bars: Array<{
    key: 'success' | 'failure';
    label: string;
    count: number;
    rate_pct: number;
  }>;
  confidence_band: {
    baseline: number;
    center?: number | null;
    lower?: number | null;
    upper?: number | null;
  };
  generated_at: string;
}

export interface OptimizationCharacteristicsAnalysis {
  analysis_type: 'optimization_characteristics';
  summary: {
    trial_count: number;
    bucket_size: number;
    top_avg_oos_pnl: number | null;
    bottom_avg_oos_pnl: number | null;
    top_avg_oos_win_rate: number | null;
    bottom_avg_oos_win_rate: number | null;
  };
  highlights: Array<{
    param: string;
    label: string;
    direction: 'higher_better' | 'lower_better';
    top_mean: number;
    bottom_mean: number;
    effect_pct: number;
    interpretation: string;
  }>;
}

export type AIAnalysisResult = ConditionalProbabilityAnalysis | OptimizationCharacteristicsAnalysis;

export interface AIResearchResponse {
  success: boolean;
  answer: string;
  backtest_params?: Record<string, unknown>;
  backtest_result?: BacktestResult;
  analysis_result?: AIAnalysisResult | null;
  needs_clarification?: boolean;
  clarifying_questions?: string[] | null;
  cache_hit?: boolean | null;
  execution_path?: string | null;
  error?: string;
  error_code?: string | null;
}

export async function runAIResearch(request: AIResearchRequest): Promise<AIResearchResponse> {
  try {
    const res = await api.post<AIResearchResponse>('/ai/research', request);
    return ensureApiSuccess(res, 'AI research failed.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'AI research failed.');
  }
}

export interface AIAnalystRequest {
  prompt: string;
  coin: string;
  interval: string;
  api_key?: string;
  provider?: 'gemini';
  model?: string;
  temperature?: number;
  history?: Array<{ role: string; content: string }>;
}

export interface AIAnalystResponse {
  success: boolean;
  answer: string;
  execution_path?: string | null;
  cache_hit?: boolean | null;
  error?: string;
}

export async function runAIAnalyst(request: AIAnalystRequest): Promise<AIAnalystResponse> {
  try {
    const res = await api.post<AIAnalystResponse>('/ai/analyst', request);
    return ensureApiSuccess(res, 'AI analyst request failed.');
  } catch (error: unknown) {
    throw toApiClientError(error, 'AI analyst request failed.');
  }
}
