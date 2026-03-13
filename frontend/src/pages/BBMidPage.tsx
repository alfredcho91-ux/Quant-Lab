// BB Mid Touch Statistics Page
import { useState } from 'react';
import { runBBMid } from '../api/client';
import { useBacktestParams, useSelectedInterval } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { useAnalysisMutation } from '../hooks/useAnalysisMutation';
import { SkeletonChart, SkeletonTable } from '../components/Skeleton';
import type { BBMidParams } from '../types';
import { getErrorMessage } from '../utils/error';

const ALL_TIMEFRAMES = ['4h', '1d', '3d', '1w', '1M'];  // 4h 1d 3d 주봉 월봉

export default function BBMidPage() {
  const backtestParams = useBacktestParams();
  const selectedInterval = useSelectedInterval();
  const { isKo, selectedCoin } = usePageCommon();

  const [params, setParams] = useState<BBMidParams>({
    coin: selectedCoin,
    intervals: selectedInterval === '1d' ? ['4h', '1d'] : [selectedInterval, '1d'],
    start_side: 'lower',
    max_bars: 7,
    regime: null,
    use_csv: backtestParams.use_csv,
  });

  const { mutation, handleRun: handleRunBase } = useAnalysisMutation({
    mutationFn: runBBMid,
    onSuccess: (data) => {
      console.log('✅ BB Mid 분석 성공:', data);
    },
    onError: (error: unknown) => {
      console.error('❌ BB Mid 분석 실패:', error);
      const msg = getErrorMessage(error) || (isKo ? '알 수 없는 오류' : 'Unknown error');
      alert(isKo ? `분석 실패: ${msg}` : `Analysis failed: ${msg}`);
    },
  });

  const handleRun = () => {
    console.log('🚀 BB Mid 분석 시작, 파라미터:', params);
    if (params.intervals.length === 0) {
      alert(isKo ? '타임프레임을 최소 1개 이상 선택해주세요.' : 'Please select at least one timeframe.');
      return;
    }
    handleRunBase({ ...params } as BBMidParams);
  };

  const result = mutation.data;
  
  // 디버깅용 로그
  console.log('BBMidPage 렌더링:', {
    isPending: mutation.isPending,
    hasError: !!mutation.error,
    hasResult: !!result,
    resultType: typeof result,
    resultKeys: result ? Object.keys(result) : null,
    error: mutation.error,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          📊 {selectedCoin} {isKo ? '볼밴 중단 터치 통계' : 'BB Mid Touch Stats'}
        </h1>
        <p className="text-dark-400 mt-1">
          {isKo
            ? '볼린저밴드 하단/상단 터치 후 중단선 터치 확률'
            : 'BB mid touch probability after lower/upper band touch'}
        </p>
      </div>

      {/* Controls */}
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Side Selection */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '분석 방향' : 'Analysis Side'}
            </label>
            <select
              value={params.start_side}
              onChange={(e) => setParams({ ...params, start_side: e.target.value as 'lower' | 'upper' })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="lower">{isKo ? '볼밴 하단 터치 후' : 'After lower touch'}</option>
              <option value="upper">{isKo ? '볼밴 상단 터치 후' : 'After upper touch'}</option>
            </select>
          </div>

          {/* Max Bars */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? 'N봉' : 'N bars'}
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={params.max_bars}
              onChange={(e) => setParams({ ...params, max_bars: parseInt(e.target.value) || 7 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-dark-400 mb-2">
            {isKo ? '분석 기간 (타임프레임)' : 'Analysis Period (Timeframe)'}
          </label>
          <div className="flex flex-wrap gap-2">
            {ALL_TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => {
                  const intervals = params.intervals.includes(tf)
                    ? params.intervals.filter((t) => t !== tf)
                    : [...params.intervals, tf];
                  setParams({ ...params, intervals });
                }}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  params.intervals.includes(tf)
                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Run Button */}
        <button
          onClick={(e) => {
            e.preventDefault();
            console.log('🔘 버튼 클릭됨, intervals:', params.intervals);
            handleRun();
          }}
          disabled={mutation.isPending || params.intervals.length === 0}
          className="w-full btn-primary py-3 disabled:opacity-50"
        >
          {mutation.isPending ? (isKo ? '계산 중...' : 'Calculating...') : (isKo ? '🚀 통계 계산' : '🚀 Calculate Stats')}
        </button>
      </div>

      {/* Loading Skeleton */}
      {mutation.isPending && (
        <div className="space-y-6">
          <SkeletonChart />
          <SkeletonTable rows={8} cols={5} />
        </div>
      )}

      {/* Error Message */}
      {!mutation.isPending && mutation.error && (
        <div className="card p-6 bg-red-500/10 border border-red-500/30">
          <h3 className="text-lg font-semibold text-red-400 mb-2">
            {isKo ? '❌ 오류 발생' : '❌ Error'}
          </h3>
          <p className="text-red-300 text-sm">
            {isKo 
              ? '통계 계산 중 오류가 발생했습니다. 브라우저 콘솔을 확인해주세요.'
              : 'An error occurred while calculating statistics. Please check the browser console.'}
          </p>
          {mutation.error instanceof Error && (
            <p className="text-red-400 text-xs mt-2 font-mono">
              {mutation.error.message}
            </p>
          )}
        </div>
      )}

      {/* No Data Message - 초기 상태 또는 분석 전 */}
      {!mutation.isPending && !mutation.error && !result && (
        <div className="card p-6 bg-yellow-500/10 border border-yellow-500/30">
          <h3 className="text-lg font-semibold text-yellow-400 mb-2">
            {isKo ? '📊 분석 대기' : '📊 Ready'}
          </h3>
          <p className="text-yellow-300 text-sm">
            {isKo 
              ? '위 파라미터를 선택하고 「통계 계산」 버튼을 눌러주세요.'
              : 'Select parameters and click 「Calculate Stats」.'}
          </p>
        </div>
      )}

      {/* Results */}
      {!mutation.isPending && !mutation.error && result && result.data && Array.isArray(result.data) && (() => {
        const safeResult = result;
        const hasRows = safeResult.data.length > 0;
        return (
        <div className="space-y-6">
          {!hasRows && (
            <div className="card p-6 bg-amber-500/10 border border-amber-500/30">
              <p className="text-amber-300 text-sm">
                {isKo ? '해당 조건에서 이벤트가 없습니다. 타임프레임·분석방향을 변경해보세요.' : 'No events for this condition. Try different timeframe or side.'}
              </p>
            </div>
          )}
          {hasRows && (
          <>
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isKo ? '분석 기간별 중단 터치 성공률' : 'Mid Touch Success Rate by Period'}
            </h3>
            <div className="space-y-4">
              {safeResult.data.map((row) => (
                <div key={row.interval} className="flex items-center gap-4">
                  <span className="w-16 text-sm font-medium text-primary-400">{row.interval}</span>
                  <div className="flex-1 h-8 bg-dark-800 rounded-lg overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary-500 to-primary-400 flex items-center justify-end pr-2"
                      style={{ width: `${row.success_rate ?? 0}%` }}
                    >
                      <span className="text-xs font-bold text-white">
                        {row.success_rate?.toFixed(2) ?? 0}%
                      </span>
                    </div>
                  </div>
                  <span className="text-sm text-dark-400">n={row.events}</span>
                  {row.avg_bars_to_mid != null && (
                    <span className="text-xs text-dark-500">{isKo ? '평균' : 'avg'} {row.avg_bars_to_mid.toFixed(1)}{isKo ? '봉' : ''}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {safeResult.excursions && Object.keys(safeResult.excursions).length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">
                {isKo ? '평균 변동폭 (MFE/MAE)' : 'Average Excursions (MFE/MAE)'}
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-dark-700">
                      <th className="text-left py-2 px-3">{isKo ? '분석 기간' : 'Period'}</th>
                      <th className="text-right py-2 px-3 text-bull">{isKo ? '평균 MFE' : 'Avg MFE'}</th>
                      <th className="text-right py-2 px-3 text-bear">{isKo ? '평균 MAE' : 'Avg MAE'}</th>
                      <th className="text-right py-2 px-3">{isKo ? '평균 마감' : 'Avg End'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(safeResult.excursions).map(([interval, exc]) => (
                      <tr key={interval} className="border-b border-dark-800">
                        <td className="py-2 px-3 font-medium">{interval}</td>
                        <td className="py-2 px-3 text-right text-bull">+{exc.avg_mfe.toFixed(2)}%</td>
                        <td className="py-2 px-3 text-right text-bear">{exc.avg_mae.toFixed(2)}%</td>
                        <td className={`py-2 px-3 text-right ${exc.avg_end >= 0 ? 'text-bull' : 'text-bear'}`}>
                          {exc.avg_end >= 0 ? '+' : ''}{exc.avg_end.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          </>
          )}
        </div>
        );
      })()}
    </div>
  );
}
