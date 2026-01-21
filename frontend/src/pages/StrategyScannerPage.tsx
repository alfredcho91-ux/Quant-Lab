// Strategy Scanner Page - Real-time signals for all strategies
import { useState } from 'react';
import { runStrategyScanner } from '../api/client';
import { usePageCommon } from '../hooks/usePageCommon';
import { useAnalysisMutation } from '../hooks/useAnalysisMutation';
import { RefreshCw } from 'lucide-react';

export default function StrategyScannerPage() {
  const { isKo, selectedCoin, timeframes } = usePageCommon();

  const [interval, setInterval] = useState('1h');

  const { mutation, handleRun } = useAnalysisMutation({
    mutationFn: runStrategyScanner,
  });

  const handleScan = () => {
    handleRun({
      coin: selectedCoin,
      interval,
    });
  };

  const result = mutation.data;

  const renderSignal = (long: boolean, short: boolean) => {
    const longIcon = long ? '🟢' : '⚪';
    const shortIcon = short ? '🔴' : '⚪';
    return (
      <div className="flex items-center gap-2 text-lg">
        <span>L {longIcon}</span>
        <span>/</span>
        <span>S {shortIcon}</span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            📡 {selectedCoin} {isKo ? '전략 스캐너' : 'Strategy Scanner'}
          </h1>
          <p className="text-dark-400 mt-1">
            {isKo
              ? '8개 전략의 실시간 Long/Short 시그널 모니터링'
              : 'Monitor real-time Long/Short signals for 8 strategies'}
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="card p-4 flex items-center gap-4">
        {/* Timeframe Selection */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-dark-400">{isKo ? '타임프레임' : 'Timeframe'}:</label>
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
          >
            {timeframes.map((tf) => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>
        </div>

        {/* Scan Button */}
        <button
          onClick={handleScan}
          disabled={mutation.isPending}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${mutation.isPending ? 'animate-spin' : ''}`} />
          {mutation.isPending
            ? (isKo ? '스캔 중...' : 'Scanning...')
            : (isKo ? '🔍 시그널 스캔' : '🔍 Scan Signals')}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Market Context */}
          <div className="card p-4 bg-dark-800/50">
            <div className="flex flex-wrap items-center gap-6 text-sm">
              <div>
                <span className="text-dark-400">{isKo ? '마지막 업데이트' : 'Last Update'}:</span>
                <span className="ml-2 font-mono">{result.market_context.last_time}</span>
              </div>
              <div>
                <span className="text-dark-400">{isKo ? '종가' : 'Close'}:</span>
                <span className="ml-2 font-mono">${result.market_context.last_close.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-dark-400">Regime:</span>
                <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                  result.market_context.regime === 'Bull'
                    ? 'bg-bull/20 text-bull'
                    : result.market_context.regime === 'Bear'
                    ? 'bg-bear/20 text-bear'
                    : 'bg-dark-600 text-dark-300'
                }`}>
                  {result.market_context.regime}
                </span>
              </div>
              <div>
                <span className="text-dark-400">ADX:</span>
                <span className="ml-2 font-mono">{result.market_context.adx.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-dark-400">RSI:</span>
                <span className={`ml-2 font-mono ${
                  result.market_context.rsi < 30 ? 'text-bull' : result.market_context.rsi > 70 ? 'text-bear' : ''
                }`}>
                  {result.market_context.rsi.toFixed(1)}
                </span>
              </div>
            </div>
          </div>

          {/* Strategy Signals Grid */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">
              {isKo ? '📊 기본 전략 시그널' : '📊 Built-in Strategy Signals'}
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {result.signals.map((signal) => {
                const hasSignal = signal.long_signal || signal.short_signal;
                return (
                  <div
                    key={signal.id}
                    className={`rounded-xl p-4 text-center transition-all ${
                      hasSignal
                        ? signal.long_signal
                          ? 'bg-bull/10 border-2 border-bull/30'
                          : 'bg-bear/10 border-2 border-bear/30'
                        : 'bg-dark-800'
                    }`}
                  >
                    <div className="text-sm font-medium mb-2 text-dark-300">
                      {isKo ? signal.name_ko : signal.name_en}
                    </div>
                    {renderSignal(signal.long_signal, signal.short_signal)}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Preset Signals */}
          {result.preset_signals.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">
                💾 {isKo ? '저장된 프리셋 시그널' : 'Saved Preset Signals'}
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {result.preset_signals.map((preset) => {
                  const hasSignal = preset.long_signal || preset.short_signal;
                  return (
                    <div
                      key={preset.name}
                      className={`rounded-xl p-4 text-center transition-all ${
                        hasSignal
                          ? preset.long_signal
                            ? 'bg-bull/10 border-2 border-bull/30'
                            : 'bg-bear/10 border-2 border-bear/30'
                          : 'bg-dark-800'
                      }`}
                    >
                      <div className="text-sm font-medium mb-1 text-dark-300">
                        💾 {preset.name}
                      </div>
                      <div className="text-xs text-dark-500 mb-2">
                        ({preset.strategy_id})
                      </div>
                      {renderSignal(preset.long_signal, preset.short_signal)}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="card p-4 text-sm text-dark-400">
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-2">
                <span>🟢</span>
                <span>{isKo ? 'Long 시그널 활성' : 'Long Signal Active'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span>🔴</span>
                <span>{isKo ? 'Short 시그널 활성' : 'Short Signal Active'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span>⚪</span>
                <span>{isKo ? '시그널 없음' : 'No Signal'}</span>
              </div>
            </div>
            <p className="mt-2 text-xs">
              {isKo
                ? '※ 각 전략의 기본 파라미터 기준입니다. 프리셋은 저장된 커스텀 파라미터를 사용합니다.'
                : '※ Uses default parameters for each strategy. Presets use saved custom parameters.'}
            </p>
          </div>

          {/* Active Signals Summary */}
          {(result.signals.some(s => s.long_signal || s.short_signal) ||
            result.preset_signals.some(p => p.long_signal || p.short_signal)) && (
            <div className="card p-4 bg-emerald-500/10 border border-emerald-500/30">
              <h4 className="font-semibold text-emerald-400 mb-2">
                ✨ {isKo ? '활성 시그널 요약' : 'Active Signals Summary'}
              </h4>
              <div className="space-y-1 text-sm">
                {result.signals.filter(s => s.long_signal).map(s => (
                  <div key={`${s.id}-long`} className="text-bull">
                    🟢 {isKo ? s.name_ko : s.name_en} - Long
                  </div>
                ))}
                {result.signals.filter(s => s.short_signal).map(s => (
                  <div key={`${s.id}-short`} className="text-bear">
                    🔴 {isKo ? s.name_ko : s.name_en} - Short
                  </div>
                ))}
                {result.preset_signals.filter(p => p.long_signal).map(p => (
                  <div key={`${p.name}-long`} className="text-bull">
                    🟢 💾 {p.name} - Long
                  </div>
                ))}
                {result.preset_signals.filter(p => p.short_signal).map(p => (
                  <div key={`${p.name}-short`} className="text-bear">
                    🔴 💾 {p.name} - Short
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Initial State */}
      {!result && !mutation.isPending && (
        <div className="card p-8 text-center text-dark-400">
          <p>{isKo ? '타임프레임을 선택하고 스캔 버튼을 눌러주세요.' : 'Select a timeframe and click scan.'}</p>
        </div>
      )}
    </div>
  );
}

