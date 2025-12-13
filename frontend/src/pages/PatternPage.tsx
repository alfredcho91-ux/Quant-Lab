// Pattern Statistics Page
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, RefreshCw } from 'lucide-react';
import { useStore } from '../store/useStore';
import { getLabels } from '../store/labels';
import { getOHLCV } from '../api/client';

// Candle pattern detection functions
function detectEngulfing(data: {open: number; close: number; high: number; low: number}[]) {
  const results: { index: number; type: 'bullish' | 'bearish' }[] = [];
  
  for (let i = 1; i < data.length; i++) {
    const prev = data[i - 1];
    const curr = data[i];
    
    const prevBullish = prev.close > prev.open;
    const currBullish = curr.close > curr.open;
    
    // Bullish engulfing
    if (!prevBullish && currBullish) {
      if (curr.open <= prev.close && curr.close >= prev.open) {
        results.push({ index: i, type: 'bullish' });
      }
    }
    
    // Bearish engulfing
    if (prevBullish && !currBullish) {
      if (curr.open >= prev.close && curr.close <= prev.open) {
        results.push({ index: i, type: 'bearish' });
      }
    }
  }
  
  return results;
}

function detectDoji(data: {open: number; close: number; high: number; low: number}[]) {
  const results: number[] = [];
  
  for (let i = 0; i < data.length; i++) {
    const candle = data[i];
    const bodySize = Math.abs(candle.close - candle.open);
    const totalSize = candle.high - candle.low;
    
    if (totalSize > 0 && bodySize / totalSize < 0.1) {
      results.push(i);
    }
  }
  
  return results;
}

function detectHammer(data: {open: number; close: number; high: number; low: number}[]) {
  const results: number[] = [];
  
  for (let i = 0; i < data.length; i++) {
    const candle = data[i];
    const bodySize = Math.abs(candle.close - candle.open);
    const upperWick = candle.high - Math.max(candle.open, candle.close);
    const lowerWick = Math.min(candle.open, candle.close) - candle.low;
    
    // Hammer: small body, long lower wick, short upper wick
    if (lowerWick > bodySize * 2 && upperWick < bodySize * 0.5) {
      results.push(i);
    }
  }
  
  return results;
}

interface PatternStat {
  name: string;
  count: number;
  avgReturn: number;
  winRate: number;
}

