// Strategy Scanner Page
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { useLanguage, useSelectedCoin } from '../store/useStore';
import { getLabels } from '../store/labels';
import { getStrategies, getOHLCV } from '../api/client';
import type { Strategy } from '../types';

interface SignalResult {
  strategy: string;
  strategyId: string;
  longSignal: boolean;
  shortSignal: boolean;
  regime: string;
  rsi: number;
  adx: number;
}

// Simple indicator calculations (client-side for scanner)
function calculateRSI(closes: number[], period: number = 14): number[] {
  const rsi: number[] = [];
  
  for (let i = 0; i < closes.length; i++) {
    if (i < period) {
      rsi.push(50);
      continue;
    }
    
    let gains = 0;
    let losses = 0;
    
    for (let j = i - period + 1; j <= i; j++) {
      const diff = closes[j] - closes[j - 1];
      if (diff > 0) gains += diff;
      else losses -= diff;
    }
    
    const avgGain = gains / period;
    const avgLoss = losses / period;
    
    if (avgLoss === 0) {
      rsi.push(100);
    } else {
      const rs = avgGain / avgLoss;
      rsi.push(100 - (100 / (1 + rs)));
    }
  }
  
  return rsi;
}

function calculateSMA(data: number[], period: number): number[] {
  const sma: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    const window = data.slice(start, i + 1);
    const mean = window.reduce((acc, v) => acc + v, 0) / window.length;
    sma.push(mean);
  }
  return sma;
}

