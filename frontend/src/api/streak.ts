// 연속 봉패턴 분석 API

import { ApiClientError, api, toApiClientError, unwrapApiResponse } from './config';
import type { StreakAnalysisParams, StreakAnalysisResult } from '../types';

type StreakAnalysisApiPayload = Partial<StreakAnalysisResult>;

function hasCoreStreakFields(payload: StreakAnalysisApiPayload): payload is StreakAnalysisResult {
  return (
    typeof payload.total_cases === 'number' &&
    typeof payload.continuation_count === 'number' &&
    typeof payload.reversal_count === 'number' &&
    typeof payload.c1_green_count === 'number' &&
    typeof payload.c1_red_count === 'number' &&
    payload.comparative_report !== undefined &&
    payload.coin !== undefined &&
    payload.interval !== undefined &&
    payload.n_streak !== undefined &&
    payload.direction !== undefined
  );
}

export async function runStreakAnalysis(params: StreakAnalysisParams): Promise<StreakAnalysisResult> {
  try {
    const res = await api.post('/streak-analysis', params);
    const payload = unwrapApiResponse<StreakAnalysisApiPayload>(
      res,
      'Failed to run streak analysis.'
    );
    if (hasCoreStreakFields(payload)) return payload;
    throw new ApiClientError('Streak analysis returned an incomplete result.', {
      details: payload,
    });
  } catch (error: unknown) {
    throw toApiClientError(error, 'Failed to run streak analysis.');
  }
}
