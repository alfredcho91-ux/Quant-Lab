// Real-time Pattern Scanner Page
import { useState } from 'react';
import { runPatternScanner } from '../api/client';
import { useBacktestParams, useUpdateBacktestParams } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { useAnalysisMutation } from '../hooks/useAnalysisMutation';
import type { PatternScanParams, PatternStat } from '../types';

const PATTERN_NAMES_KO: Record<string, string> = {
  'Bullish Engulfing': '강세 장악형 (Bull Engulf)',
  'Bearish Engulfing': '약세 장악형 (Bear Engulf)',
  'Hammer': '망치형 (Hammer)',
  'Shooting Star': '슈팅 스타',
  'Doji': '도지 (십자형)',
};

export default function PatternScannerPage() {
  const backtestParams = useBacktestParams();
  const updateBacktestParams = useUpdateBacktestParams();
  const { isKo, selectedCoin, availableTfs } = usePageCommon();

  const [params, setParams] = useState<PatternScanParams>({
    coin: selectedCoin,
    intervals: ['1h', '4h'],
    tp_pct: backtestParams.tp_pct || 1.0, // 전역 설정 사용
    horizon: 3,
    mode: 'natural',
    position: 'long',
    use_csv: backtestParams.use_csv, // 전역 설정 사용
  });

  const { mutation, handleRun: handleRunBase } = useAnalysisMutation({
    mutationFn: runPatternScanner,
  });

  const handleRun = () => {
    handleRunBase({ ...params } as PatternScanParams);
  };

  const result = mutation.data;

  const getPatternName = (key: string) => {
    if (isKo) return PATTERN_NAMES_KO[key] || key;
    return key;
  };

  const renderPatternCell = (stat: PatternStat | undefined) => {
    if (!stat || stat.signals === 0 || stat.hit_rate === null) {
      return <span className="text-dark-600">—</span>;
    }

    const dirIcon = stat.direction === 'bull' ? '🟢' : stat.direction === 'bear' ? '🔴' : '🟡';
    const statusIcon = stat.last_on ? dirIcon : '○';

    return (
      <span className={stat.last_on ? (stat.direction === 'bull' ? 'text-bull' : 'text-bear') : 'text-dark-300'}>
        {statusIcon} {stat.hit_rate.toFixed(1)}% (n={stat.signals})
      </span>
    );
  };

  // Organize patterns by direction
  const bullPatterns = ['Bullish Engulfing', 'Hammer'];
  const bearPatterns = ['Bearish Engulfing', 'Shooting Star'];
  const neutralPatterns = ['Doji'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          🔍 {isKo ? '실시간 패턴 스캐너 + TP 확률' : 'Live Pattern Scanner + TP Stats'}
        </h1>
        <p className="text-dark-400 mt-1">
          {isKo
            ? `${selectedCoin}/USDT 주요 캔들 패턴 발생 여부와 TP 도달 확률`
            : `Scan ${selectedCoin}/USDT for candle patterns and TP hit probability`}
        </p>
      </div>

      {/* Controls */}
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {/* Mode Selection */}
          <div className="col-span-2">
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '승률 기준' : 'Mode'}
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setParams({ ...params, mode: 'natural' })}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  params.mode === 'natural'
                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                {isKo ? '패턴 방향 기준' : 'Pattern Direction'}
              </button>
              <button
                onClick={() => setParams({ ...params, mode: 'position' })}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  params.mode === 'position'
                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                {isKo ? '내 포지션 기준' : 'My Position'}
              </button>
            </div>
          </div>

          {/* Position (only when mode = position) */}
          {params.mode === 'position' && (
            <div>
              <label className="block text-sm text-dark-400 mb-1">
                {isKo ? '포지션' : 'Position'}
              </label>
              <select
                value={params.position}
                onChange={(e) => setParams({ ...params, position: e.target.value as 'long' | 'short' })}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
              >
                <option value="long">Long</option>
                <option value="short">Short</option>
              </select>
            </div>
          )}

          {/* TP */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? 'TP 목표 (%)' : 'TP Target (%)'}
            </label>
            <input
              type="number"
              step={0.1}
              min={0.1}
              max={10}
              value={params.tp_pct}
              onChange={(e) => {
                const newTp = parseFloat(e.target.value) || 1;
                setParams({ ...params, tp_pct: newTp });
                updateBacktestParams({ tp_pct: newTp }); // 전역 설정 동기화
              }}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Horizon */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '보는 기간 (봉)' : 'Look-ahead (bars)'}
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={params.horizon}
              onChange={(e) => setParams({ ...params, horizon: parseInt(e.target.value) || 3 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* Timeframe Selection */}
        <div>
          <label className="block text-sm text-dark-400 mb-2">
            {isKo ? '스캔할 타임프레임' : 'Timeframes to Scan'}
          </label>
          <div className="flex flex-wrap gap-2">
            {availableTfs.map((tf: string) => (
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
          onClick={handleRun}
          disabled={mutation.isPending || params.intervals.length === 0}
          className="w-full btn-primary py-3 disabled:opacity-50"
        >
          {mutation.isPending
            ? (isKo ? '스캔 중...' : 'Scanning...')
            : (isKo ? '🔍 스캔 & 통계 계산' : '🔍 Scan & Analyze')}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Legend */}
          <div className="card p-4">
            <p className="text-sm text-dark-400">
              {isKo ? (
                <>
                  🟢 강세 패턴 / 🔴 약세 패턴 / 
                  ● 현재 패턴 발생 / ○ 패턴 없음
                </>
              ) : (
                <>
                  🟢 Bullish / 🔴 Bearish / 
                  ● Pattern present / ○ No pattern
                </>
              )}
            </p>
          </div>

          {/* Bullish Patterns Table */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              🟢 {isKo ? '강세 패턴' : 'Bullish Patterns'}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-dark-700">
                    <th className="text-left py-2 px-3">TF</th>
                    {bullPatterns.map((p) => (
                      <th key={p} className="text-center py-2 px-3">{getPatternName(p)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {params.intervals.map((tf) => (
                    <tr key={tf} className="border-b border-dark-800 hover:bg-dark-800/50">
                      <td className="py-2 px-3 font-medium">{tf}</td>
                      {bullPatterns.map((p) => (
                        <td key={p} className="py-2 px-3 text-center">
                          {renderPatternCell(result.data[tf]?.[p])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Bearish Patterns Table */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              🔴 {isKo ? '약세 패턴' : 'Bearish Patterns'}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-dark-700">
                    <th className="text-left py-2 px-3">TF</th>
                    {bearPatterns.map((p) => (
                      <th key={p} className="text-center py-2 px-3">{getPatternName(p)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {params.intervals.map((tf) => (
                    <tr key={tf} className="border-b border-dark-800 hover:bg-dark-800/50">
                      <td className="py-2 px-3 font-medium">{tf}</td>
                      {bearPatterns.map((p) => (
                        <td key={p} className="py-2 px-3 text-center">
                          {renderPatternCell(result.data[tf]?.[p])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Neutral Patterns Table */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              🟡 {isKo ? '중립 패턴' : 'Neutral Patterns'}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-dark-700">
                    <th className="text-left py-2 px-3">TF</th>
                    {neutralPatterns.map((p) => (
                      <th key={p} className="text-center py-2 px-3">{getPatternName(p)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {params.intervals.map((tf) => (
                    <tr key={tf} className="border-b border-dark-800 hover:bg-dark-800/50">
                      <td className="py-2 px-3 font-medium">{tf}</td>
                      {neutralPatterns.map((p) => (
                        <td key={p} className="py-2 px-3 text-center">
                          {renderPatternCell(result.data[tf]?.[p])}
                        </td>
                      ))}
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
