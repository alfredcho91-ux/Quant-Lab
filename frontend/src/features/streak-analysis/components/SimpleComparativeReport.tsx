import { ArrowRight, FileText } from 'lucide-react';
import type { StreakAnalysisResult } from '../../../types';

interface SimpleComparativeReportProps {
  result: StreakAnalysisResult;
  direction: 'green' | 'red';
  isKo: boolean;
}

export default function SimpleComparativeReport({ result, direction, isKo }: SimpleComparativeReportProps) {
  if (!result.comparative_report || result.comparative_report.pattern_total <= 0) {
    return null;
  }

  return (
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
                <div key={i} className="w-3 h-7 bg-primary-500 rounded-sm" />
              ))}
              {result.n_streak > 6 && <span className="text-dark-500 text-xs">...</span>}
            </div>
            <div className="w-3 h-7 bg-rose-500 rounded-sm" />
            <ArrowRight className="w-4 h-4 text-dark-500" />
            <div className="w-4 h-8 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-sm animate-pulse" />
            <span className="text-dark-400 text-sm ml-2">{isKo ? '= 양봉/음봉?' : '= Green/Red?'}</span>
          </>
        ) : (
          <>
            <div className="flex gap-0.5">
              {Array.from({ length: Math.min(result.n_streak, 6) }).map((_, i) => (
                <div key={i} className="w-3 h-7 bg-rose-500 rounded-sm" />
              ))}
              {result.n_streak > 6 && <span className="text-dark-500 text-xs">...</span>}
            </div>
            <div className="w-3 h-7 bg-primary-500 rounded-sm" />
            <ArrowRight className="w-4 h-4 text-dark-500" />
            <div className="w-4 h-8 bg-gradient-to-t from-rose-500 to-rose-400 rounded-sm animate-pulse" />
            <span className="text-dark-400 text-sm ml-2">{isKo ? '= 음봉/양봉?' : '= Red/Green?'}</span>
          </>
        )}
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-dark-800 rounded-lg p-3 text-center">
          <div className="text-dark-400 text-xs mb-1">{isKo ? '총 패턴' : 'Total'}</div>
          <div className="text-white font-bold text-lg">{result.comparative_report.pattern_total}</div>
        </div>
        <div
          className={`${
            direction === 'green' ? 'bg-primary-500/10 border border-primary-500/20' : 'bg-rose-500/10 border border-rose-500/20'
          } rounded-lg p-3 text-center`}
        >
          <div className={`${direction === 'green' ? 'text-primary-400' : 'text-rose-400'} text-xs mb-1`}>
            {isKo ? (direction === 'green' ? '양봉' : '음봉') : direction === 'green' ? 'Green' : 'Red'}
          </div>
          <div className={`${direction === 'green' ? 'text-primary-400' : 'text-rose-400'} font-bold text-lg`}>
            {result.comparative_report.success_count}
          </div>
        </div>
        <div
          className={`${
            direction === 'green' ? 'bg-rose-500/10 border border-rose-500/20' : 'bg-primary-500/10 border border-primary-500/20'
          } rounded-lg p-3 text-center`}
        >
          <div className={`${direction === 'green' ? 'text-rose-400' : 'text-primary-400'} text-xs mb-1`}>
            {isKo ? (direction === 'green' ? '음봉' : '양봉') : direction === 'green' ? 'Red' : 'Green'}
          </div>
          <div className={`${direction === 'green' ? 'text-rose-400' : 'text-primary-400'} font-bold text-lg`}>
            {result.comparative_report.failure_count}
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left py-3 px-4 text-dark-400">{isKo ? '지표 (전일 기준)' : 'Metric (Prev Day)'}</th>
              <th className={`text-right py-3 px-4 ${direction === 'green' ? 'text-primary-400' : 'text-rose-400'}`}>
                {direction === 'green' ? (isKo ? '양봉 케이스' : 'Green Cases') : isKo ? '음봉 케이스' : 'Red Cases'}
              </th>
              <th className={`text-right py-3 px-4 ${direction === 'green' ? 'text-rose-400' : 'text-primary-400'}`}>
                {direction === 'green' ? (isKo ? '음봉 케이스' : 'Red Cases') : isKo ? '양봉 케이스' : 'Green Cases'}
              </th>
              <th className="text-right py-3 px-4 text-cyan-400">{isKo ? '차이' : 'Diff'}</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-dark-800 hover:bg-dark-800/50">
              <td className="py-3 px-4 text-dark-300">{isKo ? '전일 RSI' : 'Prev RSI'}</td>
              <td className={`py-3 px-4 text-right ${direction === 'green' ? 'text-primary-400' : 'text-rose-400'} font-mono`}>
                {result.comparative_report.success.prev_rsi?.toFixed(2) ?? '-'}
              </td>
              <td className={`py-3 px-4 text-right ${direction === 'green' ? 'text-rose-400' : 'text-primary-400'} font-mono`}>
                {result.comparative_report.failure.prev_rsi?.toFixed(2) ?? '-'}
              </td>
              <td className="py-3 px-4 text-right text-cyan-400 font-mono">
                {result.comparative_report.success.prev_rsi != null && result.comparative_report.failure.prev_rsi != null
                  ? (result.comparative_report.success.prev_rsi - result.comparative_report.failure.prev_rsi).toFixed(2)
                  : '-'}
              </td>
            </tr>
            <tr className="border-b border-dark-800 hover:bg-dark-800/50">
              <td className="py-3 px-4 text-dark-300">{isKo ? '전일 몸통(%)' : 'Prev Body %'}</td>
              <td className={`py-3 px-4 text-right ${direction === 'green' ? 'text-primary-400' : 'text-rose-400'} font-mono`}>
                {result.comparative_report.success.prev_body_pct?.toFixed(2) ?? '-'}%
              </td>
              <td className={`py-3 px-4 text-right ${direction === 'green' ? 'text-rose-400' : 'text-primary-400'} font-mono`}>
                {result.comparative_report.failure.prev_body_pct?.toFixed(2) ?? '-'}%
              </td>
              <td className="py-3 px-4 text-right text-cyan-400 font-mono">
                {result.comparative_report.success.prev_body_pct != null &&
                result.comparative_report.failure.prev_body_pct != null
                  ? (result.comparative_report.success.prev_body_pct - result.comparative_report.failure.prev_body_pct).toFixed(2)
                  : '-'}
              </td>
            </tr>
            <tr className="border-b border-dark-800 hover:bg-dark-800/50">
              <td className="py-3 px-4 text-dark-300">{isKo ? '전일 거래량 변화(%)' : 'Prev Vol Change %'}</td>
              <td className={`py-3 px-4 text-right ${direction === 'green' ? 'text-primary-400' : 'text-rose-400'} font-mono`}>
                {result.comparative_report.success.prev_vol_change?.toFixed(2) ?? '-'}%
              </td>
              <td className={`py-3 px-4 text-right ${direction === 'green' ? 'text-rose-400' : 'text-primary-400'} font-mono`}>
                {result.comparative_report.failure.prev_vol_change?.toFixed(2) ?? '-'}%
              </td>
              <td className="py-3 px-4 text-right text-cyan-400 font-mono">
                {result.comparative_report.success.prev_vol_change != null &&
                result.comparative_report.failure.prev_vol_change != null
                  ? (
                      result.comparative_report.success.prev_vol_change - result.comparative_report.failure.prev_vol_change
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
            {direction === 'green' ? (isKo ? '양봉 확률' : 'Green Probability') : isKo ? '음봉 확률' : 'Red Probability'}
          </span>
          <span className="text-2xl font-bold text-cyan-400">{result.comparative_report.success_rate?.toFixed(2) ?? '-'}%</span>
        </div>
      </div>
    </div>
  );
}

