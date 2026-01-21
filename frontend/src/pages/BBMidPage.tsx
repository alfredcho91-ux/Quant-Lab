// BB Mid Touch Statistics Page
import { useState } from 'react';
import { runBBMid } from '../api/client';
import { useStore } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { useAnalysisMutation } from '../hooks/useAnalysisMutation';
import { SkeletonChart, SkeletonTable } from '../components/Skeleton';
import type { BBMidParams } from '../types';

const ALL_TIMEFRAMES = ['15m', '30m', '1h', '2h', '4h', '8h', '12h', '1d', '3d', '1w'];

export default function BBMidPage() {
  const { backtestParams } = useStore();
  const { isKo, selectedCoin } = usePageCommon();

  const [params, setParams] = useState<BBMidParams>({
    coin: selectedCoin,
    intervals: ['1h', '4h'],
    start_side: 'lower',
    max_bars: 7,
    rsi_min: 0,
    rsi_max: 100,
    regime: null, // 레짐 필터 비활성화 (null = 무시)
    use_csv: backtestParams.use_csv, // 전역 설정 사용
  });

  const { mutation, handleRun: handleRunBase } = useAnalysisMutation({
    mutationFn: runBBMid,
  });

  const handleRun = () => {
    handleRunBase({ ...params } as BBMidParams);
  };

  const result = mutation.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          📊 {selectedCoin} {isKo ? '볼밴 중단 터치 통계' : 'BB Mid Touch Stats'}
        </h1>
        <p className="text-dark-400 mt-1">
          {isKo
            ? '볼린저밴드 하단/상단 터치 후 중단선 터치 확률 분석'
            : 'Probability of touching mid band after touching lower/upper band'}
        </p>
      </div>

      {/* Controls */}
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
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

          {/* RSI Range */}
          <div className="col-span-2">
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? 'RSI 필터' : 'RSI Filter'}: {params.rsi_min} - {params.rsi_max}
            </label>
            <div className="flex gap-2">
              <input
                type="range"
                min={0}
                max={100}
                value={params.rsi_min}
                onChange={(e) => setParams({ ...params, rsi_min: parseInt(e.target.value) })}
                className="flex-1"
              />
              <input
                type="range"
                min={0}
                max={100}
                value={params.rsi_max}
                onChange={(e) => setParams({ ...params, rsi_max: parseInt(e.target.value) })}
                className="flex-1"
              />
            </div>
          </div>
        </div>

        {/* Timeframe Selection */}
        <div>
          <label className="block text-sm text-dark-400 mb-2">
            {isKo ? '타임프레임 선택' : 'Select Timeframes'}
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
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
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
          onClick={handleRun}
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

      {/* Results */}
      {!mutation.isPending && result && (
        <div className="space-y-6">
          {/* Success Rate Chart */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isKo ? '타임프레임별 중단 터치 성공률' : 'Mid Touch Success Rate by TF'}
            </h3>
            <div className="space-y-3">
              {result.data.map((row) => (
                <div key={row.interval} className="flex items-center gap-4">
                  <span className="w-16 text-sm text-dark-300">{row.interval}</span>
                  <div className="flex-1 h-8 bg-dark-800 rounded-lg overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500 to-green-400 flex items-center justify-end pr-2"
                      style={{ width: `${row.success_rate || 0}%` }}
                    >
                      <span className="text-xs font-bold text-white">
                        {row.success_rate?.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <span className="text-sm text-dark-400">
                    n={row.events}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Excursion Stats */}
          {Object.keys(result.excursions).length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">
                {isKo ? '평균 변동폭 (MFE/MAE)' : 'Average Excursions (MFE/MAE)'}
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-dark-700">
                      <th className="text-left py-2 px-3">TF</th>
                      <th className="text-right py-2 px-3 text-bull">{isKo ? '평균 MFE' : 'Avg MFE'}</th>
                      <th className="text-right py-2 px-3 text-bear">{isKo ? '평균 MAE' : 'Avg MAE'}</th>
                      <th className="text-right py-2 px-3">{isKo ? '평균 마감' : 'Avg End'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(result.excursions).map(([tf, exc]) => (
                      <tr key={tf} className="border-b border-dark-800">
                        <td className="py-2 px-3 font-medium">{tf}</td>
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

          {/* Raw Data Table */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isKo ? '상세 결과' : 'Detailed Results'}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-dark-700">
                    <th className="text-left py-2 px-3">TF</th>
                    <th className="text-right py-2 px-3">{isKo ? '이벤트 수' : 'Events'}</th>
                    <th className="text-right py-2 px-3">{isKo ? '성공' : 'Success'}</th>
                    <th className="text-right py-2 px-3">{isKo ? '성공률' : 'Rate'}</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.map((row) => (
                    <tr key={row.interval} className="border-b border-dark-800">
                      <td className="py-2 px-3 font-medium">{row.interval}</td>
                      <td className="py-2 px-3 text-right">{row.events}</td>
                      <td className="py-2 px-3 text-right">{row.success}</td>
                      <td className="py-2 px-3 text-right text-emerald-400">
                        {row.success_rate?.toFixed(1) || '-'}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

