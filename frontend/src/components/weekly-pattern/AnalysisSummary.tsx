// 주간 패턴 분석 - 분석 요약 컴포넌트

import type { WeeklyPatternResult } from '../../types';

interface AnalysisSummaryProps {
  result: WeeklyPatternResult;
  isKo: boolean;
}

export function AnalysisSummary({ result, isKo }: AnalysisSummaryProps) {
  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold mb-4">
        {isKo ? '분석 요약' : 'Analysis Summary'}
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-sm text-dark-400">
            {isKo ? '총 주 수' : 'Total Weeks'}
          </div>
          <div className="text-2xl font-bold mt-1">{result.total_weeks}</div>
        </div>
        <div>
          <div className="text-sm text-dark-400">
            {isKo 
              ? (result.results.deep_drop ? '깊은 하락 임계값' : '깊은 상승 임계값')
              : (result.results.deep_drop ? 'Deep Drop Threshold' : 'Deep Rise Threshold')}
          </div>
          <div className="text-2xl font-bold mt-1">
            {result.results.deep_drop
              ? (result.filters.deep_drop_threshold * 100).toFixed(1)
              : ((result.filters as any).deep_rise_threshold || 0.05) * 100}%
          </div>
        </div>
        <div>
          <div className="text-sm text-dark-400">
            {isKo ? 'RSI 임계값' : 'RSI Threshold'}
          </div>
          <div className="text-2xl font-bold mt-1">{result.filters.rsi_threshold}</div>
        </div>
        <div>
          <div className="text-sm text-dark-400">
            {isKo ? '코인' : 'Coin'}
          </div>
          <div className="text-2xl font-bold mt-1">{result.coin}</div>
        </div>
      </div>
    </div>
  );
}
