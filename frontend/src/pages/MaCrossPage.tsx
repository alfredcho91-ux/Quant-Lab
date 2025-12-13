// MA Cross Statistics Page
import { useState, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, RefreshCw, BarChart3, Grid3X3 } from 'lucide-react';
import { useStore } from '../store/useStore';
import { getLabels } from '../store/labels';
import { runMaCross } from '../api/client';
import type { MaCrossParams, MaCrossStat, MaCrossResult } from '../types';

const DEFAULT_PAIRS = [
  [5, 20],
  [5, 60],
  [20, 60],
  [20, 240],
  [60, 240],
];

const PAIR_LABELS = DEFAULT_PAIRS.map(([s, l]) => `${s}/${l}`);

export default function MaCrossPage() {
  const { language, selectedCoin } = useStore();
  const labels = getLabels(language);
  
  // State
  const [interval, setInterval] = useState('1h');
  const [crossType, setCrossType] = useState<'golden' | 'dead'>('golden');
  const [selectedPairs, setSelectedPairs] = useState<number[][]>(DEFAULT_PAIRS);
  const [maxHorizon, setMaxHorizon] = useState(5);
  const [upThresholds, setUpThresholds] = useState('0.5, 1, 2');
  const [downThresholds, setDownThresholds] = useState('0.5, 1, 2');
  const [useCsv, setUseCsv] = useState(false);
  const [result, setResult] = useState<MaCrossResult | null>(null);
  const [selectedHorizon, setSelectedHorizon] = useState(3);
  const [activeTab, setActiveTab] = useState<'chart' | 'heatmap' | 'data'>('chart');

  // Parse threshold strings
  const parseThresholds = (str: string): number[] => {
    return str.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
  };

  // Mutation for running MA cross analysis
  const mutation = useMutation({
    mutationFn: (params: MaCrossParams) => runMaCross(params),
    onSuccess: (data) => {
      setResult(data);
      if (data && data.horizons.length > 0) {
        setSelectedHorizon(Math.min(3, Math.max(...data.horizons)));
      }
    },
  });

  const handleRun = () => {
    const params: MaCrossParams = {
      coin: selectedCoin,
      interval,
      cross_type: crossType,
      pairs: selectedPairs,
      horizons: Array.from({ length: maxHorizon }, (_, i) => i + 1),
      up_thresholds: parseThresholds(upThresholds),
      down_thresholds: parseThresholds(downThresholds),
      use_csv: useCsv,
    };
    mutation.mutate(params);
  };

  const togglePair = (pairStr: string) => {
    const [s, l] = pairStr.split('/').map(Number);
    const exists = selectedPairs.some(([a, b]) => a === s && b === l);
    if (exists) {
      setSelectedPairs(selectedPairs.filter(([a, b]) => !(a === s && b === l)));
    } else {
      setSelectedPairs([...selectedPairs, [s, l]]);
    }
  };

  // Filter data for current view
  const primaryType = crossType === 'golden' ? 'up' : 'down';
  
  const filteredData = useMemo(() => {
    if (!result?.data) return [];
    return result.data.filter(
      (d) => d.type === primaryType && d.horizon === selectedHorizon
    );
  }, [result, primaryType, selectedHorizon]);

  // Heatmap data
  const heatmapData = useMemo(() => {
    if (!result?.data) return { pairs: [] as string[], horizons: [] as number[], matrix: {} as Record<string, Record<number, number>> };
    
    const uniqueThresholds = parseThresholds(primaryType === 'up' ? upThresholds : downThresholds);
    const targetThreshold = uniqueThresholds[0] / 100; // First threshold
    
    const pairs = [...new Set(result.data.map(d => d.pair))].sort();
    const horizons = result.horizons;
    
    const matrix: Record<string, Record<number, number>> = {};
    pairs.forEach(pair => {
      matrix[pair] = {};
      horizons.forEach(h => {
        const item = result.data.find(
          d => d.pair === pair && d.horizon === h && d.type === primaryType && 
               Math.abs(d.threshold_value - targetThreshold) < 0.0001
        );
        matrix[pair][h] = item?.probability ?? 0;
      });
    });
    
    return { pairs, horizons, matrix };
  }, [result, primaryType, upThresholds, downThresholds]);

  // Find best performer
  const bestStat = useMemo(() => {
    if (filteredData.length === 0) return null;
    return filteredData.reduce((best, curr) => 
      curr.probability > best.probability ? curr : best
    );
  }, [filteredData]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            {crossType === 'golden' ? (
              <TrendingUp className="w-6 h-6 text-bull" />
            ) : (
              <TrendingDown className="w-6 h-6 text-bear" />
            )}
            {language === 'ko' 
              ? `${selectedCoin} 이평선 크로스 통계` 
              : `${selectedCoin} MA Cross Statistics`}
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {language === 'ko'
              ? '골든/데드 크로스 이후 수익률 도달 확률을 분석합니다.'
              : 'Analyze probability of reaching targets after golden/dead crosses.'}
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="card p-4 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {/* Cross Type */}
          <div>
            <label className="text-xs text-dark-400 uppercase block mb-2">
              {language === 'ko' ? '크로스 종류' : 'Cross Type'}
            </label>
            <div className="flex gap-1">
              <button
                onClick={() => setCrossType('golden')}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                  crossType === 'golden'
                    ? 'bg-bull/20 text-bull border border-bull/30'
                    : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
                }`}
              >
                {language === 'ko' ? '골든' : 'Golden'}
              </button>
              <button
                onClick={() => setCrossType('dead')}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                  crossType === 'dead'
                    ? 'bg-bear/20 text-bear border border-bear/30'
                    : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
                }`}
              >
                {language === 'ko' ? '데드' : 'Dead'}
              </button>
            </div>
          </div>

          {/* Timeframe */}
          <div>
            <label className="text-xs text-dark-400 uppercase block mb-2">
              {labels.interval}
            </label>
            <select
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              className="w-full bg-dark-800"
            >
              {['15m', '30m', '1h', '2h', '4h', '1d'].map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>

          {/* Max Horizon */}
          <div>
            <label className="text-xs text-dark-400 uppercase block mb-2">
              {language === 'ko' ? '최대 기간 (봉)' : 'Max Horizon (bars)'}
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={maxHorizon}
              onChange={(e) => setMaxHorizon(Number(e.target.value))}
              className="w-full bg-dark-800"
            />
          </div>

          {/* Data Source */}
          <div>
            <label className="text-xs text-dark-400 uppercase block mb-2">
              {labels.data_src}
            </label>
            <div className="flex gap-1">
              <button
                onClick={() => setUseCsv(false)}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                  !useCsv
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
                }`}
              >
                API
              </button>
              <button
                onClick={() => setUseCsv(true)}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                  useCsv
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
                }`}
              >
                CSV
              </button>
            </div>
          </div>

          {/* Up Thresholds */}
          <div>
            <label className="text-xs text-dark-400 uppercase block mb-2">
              {language === 'ko' ? '상승 기준 (%)' : 'Up Targets (%)'}
            </label>
            <input
              type="text"
              value={upThresholds}
              onChange={(e) => setUpThresholds(e.target.value)}
              placeholder="0.5, 1, 2"
              className="w-full bg-dark-800"
            />
          </div>

          {/* Down Thresholds */}
          <div>
            <label className="text-xs text-dark-400 uppercase block mb-2">
              {language === 'ko' ? '하락 기준 (%)' : 'Down Targets (%)'}
            </label>
            <input
              type="text"
              value={downThresholds}
              onChange={(e) => setDownThresholds(e.target.value)}
              placeholder="0.5, 1, 2"
              className="w-full bg-dark-800"
            />
          </div>
        </div>

        {/* MA Pairs */}
        <div>
          <label className="text-xs text-dark-400 uppercase block mb-2">
            {language === 'ko' ? '이평 조합 선택' : 'Select MA Pairs'}
          </label>
          <div className="flex flex-wrap gap-2">
            {PAIR_LABELS.map((label) => {
              const [s, l] = label.split('/').map(Number);
              const isSelected = selectedPairs.some(([a, b]) => a === s && b === l);
              return (
                <button
                  key={label}
                  onClick={() => togglePair(label)}
                  className={`py-1.5 px-3 rounded-lg text-sm font-medium transition-all ${
                    isSelected
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Run Button */}
        <div className="flex justify-end">
          <button
            onClick={handleRun}
            disabled={mutation.isPending || selectedPairs.length === 0}
            className="btn btn-primary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${mutation.isPending ? 'animate-spin' : ''}`} />
            {language === 'ko' ? '분석 실행' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && result.data.length > 0 && (
        <>
          {/* Tabs */}
          <div className="flex gap-2 border-b border-dark-700">
            <button
              onClick={() => setActiveTab('chart')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'chart'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-dark-400 hover:text-dark-200'
              }`}
            >
              <BarChart3 className="w-4 h-4 inline mr-2" />
              {language === 'ko' ? '조합별 그래프' : 'By MA Pair'}
            </button>
            <button
              onClick={() => setActiveTab('heatmap')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'heatmap'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-dark-400 hover:text-dark-200'
              }`}
            >
              <Grid3X3 className="w-4 h-4 inline mr-2" />
              {language === 'ko' ? '히트맵' : 'Heatmap'}
            </button>
            <button
              onClick={() => setActiveTab('data')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'data'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-dark-400 hover:text-dark-200'
              }`}
            >
              {language === 'ko' ? '상세 데이터' : 'Detailed Data'}
            </button>
          </div>

          {/* Chart Tab */}
          {activeTab === 'chart' && (
            <div className="card p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  {language === 'ko' 
                    ? (primaryType === 'up' ? '조합별 상승 도달 확률' : '조합별 하락 도달 확률')
                    : (primaryType === 'up' ? 'Up Target Hit Rate by Pair' : 'Down Target Hit Rate by Pair')}
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-dark-400">
                    {language === 'ko' ? '보는 기간:' : 'Horizon:'}
                  </span>
                  <select
                    value={selectedHorizon}
                    onChange={(e) => setSelectedHorizon(Number(e.target.value))}
                    className="bg-dark-800 text-sm"
                  >
                    {result.horizons.map((h) => (
                      <option key={h} value={h}>{h} {language === 'ko' ? '봉' : 'bars'}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Bar Chart */}
              <div className="space-y-2">
                {filteredData.length > 0 ? (
                  <>
                    {/* Group by pair */}
                    {[...new Set(filteredData.map(d => d.pair))].sort().map((pair) => {
                      const pairData = filteredData.filter(d => d.pair === pair);
                      return (
                        <div key={pair} className="flex items-center gap-4">
                          <span className="w-16 text-sm font-mono text-dark-300">{pair}</span>
                          <div className="flex-1 flex gap-1">
                            {pairData.map((stat, idx) => (
                              <div
                                key={idx}
                                className="relative flex-1 bg-dark-800 rounded overflow-hidden h-8"
                                title={`${stat.threshold_label}: ${stat.probability.toFixed(1)}%`}
                              >
                                <div
                                  className={`absolute inset-y-0 left-0 ${
                                    primaryType === 'up' ? 'bg-bull/40' : 'bg-bear/40'
                                  }`}
                                  style={{ width: `${Math.min(100, stat.probability)}%` }}
                                />
                                <div className="relative flex items-center justify-between px-2 h-full">
                                  <span className="text-xs text-dark-400">{stat.threshold_label}</span>
                                  <span className="text-xs font-mono font-medium">
                                    {stat.probability.toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                          <span className="w-16 text-xs text-dark-500 text-right">
                            n={pairData[0]?.signals || 0}
                          </span>
                        </div>
                      );
                    })}
                    
                    {/* Best performer */}
                    {bestStat && (
                      <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                        <span className="text-emerald-400 text-sm">
                          ✅ {language === 'ko' ? '최고 도달 비율' : 'Best hit rate'}: {' '}
                          <span className="font-mono font-bold">{bestStat.pair}</span> / {selectedHorizon}
                          {language === 'ko' ? '봉' : ' bars'} / {bestStat.threshold_label} →{' '}
                          <span className="font-bold">{bestStat.probability.toFixed(1)}%</span>
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-dark-400 text-center py-8">
                    {language === 'ko' ? '데이터가 없습니다.' : 'No data available.'}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Heatmap Tab */}
          {activeTab === 'heatmap' && (
            <div className="card p-4">
              <h3 className="text-lg font-semibold mb-4">
                {language === 'ko' 
                  ? `히트맵: Horizon × MA 조합 (${primaryType === 'up' ? '상승' : '하락'} 기준)`
                  : `Heatmap: Horizon × MA Pair (${primaryType === 'up' ? 'Up' : 'Down'} targets)`}
              </h3>
              
              {heatmapData.pairs.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr>
                        <th className="px-3 py-2 text-left text-xs text-dark-400">
                          {language === 'ko' ? '이평 조합' : 'MA Pair'}
                        </th>
                        {heatmapData.horizons.map((h) => (
                          <th key={h} className="px-3 py-2 text-center text-xs text-dark-400">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {heatmapData.pairs.map((pair) => (
                        <tr key={pair}>
                          <td className="px-3 py-2 font-mono text-dark-300">{pair}</td>
                          {heatmapData.horizons.map((h) => {
                            const value = heatmapData.matrix[pair]?.[h] ?? 0;
                            const intensity = Math.min(100, value) / 100;
                            const bgColor = primaryType === 'up' 
                              ? `rgba(16, 185, 129, ${intensity * 0.5})` 
                              : `rgba(239, 68, 68, ${intensity * 0.5})`;
                            return (
                              <td
                                key={h}
                                className="px-3 py-2 text-center font-mono text-sm"
                                style={{ backgroundColor: bgColor }}
                              >
                                {value.toFixed(1)}%
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-dark-400 text-center py-8">
                  {language === 'ko' ? '데이터가 없습니다.' : 'No data available.'}
                </p>
              )}
            </div>
          )}

          {/* Data Tab */}
          {activeTab === 'data' && (
            <div className="card">
              <div className="p-4 border-b border-dark-700">
                <h3 className="text-lg font-semibold">
                  {language === 'ko' ? '상세 통계 데이터' : 'Detailed Statistics'}
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-dark-800/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs text-dark-400 uppercase">
                        {language === 'ko' ? '이평 조합' : 'Pair'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs text-dark-400 uppercase">
                        {language === 'ko' ? '기간' : 'Horizon'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs text-dark-400 uppercase">
                        {language === 'ko' ? '유형' : 'Type'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs text-dark-400 uppercase">
                        {language === 'ko' ? '기준' : 'Target'}
                      </th>
                      <th className="px-4 py-3 text-right text-xs text-dark-400 uppercase">
                        {language === 'ko' ? '확률' : 'Probability'}
                      </th>
                      <th className="px-4 py-3 text-right text-xs text-dark-400 uppercase">
                        {language === 'ko' ? '신호 수' : 'Signals'}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-700">
                    {result.data
                      .sort((a, b) => {
                        if (a.pair !== b.pair) return a.pair.localeCompare(b.pair);
                        if (a.horizon !== b.horizon) return a.horizon - b.horizon;
                        if (a.type !== b.type) return a.type.localeCompare(b.type);
                        return a.threshold_value - b.threshold_value;
                      })
                      .map((stat, idx) => (
                        <tr key={idx} className="hover:bg-dark-700/30">
                          <td className="px-4 py-2 font-mono">{stat.pair}</td>
                          <td className="px-4 py-2 text-center">{stat.horizon}</td>
                          <td className={`px-4 py-2 text-center ${
                            stat.type === 'up' ? 'text-bull' : 'text-bear'
                          }`}>
                            {stat.type === 'up' ? '▲' : '▼'}
                          </td>
                          <td className="px-4 py-2 text-center font-mono">{stat.threshold_label}</td>
                          <td className={`px-4 py-2 text-right font-mono font-medium ${
                            stat.probability >= 50 ? 'text-bull' : 'text-bear'
                          }`}>
                            {stat.probability.toFixed(1)}%
                          </td>
                          <td className="px-4 py-2 text-right text-dark-400">{stat.signals}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {(!result || result.data.length === 0) && !mutation.isPending && (
        <div className="card p-12 text-center">
          <TrendingUp className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-dark-300 mb-2">
            {language === 'ko' ? 'MA 크로스 분석을 실행하세요' : 'Run MA Cross Analysis'}
          </h3>
          <p className="text-dark-500 text-sm">
            {language === 'ko'
              ? '상단의 설정을 조정하고 "분석 실행" 버튼을 클릭하세요.'
              : 'Adjust settings above and click "Run Analysis" to see results.'}
          </p>
        </div>
      )}

      {/* Loading */}
      {mutation.isPending && (
        <div className="card p-12 text-center">
          <RefreshCw className="w-12 h-12 text-emerald-400 mx-auto mb-4 animate-spin" />
          <p className="text-dark-400">{labels.loading}</p>
        </div>
      )}
    </div>
  );
}

