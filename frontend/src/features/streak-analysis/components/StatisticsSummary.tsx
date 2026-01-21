/**
 * 통계 요약 컴포넌트
 * 총 케이스, 지속 확률, 신뢰구간, C1 Stats, Short Signal, Complex Results 포함
 */
import { TrendingUp, TrendingDown, AlertTriangle, ArrowRight, FileText } from 'lucide-react';
import type { StreakAnalysisResult } from '../../../types';

interface StatisticsSummaryProps {
  result: StreakAnalysisResult;
  direction: 'green' | 'red';
  isKo: boolean;
}

export default function StatisticsSummary({ result, direction, isKo }: StatisticsSummaryProps) {
  const moveLabel = direction === 'green' ? (isKo ? '상승' : 'Up') : (isKo ? '하락' : 'Down');

  return (
    <div className="space-y-6">
      {/* Simple Mode Results */}
      {(result.mode === 'simple' || (!result.mode && result.total_cases > 0)) && (
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
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
                <div className="text-dark-400 text-sm mb-1">
                  {isKo ? '지속 확률' : 'Continuation Rate'}
                </div>
                <div className="text-2xl font-bold text-emerald-400">
                  {result.continuation_rate?.toFixed(2) || 0}%
                </div>
              </div>
              {result.continuation_ci && (
                <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-4">
                  <div className="text-dark-400 text-sm mb-1">
                    {isKo ? '신뢰구간 (95%)' : 'Confidence Interval'}
                  </div>
                  <div className="text-lg font-bold text-cyan-400">
                    [{result.continuation_ci.ci_lower}% ~ {result.continuation_ci.ci_upper}%]
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
                    ? 'bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20'
                    : 'bg-gradient-to-br from-rose-500/10 to-red-500/5 border-rose-500/20'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-dark-300">
                    {isKo ? `${moveLabel} 지속` : `${moveLabel} Continue`}
                  </span>
                  {direction === 'green' ? (
                    <TrendingUp className="w-6 h-6 text-emerald-400" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-rose-400" />
                  )}
                </div>
                <div
                  className={`text-4xl font-bold ${direction === 'green' ? 'text-emerald-400' : 'text-rose-400'}`}
                >
                  {result.continuation_rate?.toFixed(2) || 0}%
                </div>
                {/* 신뢰구간 표시 */}
                {result.continuation_ci && (
                  <div className="mt-2 space-y-1">
                    <div className="text-xs text-dark-400">
                      95% CI: [{result.continuation_ci.ci_lower}% ~ {result.continuation_ci.ci_upper}%]
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          result.continuation_ci.reliability === 'high'
                            ? 'bg-emerald-500/20 text-emerald-400'
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
                    <div className={`text-lg font-bold ${direction === 'green' ? 'text-emerald-400' : 'text-rose-400'}`}>
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
                    <div key={i} className="w-3 h-7 bg-emerald-500 rounded-sm" />
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
                  <div className="text-xl font-bold text-emerald-400">
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

          {/* Comparative Report */}
          {result.comparative_report && result.comparative_report.pattern_total > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                {result.direction === 'green'
                  ? isKo
                    ? `📋 ${result.n_streak}G + 1R 패턴 비교 분석`
                    : `📋 ${result.n_streak}G + 1R Pattern Analysis`
                  : isKo
                    ? `📋 ${result.n_streak}R + 1G 패턴 비교 분석`
                    : `📋 ${result.n_streak}R + 1G Pattern Analysis`}
              </h3>
              <p className="text-dark-400 text-sm mb-4">
                {result.direction === 'green'
                  ? isKo
                    ? `${result.n_streak}연속 양봉 + 1음봉 이후, 다음 봉(${result.n_streak + 2}일차) 결과에 따른 전일 지표 비교`
                    : `Comparing prev-day metrics based on day ${result.n_streak + 2} result after ${result.n_streak}G + 1R pattern`
                  : isKo
                    ? `${result.n_streak}연속 음봉 + 1양봉 이후, 다음 봉(${result.n_streak + 2}일차) 결과에 따른 전일 지표 비교`
                    : `Comparing prev-day metrics based on day ${result.n_streak + 2} result after ${result.n_streak}R + 1G pattern`}
              </p>

              {/* Pattern Visual */}
              <div className="flex items-center gap-2 mb-4 p-3 bg-dark-800 rounded-lg">
                {result.direction === 'green' ? (
                  <>
                    <div className="flex gap-0.5">
                      {Array.from({ length: Math.min(result.n_streak, 6) }).map((_, i) => (
                        <div key={i} className="w-3 h-7 bg-emerald-500 rounded-sm" />
                      ))}
                      {result.n_streak > 6 && <span className="text-dark-500 text-xs">...</span>}
                    </div>
                    <div className="w-3 h-7 bg-rose-500 rounded-sm" />
                    <ArrowRight className="w-4 h-4 text-dark-500" />
                    <div className="w-4 h-8 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-sm animate-pulse" />
                    <span className="text-dark-400 text-sm ml-2">
                      {isKo ? '= 양봉/음봉?' : '= Green/Red?'}
                    </span>
                  </>
                ) : (
                  <>
                    <div className="flex gap-0.5">
                      {Array.from({ length: Math.min(result.n_streak, 6) }).map((_, i) => (
                        <div key={i} className="w-3 h-7 bg-rose-500 rounded-sm" />
                      ))}
                      {result.n_streak > 6 && <span className="text-dark-500 text-xs">...</span>}
                    </div>
                    <div className="w-3 h-7 bg-emerald-500 rounded-sm" />
                    <ArrowRight className="w-4 h-4 text-dark-500" />
                    <div className="w-4 h-8 bg-gradient-to-t from-rose-500 to-rose-400 rounded-sm animate-pulse" />
                    <span className="text-dark-400 text-sm ml-2">
                      {isKo ? '= 음봉/양봉?' : '= Red/Green?'}
                    </span>
                  </>
                )}
              </div>

              {/* Stats Summary */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-dark-800 rounded-lg p-3 text-center">
                  <div className="text-dark-400 text-xs mb-1">{isKo ? '총 패턴' : 'Total'}</div>
                  <div className="text-white font-bold text-lg">
                    {result.comparative_report.pattern_total}
                  </div>
                </div>
                <div
                  className={`${
                    result.direction === 'green'
                      ? 'bg-emerald-500/10 border border-emerald-500/20'
                      : 'bg-rose-500/10 border border-rose-500/20'
                  } rounded-lg p-3 text-center`}
                >
                  <div
                    className={`${
                      result.direction === 'green' ? 'text-emerald-400' : 'text-rose-400'
                    } text-xs mb-1`}
                  >
                    {isKo
                      ? result.direction === 'green'
                        ? '양봉'
                        : '음봉'
                      : result.direction === 'green'
                        ? 'Green'
                        : 'Red'}
                  </div>
                  <div
                    className={`${
                      result.direction === 'green' ? 'text-emerald-400' : 'text-rose-400'
                    } font-bold text-lg`}
                  >
                    {result.comparative_report.success_count}
                  </div>
                </div>
                <div
                  className={`${
                    result.direction === 'green'
                      ? 'bg-rose-500/10 border border-rose-500/20'
                      : 'bg-emerald-500/10 border border-emerald-500/20'
                  } rounded-lg p-3 text-center`}
                >
                  <div
                    className={`${
                      result.direction === 'green' ? 'text-rose-400' : 'text-emerald-400'
                    } text-xs mb-1`}
                  >
                    {isKo
                      ? result.direction === 'green'
                        ? '음봉'
                        : '양봉'
                      : result.direction === 'green'
                        ? 'Red'
                        : 'Green'}
                  </div>
                  <div
                    className={`${
                      result.direction === 'green' ? 'text-rose-400' : 'text-emerald-400'
                    } font-bold text-lg`}
                  >
                    {result.comparative_report.failure_count}
                  </div>
                </div>
              </div>

              {/* Comparison Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-dark-700">
                      <th className="text-left py-3 px-4 text-dark-400">
                        {isKo ? '지표 (전일 기준)' : 'Metric (Prev Day)'}
                      </th>
                      <th
                        className={`text-right py-3 px-4 ${
                          result.direction === 'green' ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {result.direction === 'green'
                          ? isKo
                            ? '양봉 케이스'
                            : 'Green Cases'
                          : isKo
                            ? '음봉 케이스'
                            : 'Red Cases'}
                      </th>
                      <th
                        className={`text-right py-3 px-4 ${
                          result.direction === 'green' ? 'text-rose-400' : 'text-emerald-400'
                        }`}
                      >
                        {result.direction === 'green'
                          ? isKo
                            ? '음봉 케이스'
                            : 'Red Cases'
                          : isKo
                            ? '양봉 케이스'
                            : 'Green Cases'}
                      </th>
                      <th className="text-right py-3 px-4 text-cyan-400">
                        {isKo ? '차이' : 'Diff'}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-dark-800 hover:bg-dark-800/50">
                      <td className="py-3 px-4 text-dark-300">{isKo ? '전일 RSI' : 'Prev RSI'}</td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-emerald-400' : 'text-rose-400'
                        } font-mono`}
                      >
                        {result.comparative_report.success.prev_rsi?.toFixed(2) ?? '-'}
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-rose-400' : 'text-emerald-400'
                        } font-mono`}
                      >
                        {result.comparative_report.failure.prev_rsi?.toFixed(2) ?? '-'}
                      </td>
                      <td className="py-3 px-4 text-right text-cyan-400 font-mono">
                        {result.comparative_report.success.prev_rsi &&
                        result.comparative_report.failure.prev_rsi
                          ? (
                              result.comparative_report.success.prev_rsi -
                              result.comparative_report.failure.prev_rsi
                            ).toFixed(2)
                          : '-'}
                      </td>
                    </tr>
                    <tr className="border-b border-dark-800 hover:bg-dark-800/50">
                      <td className="py-3 px-4 text-dark-300">
                        {isKo ? '전일 몸통(%)' : 'Prev Body %'}
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-emerald-400' : 'text-rose-400'
                        } font-mono`}
                      >
                        {result.comparative_report.success.prev_body_pct?.toFixed(2) ?? '-'}%
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-rose-400' : 'text-emerald-400'
                        } font-mono`}
                      >
                        {result.comparative_report.failure.prev_body_pct?.toFixed(2) ?? '-'}%
                      </td>
                      <td className="py-3 px-4 text-right text-cyan-400 font-mono">
                        {result.comparative_report.success.prev_body_pct &&
                        result.comparative_report.failure.prev_body_pct
                          ? (
                              result.comparative_report.success.prev_body_pct -
                              result.comparative_report.failure.prev_body_pct
                            ).toFixed(2)
                          : '-'}
                      </td>
                    </tr>
                    <tr className="border-b border-dark-800 hover:bg-dark-800/50">
                      <td className="py-3 px-4 text-dark-300">
                        {isKo ? '전일 거래량 변화(%)' : 'Prev Vol Change %'}
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-emerald-400' : 'text-rose-400'
                        } font-mono`}
                      >
                        {result.comparative_report.success.prev_vol_change?.toFixed(2) ?? '-'}%
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-rose-400' : 'text-emerald-400'
                        } font-mono`}
                      >
                        {result.comparative_report.failure.prev_vol_change?.toFixed(2) ?? '-'}%
                      </td>
                      <td className="py-3 px-4 text-right text-cyan-400 font-mono">
                        {result.comparative_report.success.prev_vol_change &&
                        result.comparative_report.failure.prev_vol_change
                          ? (
                              result.comparative_report.success.prev_vol_change -
                              result.comparative_report.failure.prev_vol_change
                            ).toFixed(2)
                          : '-'}
                      </td>
                    </tr>
                    <tr className="hover:bg-dark-800/50">
                      <td className="py-3 px-4 text-dark-300">
                        {isKo ? '전일 이격도(%)' : 'Prev Disparity %'}
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-emerald-400' : 'text-rose-400'
                        } font-mono`}
                      >
                        {result.comparative_report.success.prev_disparity?.toFixed(2) ?? '-'}%
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          result.direction === 'green' ? 'text-rose-400' : 'text-emerald-400'
                        } font-mono`}
                      >
                        {result.comparative_report.failure.prev_disparity?.toFixed(2) ?? '-'}%
                      </td>
                      <td className="py-3 px-4 text-right text-cyan-400 font-mono">
                        {result.comparative_report.success.prev_disparity &&
                        result.comparative_report.failure.prev_disparity
                          ? (
                              result.comparative_report.success.prev_disparity -
                              result.comparative_report.failure.prev_disparity
                            ).toFixed(2)
                          : '-'}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Success Rate */}
              <div className="mt-4 p-4 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-xl">
                <div className="flex items-center justify-between">
                  <span className="text-dark-300">
                    {result.direction === 'green'
                      ? isKo
                        ? '양봉 확률'
                        : 'Green Probability'
                      : isKo
                        ? '음봉 확률'
                        : 'Red Probability'}
                  </span>
                  <span className="text-2xl font-bold text-cyan-400">
                    {result.comparative_report.success_rate?.toFixed(2) ?? '-'}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Complex Mode Results */}
      {result.mode === 'complex' && (
        <div className="card p-6">
          <h3 className="text-xl font-bold text-white mb-2">
            {isKo ? '복합 패턴 분석 결과' : 'Complex Pattern Analysis Results'}
          </h3>
          {result.analysis_mode?.parameters?.complex_pattern && (
            <p className="text-dark-400 mb-4">
              {isKo ? '패턴' : 'Pattern'}: {result.analysis_mode.parameters.complex_pattern.join(', ')}
            </p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-dark-800 rounded-lg p-4">
              <div className="text-dark-400 text-sm mb-1">
                {isKo ? '필터 적용 후 케이스' : 'Filtered Cases'}
              </div>
              <div className="text-2xl font-bold text-white">
                {result.total_cases}
                {isKo ? '회' : ''}
              </div>
            </div>
            {result.complex_pattern_analysis && (
              <>
                <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-4">
                  <div className="text-dark-400 text-sm mb-1">{isKo ? '평균 스코어' : 'Avg Score'}</div>
                  <div className="text-2xl font-bold text-cyan-400">
                    {result.complex_pattern_analysis.avg_score || 0}/100
                  </div>
                </div>
                <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
                  <div className="text-dark-400 text-sm mb-1">
                    {isKo ? '고신뢰도 비율' : 'High Confidence'}
                  </div>
                  <div className="text-2xl font-bold text-purple-400">
                    {result.complex_pattern_analysis.high_confidence_count
                      ? ((result.complex_pattern_analysis.high_confidence_count / result.total_cases) *
                          100
                        ).toFixed(1)
                      : 0}
                    %
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