export default function ScannerPage() {
  const language = useLanguage();
  const selectedCoin = useSelectedCoin();
  const labels = getLabels(language);
  const [interval, setInterval] = useState('1h');
  const [signals, setSignals] = useState<SignalResult[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Fetch strategies
  const { data: strategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: getStrategies,
    staleTime: Infinity,
  });

  // Fetch OHLCV data
  const { data: ohlcvData, isLoading, refetch } = useQuery({
    queryKey: ['scanner-ohlcv', selectedCoin, interval],
    queryFn: () => getOHLCV(selectedCoin, interval, false, 500),
    staleTime: 30000,
    refetchInterval: 60000, // Auto refresh every minute
  });

  // Scan for signals
  useEffect(() => {
    if (!ohlcvData?.data || !strategies) return;
    
    interface OHLCVRow {
      open: number;
      high: number;
      low: number;
      close: number;
    }
    
    const data = ohlcvData.data as OHLCVRow[];
    const closes = data.map((d) => d.close);
    
    // Calculate indicators
    const rsi = calculateRSI(closes);
    const sma200 = calculateSMA(closes, 200);
    
    // Simple ADX approximation (using RSI as proxy for this demo)
    const adx = rsi.map(r => Math.abs(r - 50) * 2);
    
    const lastIdx = data.length - 1;
    const currentClose = closes[lastIdx];
    const currentRSI = rsi[lastIdx];
    const currentSMA = sma200[lastIdx];
    const currentADX = adx[lastIdx];
    
    // Determine regime
    let regime = 'Sideways';
    if (currentADX >= 25) {
      regime = currentClose > currentSMA ? 'Bull' : 'Bear';
    }
    
    // Generate signals for each strategy
    const results: SignalResult[] = [];
    
    strategies.forEach((strat: Strategy) => {
      let longSignal = false;
      let shortSignal = false;
      
      switch (strat.id) {
        case 'RSI':
          longSignal = currentRSI < 30;
          shortSignal = currentRSI > 70;
          break;
        case 'Connors':
          longSignal = currentClose > currentSMA && currentRSI < 30;
          shortSignal = currentClose < currentSMA && currentRSI > 70;
          break;
        case 'MA': {
          const sma20 = closes.slice(-20).reduce((a, b) => a + b, 0) / 20;
          const sma60 = closes.slice(-60).reduce((a, b) => a + b, 0) / 60;
          longSignal = sma20 > sma60 && currentClose > currentSMA;
          shortSignal = sma20 < sma60 && currentClose < currentSMA;
          break;
        }
        case 'Turtle': {
          const high20 = Math.max(...data.slice(-20).map(d => d.high));
          const low20 = Math.min(...data.slice(-20).map(d => d.low));
          longSignal = currentClose > high20 && currentClose > currentSMA;
          shortSignal = currentClose < low20 && currentClose < currentSMA;
          break;
        }
        default:
          // Generic signal based on RSI
          longSignal = currentRSI < 35 && currentClose > currentSMA;
          shortSignal = currentRSI > 65 && currentClose < currentSMA;
      }
      
      results.push({
        strategy: language === 'ko' ? strat.name_ko : strat.name_en,
        strategyId: strat.id,
        longSignal,
        shortSignal,
        regime,
        rsi: currentRSI,
        adx: currentADX,
      });
    });
    
    setSignals(results);
    setLastUpdate(new Date());
  }, [ohlcvData, strategies, language]);

  const activeSignals = signals.filter(s => s.longSignal || s.shortSignal);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="w-7 h-7 text-primary-400" />
            {language === 'ko' ? '실시간 전략 스캐너' : 'Live Strategy Scanner'}
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {language === 'ko'
              ? '8개 전략의 실시간 시그널을 모니터링합니다.'
              : 'Monitor real-time signals for all 8 strategies.'}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="bg-dark-800"
          >
            {['15m', '30m', '1h', '2h', '4h'].map((tf) => (
              <option key={tf} value={tf}>
                {tf}
              </option>
            ))}
          </select>
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            {language === 'ko' ? '새로고침' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Status Bar */}
      <div className="card p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm text-dark-400">
            {language === 'ko' ? '코인' : 'Coin'}: <strong className="text-primary-400">{selectedCoin}</strong>
          </span>
          <span className="text-sm text-dark-400">
            {language === 'ko' ? '타임프레임' : 'Timeframe'}: <strong>{interval}</strong>
          </span>
          <span className="text-sm text-dark-400">
            {language === 'ko' ? '활성 시그널' : 'Active Signals'}: 
            <strong className={activeSignals.length > 0 ? 'text-warning' : 'text-dark-300'}>
              {' '}{activeSignals.length}
            </strong>
          </span>
        </div>
        {lastUpdate && (
          <span className="text-xs text-dark-500">
            {language === 'ko' ? '마지막 업데이트' : 'Last update'}: {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Market Info */}
      {signals.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="metric-card">
            <span className="metric-label">RSI(14)</span>
            <span className={`metric-value ${signals[0].rsi < 30 ? 'text-bull' : signals[0].rsi > 70 ? 'text-bear' : ''}`}>
              {signals[0].rsi.toFixed(1)}
            </span>
          </div>
          <div className="metric-card">
            <span className="metric-label">ADX</span>
            <span className="metric-value">{signals[0].adx.toFixed(1)}</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">{language === 'ko' ? '장세' : 'Regime'}</span>
            <span className={`metric-value text-lg ${
              signals[0].regime === 'Bull' ? 'text-bull' : 
              signals[0].regime === 'Bear' ? 'text-bear' : 'text-warning'
            }`}>
              {signals[0].regime}
            </span>
          </div>
        </div>
      )}

      {/* Signals Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {signals.map((signal) => (
          <div
            key={signal.strategyId}
            className={`card p-4 transition-all ${
              signal.longSignal || signal.shortSignal
                ? 'border-2 border-warning/50 bg-warning/5'
                : ''
            }`}
          >
            <h4 className="font-medium text-sm mb-3 truncate" title={signal.strategy}>
              {signal.strategy}
            </h4>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {signal.longSignal ? (
                  <CheckCircle className="w-5 h-5 text-bull" />
                ) : (
                  <XCircle className="w-5 h-5 text-dark-600" />
                )}
                <span className={signal.longSignal ? 'text-bull font-medium' : 'text-dark-500'}>
                  Long
                </span>
              </div>
              <div className="flex items-center gap-2">
                {signal.shortSignal ? (
                  <CheckCircle className="w-5 h-5 text-bear" />
                ) : (
                  <XCircle className="w-5 h-5 text-dark-600" />
                )}
                <span className={signal.shortSignal ? 'text-bear font-medium' : 'text-dark-500'}>
                  Short
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Loading State */}
      {isLoading && signals.length === 0 && (
        <div className="card p-12 text-center">
          <RefreshCw className="w-12 h-12 text-dark-500 mx-auto mb-4 animate-spin" />
          <p className="text-dark-400">{labels.loading}</p>
        </div>
      )}
    </div>
  );
}
