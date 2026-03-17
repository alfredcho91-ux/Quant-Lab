import type { StreakAnalysisResult } from '../../../types';

interface ComplexModeSummaryProps {
  result: StreakAnalysisResult;
  isKo: boolean;
}

export default function ComplexModeSummary({ result, isKo }: ComplexModeSummaryProps) {
  if (result.mode !== 'complex') {
    return null;
  }

  return (
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

          {/* 다음 봉(C1) 양봉/음봉 확률 */}
          {result.complex_pattern_analysis?.summary?.c1_analysis && (
            <div className="mt-6 p-6 bg-gradient-to-r from-primary-500/10 via-rose-500/10 to-primary-500/10 border border-dark-700 rounded-xl">
              <h4 className="text-lg font-bold text-white mb-4">
                {isKo ? '다음 봉(C1) 확률 분석' : 'Next Candle (C1) Probability Analysis'}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 양봉 확률 */}
                <div className="bg-primary-500/10 border border-primary-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-dark-300 text-sm">
                      {isKo ? '양봉 확률' : 'Green Candle Probability'}
                    </span>
                    <span className="text-3xl font-bold text-primary-400">
                      {result.complex_pattern_analysis.summary.c1_analysis.green_rate.toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-xs text-dark-500">
                    {isKo
                      ? `케이스: ${result.complex_pattern_analysis.summary.c1_analysis.green_count}/${result.complex_pattern_analysis.summary.c1_analysis.total_count}`
                      : `Cases: ${result.complex_pattern_analysis.summary.c1_analysis.green_count}/${result.complex_pattern_analysis.summary.c1_analysis.total_count}`}
                  </div>
                  {result.complex_pattern_analysis.summary.c1_analysis.green_confidence_interval && (
                    <div className="text-xs text-dark-500 mt-1">
                      {isKo ? '95% 신뢰구간' : '95% CI'}: [
                      {result.complex_pattern_analysis.summary.c1_analysis.green_confidence_interval[0].toFixed(2)}%,
                      {result.complex_pattern_analysis.summary.c1_analysis.green_confidence_interval[1].toFixed(2)}%]
                    </div>
                  )}
                </div>

                {/* 음봉 확률 */}
                <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-dark-300 text-sm">
                      {isKo ? '음봉 확률' : 'Red Candle Probability'}
                    </span>
                    <span className="text-3xl font-bold text-rose-400">
                      {result.complex_pattern_analysis.summary.c1_analysis.red_rate.toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-xs text-dark-500">
                    {isKo
                      ? `케이스: ${result.complex_pattern_analysis.summary.c1_analysis.red_count}/${result.complex_pattern_analysis.summary.c1_analysis.total_count}`
                      : `Cases: ${result.complex_pattern_analysis.summary.c1_analysis.red_count}/${result.complex_pattern_analysis.summary.c1_analysis.total_count}`}
                  </div>
                  {result.complex_pattern_analysis.summary.c1_analysis.red_confidence_interval && (
                    <div className="text-xs text-dark-500 mt-1">
                      {isKo ? '95% 신뢰구간' : '95% CI'}: [
                      {result.complex_pattern_analysis.summary.c1_analysis.red_confidence_interval[0].toFixed(2)}%,
                      {result.complex_pattern_analysis.summary.c1_analysis.red_confidence_interval[1].toFixed(2)}%]
                    </div>
                  )}
                </div>
              </div>

              {/* 평균 수익률 */}
              {result.complex_pattern_analysis.summary.c1_analysis.avg_return !== undefined && (
                <div className="mt-4 pt-4 border-t border-dark-700">
                  <div className="flex items-center justify-between">
                    <span className="text-dark-300 text-sm">
                      {isKo ? '평균 수익률 (C1)' : 'Average Return (C1)'}
                    </span>
                    <span
                      className={`text-xl font-bold ${
                        result.complex_pattern_analysis.summary.c1_analysis.avg_return >= 0
                          ? 'text-primary-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {result.complex_pattern_analysis.summary.c1_analysis.avg_return >= 0 ? '+' : ''}
                      {result.complex_pattern_analysis.summary.c1_analysis.avg_return.toFixed(2)}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
  );
}