export default function PatternPage() {
  const { language, selectedCoin } = useStore();
  const labels = getLabels(language);
  const [interval, setInterval] = useState('1h');
  const [patternStats, setPatternStats] = useState<PatternStat[]>([]);

  const { data: ohlcvData, isLoading, refetch } = useQuery({
    queryKey: ['ohlcv', selectedCoin, interval],
    queryFn: () => getOHLCV(selectedCoin, interval, false, 1000),
    staleTime: 60000,
  });

  const analyzePatterns = () => {
    if (!ohlcvData?.data) return;
    
    const data = ohlcvData.data as {open: number; close: number; high: number; low: number}[];
    const stats: PatternStat[] = [];
    
    // Engulfing patterns
    const engulfing = detectEngulfing(data);
    const bullishEngulf = engulfing.filter(e => e.type === 'bullish');
    const bearishEngulf = engulfing.filter(e => e.type === 'bearish');
    
    // Calculate returns after bullish engulfing
    if (bullishEngulf.length > 0) {
      let wins = 0;
      let totalReturn = 0;
      bullishEngulf.forEach(({ index }) => {
        if (index + 5 < data.length) {
          const ret = (data[index + 5].close - data[index].close) / data[index].close * 100;
          totalReturn += ret;
          if (ret > 0) wins++;
        }
      });
      stats.push({
        name: language === 'ko' ? '상승 장악형 (Bullish Engulfing)' : 'Bullish Engulfing',
        count: bullishEngulf.length,
        avgReturn: totalReturn / bullishEngulf.length,
        winRate: (wins / bullishEngulf.length) * 100,
      });
    }
    
    if (bearishEngulf.length > 0) {
      let wins = 0;
      let totalReturn = 0;
      bearishEngulf.forEach(({ index }) => {
        if (index + 5 < data.length) {
          const ret = (data[index].close - data[index + 5].close) / data[index].close * 100;
          totalReturn += ret;
          if (ret > 0) wins++;
        }
      });
      stats.push({
        name: language === 'ko' ? '하락 장악형 (Bearish Engulfing)' : 'Bearish Engulfing',
        count: bearishEngulf.length,
        avgReturn: totalReturn / bearishEngulf.length,
        winRate: (wins / bearishEngulf.length) * 100,
      });
    }
    
    // Doji
    const doji = detectDoji(data);
    if (doji.length > 0) {
      let wins = 0;
      let totalReturn = 0;
      doji.forEach((index) => {
        if (index + 5 < data.length) {
          const ret = Math.abs(data[index + 5].close - data[index].close) / data[index].close * 100;
          totalReturn += ret;
          if (ret > 0) wins++;
        }
      });
      stats.push({
        name: language === 'ko' ? '도지 (Doji)' : 'Doji',
        count: doji.length,
        avgReturn: totalReturn / doji.length,
        winRate: (wins / doji.length) * 100,
      });
    }
    
    // Hammer
    const hammer = detectHammer(data);
    if (hammer.length > 0) {
      let wins = 0;
      let totalReturn = 0;
      hammer.forEach((index) => {
        if (index + 5 < data.length) {
          const ret = (data[index + 5].close - data[index].close) / data[index].close * 100;
          totalReturn += ret;
          if (ret > 0) wins++;
        }
      });
      stats.push({
        name: language === 'ko' ? '해머 (Hammer)' : 'Hammer',
        count: hammer.length,
        avgReturn: totalReturn / hammer.length,
        winRate: (wins / hammer.length) * 100,
      });
    }
    
    setPatternStats(stats);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{labels.title_pattern}</h1>
          <p className="text-dark-400 text-sm mt-1">
            {language === 'ko'
              ? '캔들 패턴을 분석하고 통계를 확인하세요.'
              : 'Analyze candlestick patterns and view statistics.'}
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="bg-dark-800"
          >
            {['15m', '30m', '1h', '2h', '4h', '1d'].map((tf) => (
              <option key={tf} value={tf}>
                {tf}
              </option>
            ))}
          </select>
          <button
            onClick={() => {
              refetch();
              analyzePatterns();
            }}
            disabled={isLoading}
            className="btn btn-primary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            {language === 'ko' ? '분석 실행' : 'Analyze'}
          </button>
        </div>
      </div>

      {/* Data Info */}
      {ohlcvData && (
        <div className="card p-4">
          <div className="flex items-center gap-4 text-sm text-dark-400">
            <span>
              {language === 'ko' ? '데이터 수' : 'Data count'}: {ohlcvData.count}
            </span>
            <span>
              {language === 'ko' ? '소스' : 'Source'}: {ohlcvData.source}
            </span>
          </div>
        </div>
      )}

      {/* Pattern Statistics */}
      {patternStats.length > 0 && (
        <div className="card">
          <div className="p-4 border-b border-dark-700 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-semibold">
              {language === 'ko' ? '패턴 통계' : 'Pattern Statistics'}
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-dark-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs text-dark-400 uppercase">
                    {language === 'ko' ? '패턴' : 'Pattern'}
                  </th>
                  <th className="px-4 py-3 text-right text-xs text-dark-400 uppercase">
                    {language === 'ko' ? '발생 횟수' : 'Count'}
                  </th>
                  <th className="px-4 py-3 text-right text-xs text-dark-400 uppercase">
                    {language === 'ko' ? '평균 수익률 (5봉 후)' : 'Avg Return (5 bars)'}
                  </th>
                  <th className="px-4 py-3 text-right text-xs text-dark-400 uppercase">
                    {language === 'ko' ? '승률' : 'Win Rate'}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700">
                {patternStats.map((stat, idx) => (
                  <tr key={idx} className="hover:bg-dark-700/30">
                    <td className="px-4 py-3 font-medium">{stat.name}</td>
                    <td className="px-4 py-3 text-right font-mono">{stat.count}</td>
                    <td
                      className={`px-4 py-3 text-right font-mono ${
                        stat.avgReturn >= 0 ? 'text-bull' : 'text-bear'
                      }`}
                    >
                      {stat.avgReturn >= 0 ? '+' : ''}
                      {stat.avgReturn.toFixed(2)}%
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-mono ${
                        stat.winRate >= 50 ? 'text-bull' : 'text-bear'
                      }`}
                    >
                      {stat.winRate.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {patternStats.length === 0 && !isLoading && (
        <div className="card p-12 text-center">
          <BarChart3 className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-dark-300 mb-2">
            {language === 'ko' ? '패턴 분석을 실행하세요' : 'Run Pattern Analysis'}
          </h3>
          <p className="text-dark-500 text-sm">
            {language === 'ko'
              ? '상단의 "분석 실행" 버튼을 클릭하여 캔들 패턴 통계를 확인하세요.'
              : 'Click the "Analyze" button above to view candlestick pattern statistics.'}
          </p>
        </div>
      )}
    </div>
  );
}

