// Advanced Backtest Page with Train/Test Split & Statistics
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { runAdvancedBacktest, getStrategies, getTimeframes } from '../api/client';
import {
  useBacktestParams,
  useLanguage,
  useSelectedCoin,
  useUpdateBacktestParams,
} from '../store/useStore';
import type { BacktestParams, AdvancedBacktestResult } from '../types';
import { AlertTriangle, CheckCircle, BarChart2 } from 'lucide-react';

export default function AdvancedBacktestPage() {
  const language = useLanguage();
  const selectedCoin = useSelectedCoin();
  const backtestParams = useBacktestParams();
  const updateBacktestParams = useUpdateBacktestParams();
  const isKo = language === 'ko';

  const { data: strategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: getStrategies,
  });

  const { data: tfData } = useQuery({
    queryKey: ['timeframes', selectedCoin],
    queryFn: () => getTimeframes(selectedCoin),
  });

  const timeframes = tfData?.all || ['1h', '4h', '1d'];

  const [params, setParams] = useState<BacktestParams & { train_ratio: number; monte_carlo_runs: number }>({
    coin: selectedCoin,
    interval: backtestParams.interval || '1h',
    strategy_id: backtestParams.strategy_id || 'Connors',
    direction: backtestParams.direction || 'Long',
    tp_pct: backtestParams.tp_pct || 2.0,
    sl_pct: backtestParams.sl_pct || 1.0,
    max_bars: backtestParams.max_bars || 48,
    leverage: backtestParams.leverage || 10,
    entry_fee_pct: backtestParams.entry_fee_pct || 0.04,
    exit_fee_pct: backtestParams.exit_fee_pct || 0.04,
    rsi_ob: backtestParams.rsi_ob || 70,
    sma_main_len: backtestParams.sma_main_len || 200,
    sma1_len: backtestParams.sma1_len || 20,
    sma2_len: backtestParams.sma2_len || 60,
    adx_thr: backtestParams.adx_thr || 25,
    donch: backtestParams.donch || 20,
    bb_length: backtestParams.bb_length || 20,
    bb_std_mult: backtestParams.bb_std_mult || 2.0,
    atr_length: backtestParams.atr_length || 20,
    kc_mult: backtestParams.kc_mult || 1.5,
    vol_ma_length: backtestParams.vol_ma_length || 20,
    vol_spike_k: backtestParams.vol_spike_k || 2.0,
    macd_fast: backtestParams.macd_fast || 12,
    macd_slow: backtestParams.macd_slow || 26,
    macd_signal: backtestParams.macd_signal || 9,
    use_csv: backtestParams.use_csv || false,
    train_ratio: 0.7,
    monte_carlo_runs: 1000,
  });

  const mutation = useMutation({
    mutationFn: runAdvancedBacktest,
  });

  const handleRun = () => {
    mutation.mutate({ ...params, coin: selectedCoin });
  };

  const result = mutation.data;

  const renderStatCard = (label: string, value: number | null | undefined, suffix: string = '', isGood?: boolean) => {
    const displayValue = value != null ? `${value.toFixed(2)}${suffix}` : '-';
    const colorClass = isGood === true ? 'text-bull' : isGood === false ? 'text-bear' : 'text-white';
    
    return (
      <div className="bg-dark-800 rounded-lg p-3">
        <div className={`text-lg font-bold ${colorClass}`}>{displayValue}</div>
        <div className="text-xs text-dark-400">{label}</div>
      </div>
    );
  };

  const renderSampleSection = (
    title: string,
    summary: AdvancedBacktestResult['in_sample']['summary'],
    stats: AdvancedBacktestResult['in_sample']['stats'],
    period?: { start: string | null; end: string | null },
    isTest: boolean = false
  ) => {
    return (
      <div className={`card p-6 ${isTest ? 'border-2 border-primary-500/30' : ''}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            {isTest ? <CheckCircle className="w-5 h-5 text-primary-400" /> : <BarChart2 className="w-5 h-5 text-dark-400" />}
            {title}
            {isTest && <span className="text-xs bg-primary-500/20 text-primary-400 px-2 py-0.5 rounded">
              {isKo ? '실제 성과' : 'Real Performance'}
            </span>}
          </h3>
          {period?.start && period?.end && (
            <span className="text-xs text-dark-500">
              {period.start.slice(0, 10)} ~ {period.end.slice(0, 10)}
            </span>
          )}
        </div>

        {/* Basic Summary */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          {renderStatCard(isKo ? '거래 수' : 'Trades', summary.n_trades)}
          {renderStatCard(isKo ? '승률' : 'Win Rate', summary.win_rate, '%', summary.win_rate > 50)}
          {renderStatCard(isKo ? '총 수익' : 'Total PnL', summary.total_pnl, '%', summary.total_pnl > 0)}
          {renderStatCard(isKo ? '평균 수익' : 'Avg PnL', summary.avg_pnl, '%', summary.avg_pnl > 0)}
        </div>

        {/* Advanced Stats */}
        <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
          {renderStatCard(isKo ? '샤프 비율' : 'Sharpe', stats.sharpe_ratio, '', stats.sharpe_ratio != null && stats.sharpe_ratio > 1)}
          {renderStatCard(isKo ? '소르티노' : 'Sortino', stats.sortino_ratio, '', stats.sortino_ratio != null && stats.sortino_ratio > 1)}
          {renderStatCard(isKo ? '최대 낙폭' : 'Max DD', stats.max_drawdown, '%', stats.max_drawdown != null && stats.max_drawdown < 20)}
          {renderStatCard(isKo ? '수익 팩터' : 'Profit Factor', stats.profit_factor, '', stats.profit_factor != null && stats.profit_factor > 1.5)}
          {renderStatCard(isKo ? '승/패 비율' : 'Win/Loss', stats.win_loss_ratio, '', stats.win_loss_ratio != null && stats.win_loss_ratio > 1)}
        </div>

        {/* Statistical Significance */}
        {summary.n_trades >= 30 && (
          <div className={`mt-4 p-3 rounded-lg flex items-center gap-3 ${
            stats.is_significant ? 'bg-primary-500/10 border border-primary-500/30' : 'bg-yellow-500/10 border border-yellow-500/30'
          }`}>
            {stats.is_significant ? (
              <CheckCircle className="w-5 h-5 text-primary-400" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
            )}
            <div>
              <div className={`font-medium ${stats.is_significant ? 'text-primary-400' : 'text-yellow-400'}`}>
                {stats.is_significant 
                  ? (isKo ? '통계적으로 유의미함 ✓' : 'Statistically Significant ✓')
                  : (isKo ? '통계적 유의성 부족' : 'Not Statistically Significant')}
              </div>
              <div className="text-xs text-dark-400">
                t-stat: {stats.t_statistic?.toFixed(2) || '-'}, p-value: {stats.p_value?.toFixed(4) || '-'}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          🔬 {selectedCoin} {isKo ? '고급 백테스트' : 'Advanced Backtest'}
        </h1>
        <p className="text-dark-400 mt-1">
          {isKo
            ? 'Train/Test 분리 + 통계적 검증 + 몬테카를로 시뮬레이션'
            : 'Train/Test Split + Statistical Validation + Monte Carlo'}
        </p>
      </div>

      {/* Controls */}
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {/* Strategy */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">{isKo ? '전략' : 'Strategy'}</label>
            <select
              value={params.strategy_id}
              onChange={(e) => setParams({ ...params, strategy_id: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              {strategies?.map((s) => (
                <option key={s.id} value={s.id}>
                  {isKo ? s.name_ko : s.name_en}
                </option>
              ))}
            </select>
          </div>

          {/* Direction */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">{isKo ? '방향' : 'Direction'}</label>
            <select
              value={params.direction}
              onChange={(e) => setParams({ ...params, direction: e.target.value as 'Long' | 'Short' })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="Long">Long</option>
              <option value="Short">Short</option>
            </select>
          </div>

          {/* Timeframe */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">{isKo ? '타임프레임' : 'Timeframe'}</label>
            <select
              value={params.interval}
              onChange={(e) => setParams({ ...params, interval: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              {timeframes.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>

          {/* TP */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">TP %</label>
            <input
              type="number"
              step={0.1}
              value={params.tp_pct}
              onChange={(e) => {
                const newTp = parseFloat(e.target.value) || 2;
                setParams({ ...params, tp_pct: newTp });
                updateBacktestParams({ tp_pct: newTp }); // 전역 설정 동기화
              }}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* SL */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">SL %</label>
            <input
              type="number"
              step={0.1}
              value={params.sl_pct}
              onChange={(e) => {
                const newSl = parseFloat(e.target.value) || 1;
                setParams({ ...params, sl_pct: newSl });
                updateBacktestParams({ sl_pct: newSl }); // 전역 설정 동기화
              }}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Train Ratio */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '훈련 비율' : 'Train Ratio'}: {(params.train_ratio * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min={0.5}
              max={0.9}
              step={0.05}
              value={params.train_ratio}
              onChange={(e) => setParams({ ...params, train_ratio: parseFloat(e.target.value) })}
              className="w-full"
            />
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
            : (isKo ? '🔬 고급 백테스트 실행' : '🔬 Run Advanced Backtest')}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Train/Test Split Info */}
          <div className="card p-4 bg-dark-800/50">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-dark-500"></div>
                <span className="text-dark-400">
                  In-Sample ({(params.train_ratio * 100).toFixed(0)}%): {isKo ? '파라미터 최적화용' : 'For optimization'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-primary-500"></div>
                <span className="text-dark-400">
                  Out-of-Sample ({((1 - params.train_ratio) * 100).toFixed(0)}%): {isKo ? '실제 성과 검증' : 'Real validation'}
                </span>
              </div>
            </div>
          </div>

          {/* In-Sample Results */}
          {renderSampleSection(
            isKo ? '📊 In-Sample (훈련 데이터)' : '📊 In-Sample (Training)',
            result.in_sample.summary,
            result.in_sample.stats,
            result.in_sample.period
          )}

          {/* Out-of-Sample Results */}
          {renderSampleSection(
            isKo ? '✅ Out-of-Sample (테스트 데이터)' : '✅ Out-of-Sample (Test)',
            result.out_of_sample.summary,
            result.out_of_sample.stats,
            result.out_of_sample.period,
            true
          )}

          {/* Monte Carlo Simulation */}
          {result.monte_carlo && result.monte_carlo.mean_final_pnl !== null && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                🎲 {isKo ? '몬테카를로 시뮬레이션' : 'Monte Carlo Simulation'}
                <span className="text-xs text-dark-500">({params.monte_carlo_runs.toLocaleString()} runs)</span>
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="bg-dark-800 rounded-lg p-4 text-center">
                  <div className="text-xl font-bold text-white">
                    {result.monte_carlo.mean_final_pnl?.toFixed(1)}%
                  </div>
                  <div className="text-xs text-dark-400">{isKo ? '평균 수익률' : 'Mean Return'}</div>
                </div>
                <div className="bg-dark-800 rounded-lg p-4 text-center">
                  <div className="text-xl font-bold text-bear">
                    {result.monte_carlo.worst_case?.toFixed(1)}%
                  </div>
                  <div className="text-xs text-dark-400">{isKo ? '최악의 경우' : 'Worst Case'}</div>
                </div>
                <div className="bg-dark-800 rounded-lg p-4 text-center">
                  <div className="text-xl font-bold text-bull">
                    {result.monte_carlo.best_case?.toFixed(1)}%
                  </div>
                  <div className="text-xs text-dark-400">{isKo ? '최선의 경우' : 'Best Case'}</div>
                </div>
                <div className="bg-dark-800 rounded-lg p-4 text-center">
                  <div className="text-xl font-bold text-yellow-400">
                    {result.monte_carlo.median_max_dd?.toFixed(1)}%
                  </div>
                  <div className="text-xs text-dark-400">{isKo ? '중앙 MDD' : 'Median MDD'}</div>
                </div>
              </div>

              {/* 95% Confidence Interval */}
              <div className="bg-dark-800/50 rounded-lg p-4">
                <div className="text-sm text-dark-400 mb-2">
                  {isKo ? '95% 신뢰구간' : '95% Confidence Interval'}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-bear font-mono">{result.monte_carlo.ci_lower?.toFixed(1)}%</span>
                  <div className="flex-1 h-3 bg-dark-700 rounded-full overflow-hidden relative">
                    <div
                      className="absolute h-full bg-gradient-to-r from-bear via-yellow-500 to-bull"
                      style={{
                        left: '2.5%',
                        right: '2.5%',
                      }}
                    />
                  </div>
                  <span className="text-bull font-mono">{result.monte_carlo.ci_upper?.toFixed(1)}%</span>
                </div>
                <p className="text-xs text-dark-500 mt-2">
                  {isKo 
                    ? '거래 순서가 달라졌을 때 95% 확률로 이 범위 안에 수익률이 위치함'
                    : '95% probability that returns fall within this range with different trade ordering'}
                </p>
              </div>
            </div>
          )}

          {/* Trade Count Warning */}
          {result.out_of_sample.summary.n_trades < 30 && (
            <div className="card p-4 bg-yellow-500/10 border border-yellow-500/30 flex items-center gap-3">
              <AlertTriangle className="w-6 h-6 text-yellow-400 flex-shrink-0" />
              <div>
                <div className="font-medium text-yellow-400">
                  {isKo ? '⚠️ 거래 수 부족' : '⚠️ Insufficient Trades'}
                </div>
                <div className="text-sm text-dark-400">
                  {isKo 
                    ? `Out-of-Sample 거래 수가 ${result.out_of_sample.summary.n_trades}회로, 통계적 검증에 최소 30회 이상 필요합니다.`
                    : `Out-of-Sample has only ${result.out_of_sample.summary.n_trades} trades. At least 30 are needed for statistical validation.`}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
