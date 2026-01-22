// Hybrid Strategy Analysis Page - 하이브리드 전략 분석
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { runHybridBacktest, runHybridLiveMode } from '../api/client';
import { useStore } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { RefreshCw, BarChart2, AlertCircle, TrendingUp, Zap, CheckCircle, XCircle } from 'lucide-react';
import { SkeletonAnalysis } from '../components/Skeleton';
import type { HybridBacktestParams, Coin } from '../types';

const AVAILABLE_STRATEGIES = [
  { value: 'EMA_ADX_Strong', label: 'EMA_ADX_Strong', desc: 'EMA20 > EMA50 & ADX > 25' },
  { value: 'MACD_RSI_Trend', label: 'MACD_RSI_Trend', desc: 'MACD > 0 & RSI > 55 & Close > SMA200' },
  { value: 'Pure_Trend', label: 'Pure_Trend', desc: 'Close > SMA200' },
];

const INTERVALS = ['1h', '2h', '4h', '1d'];

export default function HybridAnalysisPage() {
  const { selectedCoin } = useStore();
  const { isKo } = usePageCommon();
  const safeSelectedCoin = selectedCoin || 'BTC';

  // 공통 파라미터
  const [commonParams, setCommonParams] = useState<{
    coin: Coin;
    interval: string;
  }>({
    coin: safeSelectedCoin as Coin,
    interval: '1h',
  });

  const [backtestParams, setBacktestParams] = useState<Omit<HybridBacktestParams, 'coin' | 'interval'>>({
    strategy: 'EMA_ADX_Strong',
    tp: 2.0,
    sl: 1.0,
    max_hold: 5,
  });

  const backtestMutation = useMutation({
    mutationFn: runHybridBacktest,
  });

  const liveModeMutation = useMutation({
    mutationFn: runHybridLiveMode,
  });

  const handleRunBacktest = () => {
    backtestMutation.mutate({
      coin: commonParams.coin,
      interval: commonParams.interval,
      ...backtestParams,
    });
  };

  const handleRunLiveMode = () => {
    liveModeMutation.mutate({
      coin: commonParams.coin,
      interval: commonParams.interval,
    });
  };

  const backtestResult = backtestMutation.data;
  const liveModeResult = liveModeMutation.data;
  const isLoading = backtestMutation.isPending || liveModeMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart2 className="w-6 h-6" />
          {isKo ? '하이브리드 전략 분석' : 'Hybrid Strategy Analysis'}
        </h1>
        <p className="text-dark-400 mt-1">
          {isKo
            ? '여러 지표를 조합한 하이브리드 전략 분석 및 백테스팅'
            : 'Hybrid strategy analysis combining multiple indicators'}
        </p>
      </div>

      {/* Common Parameters */}
      <div className="card p-6 space-y-4 border-l-4 border-blue-500">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="text-lg font-semibold text-white">
            {isKo ? '공통 파라미터' : 'Common Parameters'}
          </h2>
          <span className="text-xs text-dark-500 bg-dark-700 px-2 py-1 rounded">
            {isKo ? '라이브 모드 & 백테스팅 공통 사용' : 'Used by Live Mode & Backtest'}
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '코인' : 'Coin'}
            </label>
            <input
              type="text"
              value={commonParams.coin}
              onChange={(e) => setCommonParams({ ...commonParams, coin: e.target.value.toUpperCase() as Coin })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '시간프레임' : 'Interval'}
            </label>
            <select
              value={commonParams.interval}
              onChange={(e) => setCommonParams({ ...commonParams, interval: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              {INTERVALS.map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Live Mode Results */}
      {liveModeResult && liveModeResult.success && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-green-400" />
            {isKo ? '라이브 모드 결과' : 'Live Mode Results'}
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 p-4 bg-dark-800 rounded-lg">
              <div>
                <div className="text-sm text-dark-400">{isKo ? '타임스탬프' : 'Timestamp'}</div>
                <div className="text-sm font-mono text-white">
                  {new Date(liveModeResult.timestamp).toLocaleString('ko-KR')}
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? '현재 가격' : 'Current Price'}</div>
                <div className="text-lg font-bold text-white">
                  {liveModeResult.current_price?.toFixed(2) || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? '활성 전략 수' : 'Active Strategies'}</div>
                <div className="text-lg font-bold text-green-400">
                  {liveModeResult.strategies.filter(s => s.is_active).length} / {liveModeResult.strategies.length}
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              {liveModeResult.strategies.map((strategy) => (
                <div
                  key={strategy.strategy}
                  className={`p-4 rounded-lg border-2 ${
                    strategy.is_active
                      ? 'bg-green-500/10 border-green-500/50'
                      : 'bg-dark-800 border-dark-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-white">{strategy.strategy}</h3>
                    <div className="flex items-center gap-2">
                      {strategy.is_active ? (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-400" />
                          <span className="text-green-400 font-semibold">{isKo ? '활성' : 'Active'}</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-5 h-5 text-red-400" />
                          <span className="text-red-400 font-semibold">{isKo ? '비활성' : 'Inactive'}</span>
                        </>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                    {strategy.strategy === 'EMA_ADX_Strong' && (
                      <>
                        <div>
                          <div className="text-dark-400">EMA20</div>
                          <div className="text-white font-mono">{strategy.conditions.ema20?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">EMA50</div>
                          <div className="text-white font-mono">{strategy.conditions.ema50?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">ADX</div>
                          <div className="text-white font-mono">{strategy.conditions.adx?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">EMA20 &gt; EMA50</div>
                          <div className={strategy.conditions.ema20_above_ema50 ? 'text-green-400' : 'text-red-400'}>
                            {strategy.conditions.ema20_above_ema50 ? '✓' : '✗'}
                          </div>
                        </div>
                        <div>
                          <div className="text-dark-400">ADX &gt; 25</div>
                          <div className={strategy.conditions.adx_above_25 ? 'text-green-400' : 'text-red-400'}>
                            {strategy.conditions.adx_above_25 ? '✓' : '✗'}
                          </div>
                        </div>
                      </>
                    )}
                    {strategy.strategy === 'MACD_RSI_Trend' && (
                      <>
                        <div>
                          <div className="text-dark-400">MACD Hist</div>
                          <div className="text-white font-mono">{strategy.conditions.macd_hist?.toFixed(4) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">RSI</div>
                          <div className="text-white font-mono">{strategy.conditions.rsi?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">Close</div>
                          <div className="text-white font-mono">{strategy.conditions.close?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">SMA200</div>
                          <div className="text-white font-mono">{strategy.conditions.sma200?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">MACD &gt; 0</div>
                          <div className={strategy.conditions.macd_positive ? 'text-green-400' : 'text-red-400'}>
                            {strategy.conditions.macd_positive ? '✓' : '✗'}
                          </div>
                        </div>
                        <div>
                          <div className="text-dark-400">RSI &gt; 55</div>
                          <div className={strategy.conditions.rsi_above_55 ? 'text-green-400' : 'text-red-400'}>
                            {strategy.conditions.rsi_above_55 ? '✓' : '✗'}
                          </div>
                        </div>
                        <div>
                          <div className="text-dark-400">Close &gt; SMA200</div>
                          <div className={strategy.conditions.close_above_sma200 ? 'text-green-400' : 'text-red-400'}>
                            {strategy.conditions.close_above_sma200 ? '✓' : '✗'}
                          </div>
                        </div>
                      </>
                    )}
                    {strategy.strategy === 'Pure_Trend' && (
                      <>
                        <div>
                          <div className="text-dark-400">Close</div>
                          <div className="text-white font-mono">{strategy.conditions.close?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">SMA200</div>
                          <div className="text-white font-mono">{strategy.conditions.sma200?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-dark-400">Close &gt; SMA200</div>
                          <div className={strategy.conditions.close_above_sma200 ? 'text-green-400' : 'text-red-400'}>
                            {strategy.conditions.close_above_sma200 ? '✓' : '✗'}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Live Mode Errors */}
      {liveModeMutation.isError && (
        <div className="card p-6 bg-red-500/10 border border-red-500/20">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">{isKo ? '라이브 모드 오류' : 'Live Mode Error'}</span>
          </div>
          <p className="mt-2 text-sm text-dark-300">
            {liveModeMutation.error instanceof Error
              ? liveModeMutation.error.message
              : 'Unknown error occurred'}
          </p>
        </div>
      )}

      {/* Backtest Controls */}
      <div className="card p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-white mb-1">
            {isKo ? '백테스팅' : 'Backtest'}
          </h2>
          <p className="text-xs text-dark-500">
            {isKo 
              ? '공통 파라미터를 사용하여 선택한 전략의 TP/SL 백테스팅을 수행합니다'
              : 'Perform TP/SL backtesting for selected strategy using common parameters'}
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '전략' : 'Strategy'}
            </label>
            <select
              value={backtestParams.strategy}
              onChange={(e) => setBacktestParams({ ...backtestParams, strategy: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              {AVAILABLE_STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '익절 (%)' : 'TP (%)'}
            </label>
            <input
              type="number"
              step="0.1"
              value={backtestParams.tp}
              onChange={(e) => setBacktestParams({ ...backtestParams, tp: parseFloat(e.target.value) || 2.0 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '손절 (%)' : 'SL (%)'}
            </label>
            <input
              type="number"
              step="0.1"
              value={backtestParams.sl}
              onChange={(e) => setBacktestParams({ ...backtestParams, sl: parseFloat(e.target.value) || 1.0 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '최대 보유' : 'Max Hold'}
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={backtestParams.max_hold}
              onChange={(e) => setBacktestParams({ ...backtestParams, max_hold: parseInt(e.target.value) || 5 })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>
        <div className="flex items-center justify-between">
          {/* Live Mode Button (왼쪽 하단) */}
          <button
            onClick={handleRunLiveMode}
            disabled={liveModeMutation.isPending}
            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold py-2 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {liveModeMutation.isPending ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>{isKo ? '확인 중...' : 'Checking...'}</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>{isKo ? '라이브 모드' : 'Live Mode'}</span>
              </>
            )}
          </button>
          
          {/* Backtest Button (오른쪽) */}
          <button
            onClick={handleRunBacktest}
            disabled={isLoading}
            className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-2 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {backtestMutation.isPending ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>{isKo ? '백테스팅 중...' : 'Backtesting...'}</span>
              </>
            ) : (
              <>
                <TrendingUp className="w-4 h-4" />
                <span>{isKo ? '백테스팅 실행' : 'Run Backtest'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Loading */}
      {isLoading && <SkeletonAnalysis />}

      {/* Backtest Results */}
      {backtestResult && backtestResult.success && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            {isKo ? '백테스팅 결과' : 'Backtest Results'}
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-4">
              <div>
                <div className="text-sm text-dark-400">{isKo ? '거래 수' : 'Trades'}</div>
                <div className="text-xl font-bold">{backtestResult.summary.n_trades}</div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? '승률' : 'Win Rate'}</div>
                <div className={`text-xl font-bold ${backtestResult.summary.win_rate > 50 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {backtestResult.summary.win_rate.toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? '총 수익률' : 'Total PnL'}</div>
                <div className={`text-xl font-bold ${backtestResult.summary.total_pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {backtestResult.summary.total_pnl > 0 ? '+' : ''}
                  {backtestResult.summary.total_pnl.toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? '평균 수익률' : 'Avg PnL'}</div>
                <div className={`text-xl font-bold ${backtestResult.summary.avg_pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {backtestResult.summary.avg_pnl > 0 ? '+' : ''}
                  {backtestResult.summary.avg_pnl.toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? 'Profit Factor' : 'Profit Factor'}</div>
                <div className={`text-xl font-bold ${backtestResult.summary.profit_factor && backtestResult.summary.profit_factor > 1 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {backtestResult.summary.profit_factor !== null
                    ? backtestResult.summary.profit_factor.toFixed(2)
                    : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? 'TP 적중률' : 'TP Hit Rate'}</div>
                <div className="text-xl font-bold text-emerald-400">
                  {backtestResult.summary.tp_hit_rate.toFixed(2)}%
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <div className="text-sm text-dark-400">{isKo ? '최대 수익' : 'Max PnL'}</div>
                <div className="text-lg font-bold text-emerald-400">
                  +{backtestResult.summary.max_pnl.toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? '최대 손실' : 'Min PnL'}</div>
                <div className="text-lg font-bold text-red-400">
                  {backtestResult.summary.min_pnl.toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? 'SL 적중률' : 'SL Hit Rate'}</div>
                <div className="text-lg font-bold text-red-400">
                  {backtestResult.summary.sl_hit_rate.toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-dark-400">{isKo ? '평균 보유' : 'Avg Hold'}</div>
                <div className="text-lg font-bold">
                  {backtestResult.summary.avg_hold.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Errors */}
      {backtestMutation.isError && (
        <div className="card p-6 bg-red-500/10 border border-red-500/20">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">{isKo ? '오류 발생' : 'Error'}</span>
          </div>
          <p className="mt-2 text-sm text-dark-300">
            {backtestMutation.error instanceof Error
              ? backtestMutation.error.message
              : 'Unknown error occurred'}
          </p>
        </div>
      )}
    </div>
  );
}
