// 주간 패턴 분석 - 필터 결과 컴포넌트

import { CheckCircle2 } from 'lucide-react';
import type { WeeklyPatternResult } from '../../types';

interface FilterResultsProps {
  result: WeeklyPatternResult;
  isKo: boolean;
}

export function FilterResults({ result, isKo }: FilterResultsProps) {
  const stats = result.results.deep_drop || result.results.deep_rise;
  if (!stats) return null;

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`text-lg ${result.results.deep_drop ? 'text-red-400' : 'text-emerald-400'}`}>
            {result.results.deep_drop ? '📉' : '📈'}
          </span>
          <h3 className="text-lg font-semibold">
            {stats.title}
          </h3>
        </div>
        {(stats.profit_factor && stats.profit_factor > 1) && (
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
        )}
      </div>
      <p className="text-sm text-dark-400 mb-4">
        {stats.description}
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-xs text-dark-400 mb-1">
            {isKo ? '샘플 수' : 'Samples'}
          </div>
          <div className="text-xl font-bold">
            {stats.sample_count || 0}
          </div>
        </div>
        <div>
          <div className="text-xs text-dark-400 mb-1">
            {isKo 
              ? (result.results.deep_drop ? '반등 확률' : '지속 확률')
              : (result.results.deep_drop ? 'Rebound Rate' : 'Continuation Rate')}
          </div>
          <div className={`text-xl font-bold ${
            ((stats.expected_return || 0) > 0 
              ? 'text-emerald-400' 
              : 'text-red-400')
          }`}>
            {stats.win_rate !== null
              ? `${(stats.win_rate || 0).toFixed(2)}%`
              : 'N/A'}
          </div>
        </div>
        <div>
          <div className="text-xs text-dark-400 mb-1">
            {isKo ? '기대 수익률' : 'Expected Return'}
          </div>
          <div className={`text-xl font-bold ${
            ((stats.expected_return || 0) > 0 
              ? 'text-emerald-400' 
              : 'text-red-400')
          }`}>
            {stats.expected_return !== null
              ? `${(stats.expected_return || 0) >= 0 ? '+' : ''}${(stats.expected_return || 0).toFixed(2)}%`
              : 'N/A'}
          </div>
        </div>
        <div>
          <div className="text-xs text-dark-400 mb-1">
            {isKo ? 'Profit Factor' : 'Profit Factor'}
          </div>
          <div className={`text-xl font-bold ${
            ((stats.profit_factor || 0) > 1 
              ? 'text-emerald-400' 
              : 'text-red-400')
          }`}>
            {stats.profit_factor !== null
              ? (stats.profit_factor === Infinity
                ? '∞'
                : (stats.profit_factor || 0).toFixed(2))
              : 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
}
