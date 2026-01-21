// Multi-TF Squeeze Direction Study Page
import { useState } from 'react';
import { runMultiTFSqueeze } from '../api/client';
import { useStore } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { useAnalysisMutation } from '../hooks/useAnalysisMutation';
import { SkeletonStats, SkeletonTable } from '../components/Skeleton';
import type { MultiTFSqueezeParams } from '../types';

const TF_ORDER = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '8h', '12h', '1d'];

export default function MultiTFSqueezePage() {
  const { selectedCoin } = useStore();
  const { isKo, tfData } = usePageCommon();

  const timeframes = tfData?.binance?.filter((tf: string) => TF_ORDER.includes(tf)).sort(
    (a: string, b: string) => TF_ORDER.indexOf(a) - TF_ORDER.indexOf(b)
  ) || ['15m', '1h', '2h', '4h'];

  const [params, setParams] = useState<MultiTFSqueezeParams>({
    coin: selectedCoin,
    high_tf: '2h',
    low_tf: '15m',
    squeeze_thr_high: 0.02,
    squeeze_thr_low: 0.02,
    lower_lookback_bars: 2,
    rsi_min: 40,
    rsi_max: 60,
    require_above_mid: true,
  });

  const { mutation, handleRun: handleRunBase } = useAnalysisMutation({
    mutationFn: runMultiTFSqueeze,
  });

  const handleRun = () => {
    handleRunBase({ ...params } as MultiTFSqueezeParams);
  };

  const result = mutation.data;

  // Filter lower TF candidates
  const highTfIndex = TF_ORDER.indexOf(params.high_tf);
  const lowTfCandidates = timeframes.filter((tf: string) => TF_ORDER.indexOf(tf) < highTfIndex);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          📐 {isKo ? '멀티 TF 볼밴 스퀴즈 방향 연구' : 'Multi-TF BB Squeeze Direction Study'}
        </h1>
        <p className="text-dark-400 mt-1">
          {isKo
            ? `${selectedCoin}/USDT 상위 TF 스퀴즈 이후 위/아래 방향 확률 분석`
            : `Analyze ${selectedCoin}/USDT breakout direction after higher TF squeeze`}
        </p>
      </div>

      {/* Controls */}
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {/* High TF */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '상위 타임프레임' : 'Higher TF'}
            </label>
            <select
              value={params.high_tf}
              onChange={(e) => setParams({ ...params, high_tf: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              {timeframes.map((tf: string) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>

          {/* Low TF */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '하위 타임프레임' : 'Lower TF'}
            </label>
            <select
              value={params.low_tf}
              onChange={(e) => setParams({ ...params, low_tf: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
              disabled={lowTfCandidates.length === 0}
            >
              {lowTfCandidates.map((tf: string) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>

          {/* Lower Lookback Bars */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '하위TF 최근 N봉' : 'Lower TF N bars'}
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={params.lower_lookback_bars}
              onChange={(e) => setParams({ ...params, lower_lookback_bars: parseInt(e.target.value) || 2 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* High TF Squeeze Threshold */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '상위TF 스퀴즈 폭 ≤' : 'High TF squeeze ≤'}
            </label>
            <input
              type="number"
              step={0.005}
              min={0.005}
              max={0.05}
              value={params.squeeze_thr_high}
              onChange={(e) => setParams({ ...params, squeeze_thr_high: parseFloat(e.target.value) || 0.02 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Low TF Squeeze Threshold */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '하위TF 스퀴즈 폭 ≤' : 'Low TF squeeze ≤'}
            </label>
            <input
              type="number"
              step={0.005}
              min={0.005}
              max={0.05}
              value={params.squeeze_thr_low}
              onChange={(e) => setParams({ ...params, squeeze_thr_low: parseFloat(e.target.value) || 0.02 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* RSI Range */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '하위TF RSI 범위' : 'Lower TF RSI'}
            </label>
            <div className="flex gap-1">
              <input
                type="number"
                min={0}
                max={100}
                value={params.rsi_min}
                onChange={(e) => setParams({ ...params, rsi_min: parseInt(e.target.value) || 0 })}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
                placeholder="Min"
              />
              <input
                type="number"
                min={0}
                max={100}
                value={params.rsi_max}
                onChange={(e) => setParams({ ...params, rsi_max: parseInt(e.target.value) || 100 })}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
                placeholder="Max"
              />
            </div>
          </div>

          {/* Above Mid */}
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={params.require_above_mid}
                onChange={(e) => setParams({ ...params, require_above_mid: e.target.checked })}
                className="w-4 h-4 rounded border-dark-600 bg-dark-700 text-emerald-500"
              />
              <span className="text-sm text-dark-300">
                {isKo ? '중단선 위 필수' : 'Above mid band'}
              </span>
            </label>
          </div>
        </div>

        {/* Run Button */}
        <button
          onClick={handleRun}
          disabled={mutation.isPending}
          className="w-full btn-primary py-3 disabled:opacity-50"
        >
          {mutation.isPending
            ? (isKo ? '분석 중...' : 'Analyzing...')
            : (isKo ? '🚀 스퀴즈 방향 통계 계산' : '🚀 Run Squeeze Analysis')}
        </button>
      </div>

      {/* Loading Skeleton */}
      {mutation.isPending && (
        <div className="space-y-6">
          <SkeletonStats />
          <SkeletonTable rows={10} cols={4} />
        </div>
      )}

      {/* Results */}
      {!mutation.isPending && result && (
        <div className="space-y-6">
          {/* Stats Overview */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">📊 {isKo ? '이벤트 수' : 'Event Counts'}</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-dark-800 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-white">{result.stats.total_events}</div>
                <div className="text-sm text-dark-400">{isKo ? '전체 이벤트' : 'Total Events'}</div>
              </div>
              <div className="bg-dark-800 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-emerald-400">{result.stats.filtered_events}</div>
                <div className="text-sm text-dark-400">{isKo ? '필터 통과' : 'Filtered'}</div>
              </div>
              <div className="bg-dark-800 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-bull">{result.stats.n_up || 0}</div>
                <div className="text-sm text-dark-400">↑ Up</div>
              </div>
              <div className="bg-dark-800 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-bear">{result.stats.n_down || 0}</div>
                <div className="text-sm text-dark-400">↓ Down</div>
              </div>
            </div>
          </div>

          {/* Direction Probabilities */}
          {result.stats.filtered_events > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">🎯 {isKo ? '방향 확률' : 'Direction Probabilities'}</h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                {/* Up Probability */}
                <div className="text-center">
                  <div className="text-4xl font-bold text-bull mb-2">
                    {result.stats.p_up?.toFixed(1)}%
                  </div>
                  <div className="text-dark-400 mb-2">↑ {isKo ? '상승 확률' : 'Up Probability'}</div>
                  {result.stats.avg_ret_up !== null && result.stats.avg_ret_up !== undefined && (
                    <div className="text-sm text-dark-500">
                      {isKo ? '평균 수익률' : 'Avg Return'}: 
                      <span className="text-bull ml-1">+{result.stats.avg_ret_up.toFixed(3)}%</span>
                    </div>
                  )}
                </div>

                {/* Down Probability */}
                <div className="text-center">
                  <div className="text-4xl font-bold text-bear mb-2">
                    {result.stats.p_down?.toFixed(1)}%
                  </div>
                  <div className="text-dark-400 mb-2">↓ {isKo ? '하락 확률' : 'Down Probability'}</div>
                  {result.stats.avg_ret_down !== null && result.stats.avg_ret_down !== undefined && (
                    <div className="text-sm text-dark-500">
                      {isKo ? '평균 수익률' : 'Avg Return'}: 
                      <span className="text-bear ml-1">{result.stats.avg_ret_down.toFixed(3)}%</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Visual Bar */}
              <div className="mt-6">
                <div className="flex h-10 rounded-lg overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-green-400 flex items-center justify-center transition-all"
                    style={{ width: `${result.stats.p_up || 0}%` }}
                  >
                    <span className="text-sm font-bold text-white">
                      ↑ {result.stats.p_up?.toFixed(0)}%
                    </span>
                  </div>
                  <div
                    className="bg-gradient-to-r from-red-500 to-orange-400 flex items-center justify-center transition-all"
                    style={{ width: `${result.stats.p_down || 0}%` }}
                  >
                    <span className="text-sm font-bold text-white">
                      ↓ {result.stats.p_down?.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Sample Events */}
          {result.events.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">📜 {isKo ? '샘플 데이터' : 'Sample Data'}</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-dark-700">
                      <th className="text-left py-2 px-3">{isKo ? '시간' : 'Time'}</th>
                      <th className="text-center py-2 px-3">{isKo ? '방향' : 'Direction'}</th>
                      <th className="text-right py-2 px-3">{isKo ? '수익률' : 'Return'}</th>
                      <th className="text-right py-2 px-3">RSI</th>
                      <th className="text-center py-2 px-3">{isKo ? '중단선 위' : 'Above Mid'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.events.slice(0, 20).map((ev, idx) => (
                      <tr key={idx} className="border-b border-dark-800 hover:bg-dark-800/50">
                        <td className="py-2 px-3 font-mono text-xs">{ev.break_time}</td>
                        <td className="py-2 px-3 text-center">
                          <span className={ev.direction === 'up' ? 'text-bull' : 'text-bear'}>
                            {ev.direction === 'up' ? '↑ Up' : '↓ Down'}
                          </span>
                        </td>
                        <td className={`py-2 px-3 text-right ${ev.immediate_ret >= 0 ? 'text-bull' : 'text-bear'}`}>
                          {ev.immediate_ret >= 0 ? '+' : ''}{ev.immediate_ret.toFixed(2)}%
                        </td>
                        <td className="py-2 px-3 text-right">{ev.lt_rsi_last.toFixed(1)}</td>
                        <td className="py-2 px-3 text-center">
                          {ev.lt_above_mid ? '✓' : '✗'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {result.events.length > 20 && (
                <p className="text-dark-500 text-sm mt-2 text-center">
                  {isKo ? `... ${result.events.length - 20}개 더` : `... ${result.events.length - 20} more`}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

