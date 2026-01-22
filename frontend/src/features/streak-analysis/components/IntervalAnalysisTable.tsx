/**
 * 구간별 승률 분석 테이블 컴포넌트
 * RSI 구간별 승률 표
 */
import { Activity } from 'lucide-react';
import type { StreakAnalysisResult } from '../../../types';

interface IntervalAnalysisTableProps {
  result: StreakAnalysisResult;
  isKo: boolean;
}

export default function IntervalAnalysisTable({ result, isKo }: IntervalAnalysisTableProps) {
  const hasRSI = result.rsi_by_interval && Object.keys(result.rsi_by_interval).length > 0;

  if (!hasRSI) {
    return null;
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Activity className="w-5 h-5 text-green-400" />
        {isKo ? '📊 구간별 승률 분석 (95% 신뢰구간)' : '📊 Win Rate by Interval (95% CI)'}
      </h3>
      <p className="text-dark-400 text-sm mb-4">
        {isKo
          ? '전일 RSI 기준, 다음 봉 양봉 확률. ⚠️ 다중비교 보정 적용됨'
          : 'Green candle probability by prev-day RSI. ⚠️ Bonferroni correction applied'}
      </p>

      <div className="grid grid-cols-1 gap-4">
        {/* RSI 구간 */}
        {hasRSI && (
          <div className="bg-dark-800 rounded-xl p-4">
            <div className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
              📈 {isKo ? '전일 RSI 구간' : 'Prev RSI Zone'}
              <span className="text-dark-500 text-xs font-normal">
                ({Object.keys(result.rsi_by_interval!).length}
                {isKo ? '개 구간 테스트' : ' intervals tested'})
              </span>
            </div>
            <div className="space-y-2">
              {Object.entries(result.rsi_by_interval!).map(([interval, data]) => {
                const isHighProb = data.rate >= 60 && data.sample_size >= 3;
                const isStatSig = data.is_significant;
                const isBonfSig = data.bonferroni?.is_significant_after_correction;
                return (
                  <div
                    key={interval}
                    className={`rounded-lg px-3 py-2 ${
                      isHighProb && isBonfSig
                        ? 'bg-emerald-500/20 border border-emerald-500/30'
                        : isHighProb
                          ? 'bg-amber-500/10 border border-amber-500/20'
                          : 'bg-dark-700/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-dark-300 text-sm font-mono">{interval}</span>
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-bold ${
                            isHighProb
                              ? 'text-emerald-400'
                              : data.rate >= 50
                                ? 'text-amber-400'
                                : 'text-rose-400'
                          }`}
                        >
                          {data.rate}%
                        </span>
                        <span className="text-dark-500 text-xs">
                          ({data.sample_size}
                          {isKo ? '건' : ''})
                        </span>
                        {isHighProb && isBonfSig && (
                          <span className="text-emerald-400 text-xs">✓✓</span>
                        )}
                        {isHighProb && isStatSig && !isBonfSig && (
                          <span className="text-amber-400 text-xs">✓</span>
                        )}
                      </div>
                    </div>
                    {/* 신뢰구간 바 */}
                    <div className="mt-1.5 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-dark-600 rounded-full relative">
                        <div
                          className="absolute h-full bg-dark-400 rounded-full"
                          style={{
                            left: `${Math.max(0, data.ci_lower)}%`,
                            width: `${
                              Math.min(100, data.ci_upper) - Math.max(0, data.ci_lower)
                            }%`,
                          }}
                        />
                        <div
                          className="absolute w-1.5 h-1.5 bg-white rounded-full top-0"
                          style={{ left: `${data.rate}%`, transform: 'translateX(-50%)' }}
                        />
                      </div>
                      <span className="text-dark-500 text-xs whitespace-nowrap">
                        [{data.ci_lower}~{data.ci_upper}]
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
            {/* 범례 */}
            <div className="mt-3 pt-3 border-t border-dark-700 flex flex-wrap gap-3 text-xs">
              <span className="text-emerald-400">
                ✓✓ {isKo ? '다중비교 통과' : 'Bonferroni sig'}
              </span>
              <span className="text-amber-400">{isKo ? '단순 유의' : 'Nominal sig'} ✓</span>
            </div>
          </div>
        )}
      </div>

      {/* 통계 해석 안내 */}
      <div className="mt-4 p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl">
        <div className="text-blue-400 font-semibold mb-2">
          📖 {isKo ? '통계 해석 가이드' : 'Statistical Guide'}
        </div>
        <ul className="text-dark-400 text-sm space-y-1">
          <li>
            • <span className="text-emerald-400">✓✓</span>:{' '}
            {isKo
              ? 'Bonferroni 보정 후에도 유의 (다중비교 고려) - 가장 신뢰도 높음'
              : 'Significant after Bonferroni - highest confidence'}
          </li>
          <li>
            • <span className="text-amber-400">✓</span>:{' '}
            {isKo
              ? 'p<0.05 유의하나, 다중비교 보정 미통과 - 참고만'
              : 'p<0.05 but not Bonferroni significant - use with caution'}
          </li>
          <li>
            •{' '}
            {isKo
              ? '샘플 30개 이상일 때 신뢰구간이 가장 안정적'
              : 'CI most stable with 30+ samples'}
          </li>
        </ul>
      </div>
    </div>
  );
}
