// Weekly Pattern Analysis Page - 주간 패턴 분석
import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { runWeeklyPattern, runWeeklyPatternBacktest, getOHLCV } from '../api/client';
import { useStore } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { RefreshCw, BarChart2, AlertCircle } from 'lucide-react';
import { SkeletonAnalysis } from '../components/Skeleton';
import {
  PriceInputPanel,
  AnalysisSummary,
  FilterResults,
  BacktestResults,
} from '../components/weekly-pattern';
import type { WeeklyPatternParams } from '../types';

export default function WeeklyPatternPage() {
  const { selectedCoin } = useStore();
  const { isKo } = usePageCommon();
  const safeSelectedCoin = selectedCoin || 'ETH';

  const [params, setParams] = useState<WeeklyPatternParams>({
    coin: safeSelectedCoin,
    interval: '1d',
    deep_drop_threshold: -0.05,
    deep_rise_threshold: 0.05,
    rsi_threshold: 40,
  });

  const [mondayOpen, setMondayOpen] = useState<number | ''>('');
  const [tuesdayClose, setTuesdayClose] = useState<number | ''>('');

  // 최근 일봉 데이터 가져오기 (월요일 시가 자동 로드)
  const { data: ohlcvData, isLoading: isLoadingOHLCV } = useQuery({
    queryKey: ['ohlcv', params.coin, '1d'],
    queryFn: () => getOHLCV(params.coin, '1d', false, 100),
    enabled: !!params.coin,
  });

  // 가장 최근 월요일 시가 자동 로드
  useEffect(() => {
    if (ohlcvData && ohlcvData.data && Array.isArray(ohlcvData.data)) {
      const data = ohlcvData.data as any[];
      const sortedData = [...data].sort((a, b) => {
        const dateA = new Date(a.open_dt || a.open_time || a.timestamp || a.date || 0).getTime();
        const dateB = new Date(b.open_dt || b.open_time || b.timestamp || b.date || 0).getTime();
        return dateB - dateA;
      });
      
      for (const candle of sortedData) {
        let date: Date | null = null;
        
        if (candle.open_dt) {
          date = new Date(candle.open_dt);
        } else if (candle.open_time) {
          date = new Date(typeof candle.open_time === 'number' ? candle.open_time : parseInt(candle.open_time));
        } else if (candle.timestamp) {
          date = new Date(typeof candle.timestamp === 'number' ? candle.timestamp : parseInt(candle.timestamp));
        } else if (candle.date) {
          date = new Date(candle.date);
        }
        
        if (date && !isNaN(date.getTime())) {
          const dayOfWeek = date.getDay();
          
          if (dayOfWeek === 1) {
            const openPrice = parseFloat(
              candle.open || candle.Open || candle.open_price || 0
            );
            if (openPrice && openPrice > 0 && !isNaN(openPrice)) {
              setMondayOpen(openPrice);
              break;
            }
          }
        }
      }
    }
  }, [ohlcvData, params.coin]);

  useEffect(() => {
    setMondayOpen('');
    setTuesdayClose('');
  }, [params.coin]);

  useEffect(() => {
    if (
      mondayOpen && 
      tuesdayClose && 
      typeof mondayOpen === 'number' && 
      typeof tuesdayClose === 'number' && 
      mondayOpen > 0 &&
      tuesdayClose > 0
    ) {
      const threshold = (tuesdayClose - mondayOpen) / mondayOpen;
      if (threshold < 0) {
        setParams((p) => ({ ...p, deep_drop_threshold: threshold }));
      } else {
        setParams((p) => ({ ...p, deep_rise_threshold: threshold }));
      }
    }
  }, [mondayOpen, tuesdayClose]);

  useEffect(() => {
    if (selectedCoin) {
      setParams((p) => ({ ...p, coin: selectedCoin }));
    }
  }, [selectedCoin]);

  const mutation = useMutation({
    mutationFn: runWeeklyPattern,
    onError: (error) => {
      console.error('Weekly Pattern Analysis Error:', error);
    },
  });

  const backtestMutation = useMutation({
    mutationFn: runWeeklyPatternBacktest,
    onError: (error) => {
      console.error('Weekly Pattern Backtest Error:', error);
    },
  });

  const handleRun = () => {
    const isDown = mondayOpen && tuesdayClose && typeof mondayOpen === 'number' && typeof tuesdayClose === 'number' && tuesdayClose < mondayOpen;
    const direction = isDown ? 'down' : 'up';
    
    mutation.mutate({ ...params, direction }, {
      onSuccess: (data) => {
        if (data && data.success) {
          backtestMutation.mutate({
            coin: params.coin,
            interval: params.interval,
            direction: direction,
            deep_drop_threshold: params.deep_drop_threshold,
            deep_rise_threshold: params.deep_rise_threshold,
            rsi_threshold: params.rsi_threshold,
            leverage: 1,
            fee_entry_rate: 0.0005,
            fee_exit_rate: 0.0005,
          });
        }
      },
      onError: (error) => {
        console.error('Weekly Pattern Analysis failed:', error);
      },
    });
  };

  const result = mutation.data;
  const backtestResult = backtestMutation.data;
  const isLoading = mutation.isPending || backtestMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">
            {isKo ? '📅 주간 패턴 분석' : '📅 Weekly Pattern Analysis'}
          </h1>
          <p className="text-dark-400">
            {isKo
              ? '주 초반(월-화) 수익률과 주 후반(수-일) 수익률 관계 분석'
              : 'Analysis of relationship between early week (Mon-Tue) and mid-late week (Wed-Sun) returns'}
          </p>
        </div>
      </div>

      {/* Parameters */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold mb-4">
          {isKo ? '파라미터 설정' : 'Parameters'}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <PriceInputPanel
            mondayOpen={mondayOpen}
            tuesdayClose={tuesdayClose}
            params={params}
            isLoadingOHLCV={isLoadingOHLCV}
            isKo={isKo}
            onTuesdayCloseChange={setTuesdayClose}
          />

          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? 'RSI 임계값' : 'RSI Threshold'}
            </label>
            <input
              type="number"
              step="1"
              value={params.rsi_threshold}
              onChange={(e) =>
                setParams({
                  ...params,
                  rsi_threshold: parseFloat(e.target.value) || 40,
                })
              }
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
            />
            <p className="text-xs text-dark-500 mt-1">
              {isKo
                ? params.direction === 'down'
                  ? '화요일 RSI가 이 값 미만일 때 과매도로 판단'
                  : '화요일 RSI가 (100 - 이 값) 초과일 때 과매수로 판단'
                : params.direction === 'down'
                  ? 'Oversold when Tuesday RSI is below this value'
                  : 'Overbought when Tuesday RSI is above (100 - this value)'}
            </p>
          </div>
          
          {params.direction === 'up' && (
            <div>
              <label className="block text-sm text-dark-400 mb-1">
                {isKo ? '깊은 상승 임계값' : 'Deep Rise Threshold'}
              </label>
              <input
                type="number"
                step="0.01"
                value={params.deep_rise_threshold * 100}
                onChange={(e) =>
                  setParams({
                    ...params,
                    deep_rise_threshold: parseFloat(e.target.value) / 100 || 0.05,
                  })
                }
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
              />
              <p className="text-xs text-dark-500 mt-1">
                {isKo
                  ? '주 초반 상승률이 이 값 이상일 때 깊은 상승으로 판단'
                  : 'Deep rise when Mon-Tue return is above this value'}
              </p>
            </div>
          )}
        </div>

        <button
          onClick={handleRun}
          disabled={isLoading}
          className="mt-6 w-full bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 text-white font-semibold py-3 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>{isKo ? '분석 중...' : 'Analyzing...'}</span>
            </>
          ) : (
            <>
              <BarChart2 className="w-5 h-5" />
              <span>{isKo ? '분석 실행' : 'Run Analysis'}</span>
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {isLoading && <SkeletonAnalysis />}

      {result && result.success && (
        <div className="space-y-6">
          <AnalysisSummary result={result} isKo={isKo} />
          <FilterResults result={result} isKo={isKo} />
          {backtestResult && <BacktestResults backtestResult={backtestResult} isKo={isKo} />}
        </div>
      )}

      {mutation.isError && (
        <div className="card p-6 bg-red-500/10 border border-red-500/20">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">
              {isKo ? '오류 발생' : 'Error'}
            </span>
          </div>
          <p className="mt-2 text-sm text-dark-300">
            {mutation.error instanceof Error ? mutation.error.message : 'Unknown error occurred'}
          </p>
        </div>
      )}

      {result && !result.success && (
        <div className="card p-6 bg-red-500/10 border border-red-500/20">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">
              {isKo ? '분석 실패' : 'Analysis Failed'}
            </span>
          </div>
          <p className="mt-2 text-sm text-dark-300">{result.error || (isKo ? '알 수 없는 오류가 발생했습니다.' : 'Unknown error occurred')}</p>
          {result.warnings && result.warnings.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-dark-400 mb-1">{isKo ? '경고:' : 'Warnings:'}</p>
              <ul className="list-disc list-inside text-xs text-dark-500">
                {result.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {backtestResult && !backtestResult.success && (
        <div className="card p-6 bg-yellow-500/10 border border-yellow-500/20">
          <div className="flex items-center gap-2 text-yellow-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">
              {isKo ? '백테스팅 경고' : 'Backtest Warning'}
            </span>
          </div>
          <p className="mt-2 text-sm text-dark-300">{backtestResult.error || (isKo ? '백테스팅 결과가 없습니다.' : 'No backtest results.')}</p>
        </div>
      )}
    </div>
  );
}
