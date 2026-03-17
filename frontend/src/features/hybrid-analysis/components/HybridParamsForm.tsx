import { usePageCommon } from '../../../hooks/usePageCommon';
import { RefreshCw, Zap, TrendingUp } from 'lucide-react';
import type { HybridBacktestParams, Coin } from '../../../types';
import type { Interval } from '../../../store/useStore';

const AVAILABLE_STRATEGIES = [
  { value: 'SMA_ADX_Strong', label: 'SMA_ADX_Strong', desc: 'SMA20 > SMA50 & ADX > 25' },
  { value: 'MACD_RSI_Trend', label: 'MACD_RSI_Trend', desc: 'MACD > 0 & RSI > 55 & Close > SMA200' },
  { value: 'Pure_Trend', label: 'Pure_Trend', desc: 'Close > SMA200' },
];

const GLOBAL_INTERVALS = ['15m', '1h', '2h', '4h', '1d', '3d', '1w', '1M'] as const;

interface HybridParamsFormProps {
  selectedCoin: Coin;
  setSelectedCoin: (coin: Coin) => void;
  selectedInterval: Interval;
  setSelectedInterval: (interval: Interval) => void;
  backtestParams: Omit<HybridBacktestParams, 'coin' | 'interval'>;
  setBacktestParams: (params: Omit<HybridBacktestParams, 'coin' | 'interval'>) => void;
  onRunBacktest: () => void;
  onRunLiveMode: () => void;
  isBacktestLoading: boolean;
  isLiveModeLoading: boolean;
  isBacktestDisabled: boolean;
}

export default function HybridParamsForm({
  selectedCoin,
  setSelectedCoin,
  selectedInterval,
  setSelectedInterval,
  backtestParams,
  setBacktestParams,
  onRunBacktest,
  onRunLiveMode,
  isBacktestLoading,
  isLiveModeLoading,
  isBacktestDisabled,
}: HybridParamsFormProps) {
  const { isKo } = usePageCommon();

  return (
    <div className="space-y-6">
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
              value={selectedCoin}
              onChange={(e) => setSelectedCoin(e.target.value.toUpperCase() as Coin)}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? '시간프레임' : 'Interval'}
            </label>
            <select
              value={selectedInterval}
              onChange={(e) => setSelectedInterval(e.target.value as Interval)}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            >
              {GLOBAL_INTERVALS.map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

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
          {/* Live Mode Button (Left) */}
          <button
            onClick={onRunLiveMode}
            disabled={isLiveModeLoading}
            className="bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white font-semibold py-2 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLiveModeLoading ? (
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
          
          {/* Backtest Button (Right) */}
          <button
            onClick={onRunBacktest}
            disabled={isBacktestDisabled}
            className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-2 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isBacktestLoading ? (
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
    </div>
  );
}


