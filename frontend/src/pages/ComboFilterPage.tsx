// Combo Filter Test Page
import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { runComboFilter } from '../api/client';
import { useStore } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { SkeletonStats, SkeletonChart } from '../components/Skeleton';
import type { ComboFilterParams } from '../types';

const PATTERNS = ['Bullish Engulfing', 'Bearish Engulfing', 'Hammer', 'Doji', 'Shooting Star'];

export default function ComboFilterPage() {
  const { backtestParams, updateBacktestParams } = useStore();
  const { isKo, timeframes, selectedCoin } = usePageCommon();

  const [params, setParams] = useState<ComboFilterParams>({
    coin: selectedCoin || 'BTC',
    interval: '1h',
    direction: 'long',
    tp_pct: backtestParams.tp_pct || 1.0, // 전역 설정 사용
    horizon: 5,
    rsi_min: 40,
    rsi_max: 60,
    sma_short: 5,
    sma_long: 20,
    filter1_type: 'none',
    filter1_params: {},
    filter2_type: 'none',
    filter2_params: {},
    filter3_type: 'none',
    filter3_params: {},
    use_csv: backtestParams.use_csv, // 전역 설정 사용
  });

  const mutation = useMutation({
    mutationFn: runComboFilter,
  });

  const handleRun = () => {
    console.log('🚀 Combo Filter 실행:', params);
    // useAnalysisMutation의 handleRun이 coin을 덮어쓰므로, 직접 mutation.mutate 호출
    mutation.mutate(params, {
      onSuccess: (data) => {
        console.log('✅ Combo Filter 성공:', data);
      },
      onError: (error) => {
        console.error('❌ Combo Filter 실패:', error);
      }
    });
  };

  const renderFilterConfig = (
    filterNum: 1 | 2 | 3,
    filterType: string,
    filterParams: Record<string, unknown>,
    setFilter: (type: string, params: Record<string, unknown>) => void
  ) => {
    return (
      <div className="space-y-3 p-4 bg-dark-800/50 rounded-lg">
        <div>
          <label className="block text-sm text-dark-400 mb-1">
            {isKo ? `${filterNum}차 필터` : `Filter ${filterNum}`}
          </label>
          <select
            value={filterType}
            onChange={(e) => setFilter(e.target.value, {})}
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
          >
            <option value="none">{isKo ? '없음' : 'None'}</option>
            <option value="ma_cross">{isKo ? 'MA 크로스' : 'MA Cross'}</option>
            <option value="bb">{isKo ? '볼밴 조건' : 'Bollinger'}</option>
            <option value="pattern">{isKo ? '캔들 패턴' : 'Pattern'}</option>
          </select>
        </div>

        {filterType === 'ma_cross' && (
          <div>
            <label className="block text-xs text-dark-500 mb-1">{isKo ? 'MA 모드' : 'MA Mode'}</label>
            <select
              value={(filterParams.ma_mode as string) || 'golden'}
              onChange={(e) => setFilter(filterType, { ...filterParams, ma_mode: e.target.value })}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="golden">{isKo ? '골든크로스' : 'Golden Cross'}</option>
              <option value="dead">{isKo ? '데드크로스' : 'Dead Cross'}</option>
            </select>
          </div>
        )}

        {filterType === 'bb' && (
          <div>
            <label className="block text-xs text-dark-500 mb-1">{isKo ? '볼밴 조건' : 'BB Condition'}</label>
            <select
              value={(filterParams.bb_mode as string) || 'lower_touch'}
              onChange={(e) => setFilter(filterType, { ...filterParams, bb_mode: e.target.value })}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="lower_touch">{isKo ? '하단 터치' : 'Lower Touch'}</option>
              <option value="upper_touch">{isKo ? '상단 터치' : 'Upper Touch'}</option>
              <option value="mid_reversion">{isKo ? '중단 터치' : 'Mid Touch'}</option>
            </select>
          </div>
        )}

        {filterType === 'pattern' && (
          <div>
            <label className="block text-xs text-dark-500 mb-1">{isKo ? '패턴' : 'Pattern'}</label>
            <select
              value={(filterParams.pattern_key as string) || ''}
              onChange={(e) => setFilter(filterType, { ...filterParams, pattern_key: e.target.value })}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="">{isKo ? '선택...' : 'Select...'}</option>
              {PATTERNS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        )}
      </div>
    );
  };

  const result = mutation.data;

  // 디버깅: 결과 확인
  useEffect(() => {
    if (mutation.isSuccess) {
      console.log('✅ Combo Filter 성공:', result);
      if (!result) {
        console.warn('⚠️ Combo Filter: API 성공했지만 결과가 null입니다');
      }
    }
    if (mutation.isError) {
      console.error('❌ Combo Filter 에러:', mutation.error);
    }
  }, [mutation.isSuccess, mutation.isError, result, mutation.error]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          🧪 {selectedCoin} {isKo ? '통합 필터 테스트' : 'Combo Filter Test'}
        </h1>
        <p className="text-dark-400 mt-1">
          {isKo
            ? 'MA, 볼밴, 패턴 조건을 조합하여 TP 달성률 테스트'
            : 'Combine MA, Bollinger, and pattern conditions to test TP hit rate'}
        </p>
      </div>

      {/* Main Settings */}
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          {/* Timeframe */}
          <div>
            <label className="block text-xs text-dark-400 mb-1">{isKo ? 'TF' : 'TF'}</label>
            <select
              value={params.interval}
              onChange={(e) => setParams({ ...params, interval: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
            >
              {timeframes.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>

          {/* Direction */}
          <div>
            <label className="block text-xs text-dark-400 mb-1">{isKo ? '방향' : 'Dir'}</label>
            <select
              value={params.direction}
              onChange={(e) => setParams({ ...params, direction: e.target.value as 'long' | 'short' })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
            >
              <option value="long">Long</option>
              <option value="short">Short</option>
            </select>
          </div>

          {/* TP */}
          <div>
            <label className="block text-xs text-dark-400 mb-1">TP %</label>
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
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
            />
          </div>

          {/* Horizon */}
          <div>
            <label className="block text-xs text-dark-400 mb-1">{isKo ? 'N봉' : 'Bars'}</label>
            <input
              type="number"
              min={1}
              max={50}
              value={params.horizon}
              onChange={(e) => setParams({ ...params, horizon: parseInt(e.target.value) || 5 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
            />
          </div>

          {/* SMA Short */}
          <div>
            <label className="block text-xs text-dark-400 mb-1">{isKo ? '단기SMA' : 'Short'}</label>
            <input
              type="number"
              min={3}
              max={100}
              value={params.sma_short}
              onChange={(e) => setParams({ ...params, sma_short: parseInt(e.target.value) || 5 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
            />
          </div>

          {/* SMA Long */}
          <div>
            <label className="block text-xs text-dark-400 mb-1">{isKo ? '장기SMA' : 'Long'}</label>
            <input
              type="number"
              min={5}
              max={400}
              value={params.sma_long}
              onChange={(e) => setParams({ ...params, sma_long: parseInt(e.target.value) || 20 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
            />
          </div>

          {/* RSI Range */}
          <div className="col-span-2">
            <label className="block text-xs text-dark-400 mb-1">
              RSI: {params.rsi_min}-{params.rsi_max}
            </label>
            <div className="flex gap-1">
              <input
                type="number"
                min={0}
                max={100}
                value={params.rsi_min}
                onChange={(e) => setParams({ ...params, rsi_min: parseInt(e.target.value) || 0 })}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
              />
              <input
                type="number"
                min={0}
                max={100}
                value={params.rsi_max}
                onChange={(e) => setParams({ ...params, rsi_max: parseInt(e.target.value) || 100 })}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-2 py-2 text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Filter Configuration */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">
          {isKo ? '필터 설정 (1차 → 3차)' : 'Filter Configuration'}
        </h3>
        <div className="grid md:grid-cols-3 gap-4">
          {renderFilterConfig(
            1,
            params.filter1_type,
            params.filter1_params,
            (type, p) => setParams({ ...params, filter1_type: type, filter1_params: p })
          )}
          {renderFilterConfig(
            2,
            params.filter2_type,
            params.filter2_params,
            (type, p) => setParams({ ...params, filter2_type: type, filter2_params: p })
          )}
          {renderFilterConfig(
            3,
            params.filter3_type,
            params.filter3_params,
            (type, p) => setParams({ ...params, filter3_type: type, filter3_params: p })
          )}
        </div>
      </div>

      {/* Run Button */}
      <button
        onClick={handleRun}
        disabled={mutation.isPending}
        className="w-full btn-primary py-3 disabled:opacity-50"
      >
        {mutation.isPending
          ? (isKo ? '테스트 중...' : 'Testing...')
          : (isKo ? '🚀 통합 필터 TP 백테스트 실행' : '🚀 Run Combo Filter Backtest')}
      </button>

      {/* Loading Skeleton */}
      {mutation.isPending && (
        <div className="space-y-6">
          <SkeletonStats />
          <SkeletonChart />
        </div>
      )}

      {/* Error Message */}
      {mutation.isError && (
        <div className="card p-6 bg-red-500/10 border border-red-500/30">
          <h3 className="text-lg font-semibold text-red-400 mb-2">
            {isKo ? '❌ 분석 실패' : '❌ Analysis Failed'}
          </h3>
          <p className="text-red-300">
            {mutation.error instanceof Error 
              ? mutation.error.message 
              : (isKo ? '알 수 없는 오류가 발생했습니다' : 'Unknown error occurred')}
          </p>
        </div>
      )}

      {/* Results */}
      {!mutation.isPending && mutation.isSuccess && result && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">
            {isKo ? 'TP 전용 백테스트 결과' : 'TP-Only Backtest Results'} ({params.direction.toUpperCase()})
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-dark-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">{result.events}</div>
              <div className="text-sm text-dark-400">{isKo ? '총 이벤트' : 'Total Events'}</div>
            </div>
            <div className="bg-dark-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-bull">{result.tp_hits}</div>
              <div className="text-sm text-dark-400">{isKo ? 'TP 달성' : 'TP Hits'}</div>
            </div>
            <div className="bg-dark-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-bear">{result.no_tp}</div>
              <div className="text-sm text-dark-400">{isKo ? 'TP 미달' : 'No TP'}</div>
            </div>
            <div className="bg-dark-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-emerald-400">
                {result.hit_rate?.toFixed(1) || '-'}%
              </div>
              <div className="text-sm text-dark-400">{isKo ? '달성률' : 'Hit Rate'}</div>
            </div>
          </div>

          {result.avg_ret !== null && (
            <div className="text-center">
              <span className="text-dark-400">{isKo ? '평균 수익률' : 'Avg Return'}:</span>
              <span className={`ml-2 font-bold ${result.avg_ret >= 0 ? 'text-bull' : 'text-bear'}`}>
                {result.avg_ret >= 0 ? '+' : ''}{result.avg_ret.toFixed(3)}%
              </span>
            </div>
          )}

          {/* Visual Bar */}
          {result.events > 0 && (
            <div className="mt-6">
              <div className="flex h-8 rounded-lg overflow-hidden">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-green-400 flex items-center justify-center"
                  style={{ width: `${(result.tp_hits / result.events) * 100}%` }}
                >
                  {result.tp_hits > 0 && (
                    <span className="text-xs font-bold text-white">TP Hit</span>
                  )}
                </div>
                <div
                  className="bg-gradient-to-r from-red-500 to-orange-400 flex items-center justify-center"
                  style={{ width: `${(result.no_tp / result.events) * 100}%` }}
                >
                  {result.no_tp > 0 && (
                    <span className="text-xs font-bold text-white">No TP</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

