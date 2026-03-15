import { TrendingUp, TrendingDown, AlertTriangle, ArrowRight } from 'lucide-react';
import type { StreakAnalysisResult } from '../../../types';
import SimpleComparativeReport from './SimpleComparativeReport';

interface SimpleModeSummaryProps {
  result: StreakAnalysisResult;
  direction: 'green' | 'red';
  isKo: boolean;
}

export default function SimpleModeSummary({ result, direction, isKo }: SimpleModeSummaryProps) {
  const moveLabel = direction === 'green' ? (isKo ? '상승' : 'Up') : (isKo ? '하락' : 'Down');

  return (
      (result.mode === 'simple' || (!result.mode && result.total_cases > 0)) && (
        <>
          <div className="card p-6">
            <h3 className="text-xl font-bold text-white mb-2">
              {isKo ? 'N연속 분석 결과' : 'N-Streak Analysis Results'}
            </h3>
            <p className="text-dark-400 mb-4">
              {result.n_streak}
              {isKo ? '연속' : ' consecutive'}{' '}
              {result.direction === 'green' ? (isKo ? '양봉' : 'Green') : (isKo ? '음봉' : 'Red')}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-dark-800 rounded-lg p-4">
                <div className="text-dark-400 text-sm mb-1">{isKo ? '총 케이스' : 'Total Cases'}</div>
                <div className="text-2xl font-bold text-white">
                  {result.total_cases}
                  {isKo ? '회' : ''}
                </div>
              </div>
              <div className="bg-primary-500/10 border border-primary-500/20 rounded-lg p-4">
                <div className="text-dark-400 text-sm mb-1">
                  {isKo ? '지속 확률' : 'Continuation Rate'}
                </div>
                <div className="text-2xl font-bold text-primary-400">
                  {result.continuation_rate?.toFixed(2) || 0}%
                </div>
              </div>
              {result.continuation_ci && (
                <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-4">
                  <div className="text-dark-400 text-sm mb-1">
                    {isKo ? '신뢰구간 (95%)' : 'Confidence Interval'}
                  </div>
                  <div className="text-lg font-bold text-cyan-400">
                    [{result.continuation_ci.ci_lower.toFixed(2)}% ~ {result.continuation_ci.ci_upper.toFixed(2)}%]
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* C1 Stats */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              📍 {isKo ? `첫 번째 봉 (C₁ = n+1번째)` : `First Bar (C₁)`}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                className={`rounded-xl p-6 border ${
                  direction === 'green'
                    ? 'bg-gradient-to-br from-primary-500/10 to-primary-500/5 border-primary-500/20'
                    : 'bg-gradient-to-br from-rose-500/10 to-red-500/5 border-rose-500/20'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-dark-300">
                    {isKo ? `${moveLabel} 지속` : `${moveLabel} Continue`}
                  </span>
                  {direction === 'green' ? (
                    <TrendingUp className="w-6 h-6 text-primary-400" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-rose-400" />
                  )}
                </div>
                <div
                  className={`text-4xl font-bold ${direction === 'green' ? 'text-primary-400' : 'text-rose-400'}`}
                >
                  {result.continuation_rate?.toFixed(2) || 0}%
                </div>
                {/* 신뢰구간 표시 */}
                {result.continuation_ci && (
                  <div className="mt-2 space-y-1">
                    <div className="text-xs text-dark-400">
                      95% CI: [{result.continuation_ci.ci_lower.toFixed(2)}% ~ {result.continuation_ci.ci_upper.toFixed(2)}%]
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          result.continuation_ci.reliability === 'high'
                            ? 'bg-primary-500/20 text-primary-400'
                            : result.continuation_ci.reliability === 'medium'
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-rose-500/20 text-rose-400'
                        }`}
                      >
                        {result.continuation_ci.reliability === 'high'
                          ? isKo
                            ? '높은 신뢰도'
                            : 'High'
                          : result.continuation_ci.reliability === 'medium'
                            ? isKo
                              ? '중간 신뢰도'
                              : 'Medium'
                            : isKo
                              ? '낮은 신뢰도'
                              : 'Low'}
                      </span>
                      {result.c1_is_significant && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400">
                          p&lt;0.05 ✓
                        </span>
                      )}
                    </div>
                  </div>
                )}
                <div className="text-sm text-dark-500 mt-2">
                  {result.continuation_count}
                  {isKo ? '회' : ''}
                </div>
                {/* 평균 상승/하락폭 표시 */}
                {result.continuation_stats && result.continuation_stats.avg_body_pct !== null && (
                  <div className="mt-3 pt-3 border-t border-dark-700">
                    <div className="text-xs text-dark-400 mb-1">
                      {isKo ? '평균 변동폭' : 'Avg Movement'}
                    </div>
                    <div className={`text-lg font-bold ${direction === 'green' ? 'text-primary-400' : 'text-rose-400'}`}>
                      {direction === 'green' ? '+' : '-'}
                      {Math.abs(result.continuation_stats.avg_body_pct).toFixed(2)}%
                    </div>
                    {result.continuation_stats.max_body_pct !== null &&
                      result.continuation_stats.min_body_pct !== null && (
                        <div className="text-xs text-dark-500 mt-1">
                          {isKo ? '범위' : 'Range'}: {Math.abs(result.continuation_stats.min_body_pct).toFixed(2)}% ~{' '}
                          {Math.abs(result.continuation_stats.max_body_pct).toFixed(2)}%
                        </div>
                      )}
                  </div>
                )}
              </div>
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border border-purple-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-dark-300">{isKo ? '반전' : 'Reversal'}</span>
                  <AlertTriangle className="w-6 h-6 text-purple-400" />
                </div>
                <div className="text-4xl font-bold text-purple-400">
                  {result.reversal_rate?.toFixed(2) || 0}%
                </div>
                <div className="text-sm text-dark-500 mt-2">
                  {result.reversal_count}
                  {isKo ? '회' : ''}
                </div>
                {/* 평균 상승/하락폭 표시 */}
                {result.reversal_stats && result.reversal_stats.avg_body_pct !== null && (
                  <div className="mt-3 pt-3 border-t border-dark-700">
                    <div className="text-xs text-dark-400 mb-1">
                      {isKo ? '평균 변동폭' : 'Avg Movement'}
                    </div>
                    <div className="text-lg font-bold text-purple-400">
                      {direction === 'green' ? '-' : '+'}
                      {Math.abs(result.reversal_stats.avg_body_pct).toFixed(2)}%
                    </div>
                    {result.reversal_stats.max_body_pct !== null &&
                      result.reversal_stats.min_body_pct !== null && (
                        <div className="text-xs text-dark-500 mt-1">
                          {isKo ? '범위' : 'Range'}: {Math.abs(result.reversal_stats.min_body_pct).toFixed(2)}% ~{' '}
                          {Math.abs(result.reversal_stats.max_body_pct).toFixed(2)}%
                        </div>
                      )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Short Signal */}
          {result.short_signal && direction === 'green' && !result.complex_pattern_analysis && (
            <div
              className={`card p-6 border-2 ${
                result.short_signal.enabled
                  ? 'border-rose-500/50 bg-gradient-to-br from-rose-500/10 to-red-500/5'
                  : 'border-dark-700'
              }`}
            >
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-rose-400" />
                {isKo
                  ? `📉 숏 시그널 (${result.n_streak}연속 양봉 + RSI ${result.short_signal.rsi_threshold}+)`
                  : `📉 Short Signal`}
                {result.short_signal.enabled && (
                  <span className="ml-2 px-2 py-0.5 bg-rose-500 text-white text-xs font-bold rounded">
                    {isKo ? '활성화' : 'ACTIVE'}
                  </span>
                )}
              </h3>
              <p className="text-dark-400 text-sm mb-4">
                {isKo
                  ? `${result.n_streak}연속 양봉 후 RSI가 ${result.short_signal.rsi_threshold} 이상일 때 역추세 숏 전략`
                  : `Counter-trend short after ${result.n_streak}-streak with RSI >= ${result.short_signal.rsi_threshold}`}
              </p>

              {/* 패턴 시각화 */}
              <div className="flex items-center gap-2 mb-4 p-3 bg-dark-800 rounded-lg">
                <div className="flex gap-0.5">
                  {Array.from({ length: Math.min(result.n_streak, 6) }).map((_, i) => (
                    <div key={i} className="w-3 h-7 bg-primary-500 rounded-sm" />
                  ))}
                </div>
                <span className="text-amber-400 text-xs font-bold">
                  RSI≥{result.short_signal.rsi_threshold}
                </span>
                <ArrowRight className="w-4 h-4 text-dark-500" />
                <div className="w-4 h-8 bg-rose-500 rounded-sm animate-pulse" />
                <span className="text-rose-400 text-sm font-bold">{isKo ? '숏' : 'SHORT'}</span>
              </div>

              {/* 승률 & 타점 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div
                  className={`rounded-xl p-4 text-center ${
                    result.short_signal.win_rate >= 60
                      ? 'bg-rose-500/20 border border-rose-500/30'
                      : 'bg-dark-800'
                  }`}
                >
                  <div className="text-dark-400 text-xs mb-1">{isKo ? '숏 승률' : 'Win Rate'}</div>
                  <div
                    className={`text-2xl font-bold ${result.short_signal.win_rate >= 60 ? 'text-rose-400' : 'text-dark-300'}`}
                  >
                    {result.short_signal.win_rate}%
                  </div>
                  <div className="text-dark-500 text-xs mt-1">
                    {result.short_signal.win_count}/{result.short_signal.total_cases}
                  </div>
                </div>
                <div className="bg-dark-800 rounded-xl p-4 text-center">
                  <div className="text-dark-400 text-xs mb-1">{isKo ? '진입가' : 'Entry'}</div>
                  <div className="text-xl font-bold text-amber-400">
                    +{result.short_signal.entry_rise_pct ?? '-'}%
                  </div>
                  <div className="text-dark-500 text-xs mt-1">{isKo ? '시가 대비' : 'from Open'}</div>
                </div>
                <div className="bg-dark-800 rounded-xl p-4 text-center">
                  <div className="text-dark-400 text-xs mb-1">{isKo ? '익절 목표' : 'Take Profit'}</div>
                  <div className="text-xl font-bold text-primary-400">
                    +{result.short_signal.take_profit_pct ?? '-'}%
                  </div>
                  <div className="text-dark-500 text-xs mt-1">{isKo ? '평균 수익' : 'Avg Profit'}</div>
                </div>
                <div className="bg-dark-800 rounded-xl p-4 text-center">
                  <div className="text-dark-400 text-xs mb-1">{isKo ? '손절' : 'Stop Loss'}</div>
                  <div className="text-xl font-bold text-rose-400">
                    +{result.short_signal.stop_loss_pct}%
                  </div>
                  <div className="text-dark-500 text-xs mt-1">
                    {isKo ? '진입가 대비' : 'from Entry'}
                  </div>
                </div>
              </div>

              {/* 시그널 메시지 */}
              {result.short_signal.enabled ? (
                <div className="mt-4 p-4 bg-rose-500/20 border border-rose-500/30 rounded-xl">
                  <div className="text-rose-400 font-bold mb-1">
                    🔥 {isKo ? '숏 시그널 활성화!' : 'SHORT SIGNAL ACTIVE!'}
                  </div>
                  <div className="text-dark-300 text-sm">
                    {isKo
                      ? `시가 대비 +${result.short_signal.entry_rise_pct}% 위꼬리 저항에서 숏 진입 고려`
                      : `Consider short entry at +${result.short_signal.entry_rise_pct}% resistance`}
                  </div>
                </div>
              ) : (
                <div className="mt-4 p-3 bg-dark-800 rounded-lg text-dark-500 text-sm text-center">
                  {isKo ? '승률 60% 미만 - 시그널 비활성화' : 'Win rate < 60% - Signal inactive'}
                </div>
              )}
            </div>
          )}

          <SimpleComparativeReport result={result} direction={direction} isKo={isKo} />
        </>
      )
  );
}
