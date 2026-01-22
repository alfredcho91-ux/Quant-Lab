// Weekly Pattern Analysis Page - 주간 패턴 분석
import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { runWeeklyPattern, runWeeklyPatternBacktest, getOHLCV } from '../api/client';
import { useStore } from '../store/useStore';
import { usePageCommon } from '../hooks/usePageCommon';
import { RefreshCw, BarChart2, AlertCircle } from 'lucide-react';
import { SkeletonAnalysis } from '../components/Skeleton';
import {
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
    rsi_min: 0,
    rsi_max: 40,
    start_day: 0,  // 월요일
    end_day: 1,  // 화요일
  });

  const [startDayOpen, setStartDayOpen] = useState<number | ''>('');  // 시작 요일 시가
  const [endDayClose, setEndDayClose] = useState<number | ''>('');  // 종료 요일 종가

  // 최근 일봉 데이터 가져오기 (월요일 시가 자동 로드)
  // limit을 30으로 줄여서 빠른 응답 (시작 요일 찾기에는 충분)
  const { data: ohlcvData, isLoading: isLoadingOHLCV, error: ohlcvError } = useQuery({
    queryKey: ['ohlcv', params.coin, '1d'],
    queryFn: () => getOHLCV(params.coin, '1d', false, 30),
    enabled: !!params.coin,
    retry: 1,  // 재시도 1회만
    retryDelay: 1000,  // 1초 후 재시도
    staleTime: 5 * 60 * 1000,  // 5분간 캐시 유지
  });

  // 가장 최근 시작 요일 시가 자동 로드
  useEffect(() => {
    if (!ohlcvData || !ohlcvData.data || !Array.isArray(ohlcvData.data)) {
      return;
    }

    const data = ohlcvData.data as any[];
    const startDay = params.start_day ?? 0;
    
    // 데이터가 없으면 리턴
    if (data.length === 0) {
      return;
    }

    // 날짜 기준으로 정렬 (최신순)
    const sortedData = [...data].sort((a, b) => {
      let dateA: number = 0;
      let dateB: number = 0;
      
      if (a.open_dt) {
        dateA = new Date(a.open_dt).getTime();
      } else if (a.open_time) {
        dateA = typeof a.open_time === 'number' 
          ? (a.open_time > 1e10 ? a.open_time : a.open_time * 1000)
          : parseInt(a.open_time);
      }
      
      if (b.open_dt) {
        dateB = new Date(b.open_dt).getTime();
      } else if (b.open_time) {
        dateB = typeof b.open_time === 'number'
          ? (b.open_time > 1e10 ? b.open_time : b.open_time * 1000)
          : parseInt(b.open_time);
      }
      
      return dateB - dateA;  // 최신순
    });
    
    // 가장 최근 시작 요일 찾기
    for (let i = 0; i < sortedData.length; i++) {
      const candle = sortedData[i];
      let date: Date | null = null;
      
      // open_time을 우선 사용
      if (candle.open_time) {
        const timeValue = typeof candle.open_time === 'number' 
          ? candle.open_time 
          : parseFloat(candle.open_time);
        if (timeValue > 1e10) {
          date = new Date(timeValue);
        } else if (timeValue > 1e9) {
          date = new Date(timeValue * 1000);
        }
      } 
      // open_dt 사용
      else if (candle.open_dt) {
        const dtStr = String(candle.open_dt);
        date = new Date(dtStr);
        if (isNaN(date.getTime())) {
          date = new Date(dtStr.replace(' ', 'T'));
        }
      }
      
      if (date && !isNaN(date.getTime())) {
        const dayOfWeek = date.getDay();  // 0=일요일, 1=월요일, ..., 6=토요일
        
        if (dayOfWeek === startDay) {  // 시작 요일
          const openPrice = parseFloat(
            String(candle.open || candle.Open || candle.open_price || '0')
          );
          
          if (openPrice && openPrice > 0 && !isNaN(openPrice)) {
            setStartDayOpen(openPrice);
            return;  // 찾았으면 종료
          }
        }
      }
    }
    
    // 해당 요일을 찾지 못한 경우 빈 값으로 설정
    setStartDayOpen('');
  }, [ohlcvData, params.start_day]);

  // 코인 변경 시에만 초기화 (요일 변경 시에는 시가 자동 로드가 처리)
  useEffect(() => {
    setStartDayOpen('');
    setEndDayClose('');
  }, [params.coin]);

  // 시작일 시가와 종료일 종가로 임계값 계산
  useEffect(() => {
    if (
      startDayOpen && 
      endDayClose && 
      typeof startDayOpen === 'number' && 
      typeof endDayClose === 'number' && 
      startDayOpen > 0 &&
      endDayClose > 0
    ) {
      const threshold = (endDayClose - startDayOpen) / startDayOpen;
      if (threshold < 0) {
        setParams((p) => ({ ...p, deep_drop_threshold: threshold }));
      } else {
        setParams((p) => ({ ...p, deep_rise_threshold: threshold }));
      }
    }
  }, [startDayOpen, endDayClose]);

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
    const isDown = startDayOpen && endDayClose && typeof startDayOpen === 'number' && typeof endDayClose === 'number' && endDayClose < startDayOpen;
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
            rsi_min: params.rsi_min,
            rsi_max: params.rsi_max,
            start_day: params.start_day ?? 0,
            end_day: params.end_day ?? 1,
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
        
        {/* API 에러 표시 */}
        {ohlcvError && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
            <p className="text-sm text-red-400">
              {isKo 
                ? '⚠️ 데이터 로딩 실패: API 서버가 응답하지 않습니다. 서버를 확인해주세요.'
                : '⚠️ Data loading failed: API server is not responding. Please check the server.'}
            </p>
          </div>
        )}
        
        <div className="space-y-4">
          {/* 1. 요일 선택 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-dark-400 mb-1">
                {isKo ? '분석 시작 요일' : 'Start Day'}
              </label>
              <select
                value={params.start_day ?? 0}
                onChange={(e) =>
                  setParams({
                    ...params,
                    start_day: parseInt(e.target.value),
                  })
                }
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
              >
                <option value={0}>{isKo ? '월요일' : 'Monday'}</option>
                <option value={1}>{isKo ? '화요일' : 'Tuesday'}</option>
                <option value={2}>{isKo ? '수요일' : 'Wednesday'}</option>
                <option value={3}>{isKo ? '목요일' : 'Thursday'}</option>
                <option value={4}>{isKo ? '금요일' : 'Friday'}</option>
                <option value={5}>{isKo ? '토요일' : 'Saturday'}</option>
                <option value={6}>{isKo ? '일요일' : 'Sunday'}</option>
              </select>
              <p className="text-xs text-dark-500 mt-1">
                {isKo
                  ? '분석할 기간의 시작 요일'
                  : 'Start day of the analysis period'}
              </p>
            </div>

            <div>
              <label className="block text-sm text-dark-400 mb-1">
                {isKo ? '분석 종료 요일' : 'End Day'}
              </label>
              <select
                value={params.end_day ?? 1}
                onChange={(e) =>
                  setParams({
                    ...params,
                    end_day: parseInt(e.target.value),
                  })
                }
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
              >
                <option value={0}>{isKo ? '월요일' : 'Monday'}</option>
                <option value={1}>{isKo ? '화요일' : 'Tuesday'}</option>
                <option value={2}>{isKo ? '수요일' : 'Wednesday'}</option>
                <option value={3}>{isKo ? '목요일' : 'Thursday'}</option>
                <option value={4}>{isKo ? '금요일' : 'Friday'}</option>
                <option value={5}>{isKo ? '토요일' : 'Saturday'}</option>
                <option value={6}>{isKo ? '일요일' : 'Sunday'}</option>
              </select>
              <p className="text-xs text-dark-500 mt-1">
                {isKo
                  ? '분석할 기간의 종료 요일 (다음 날부터 일요일까지 분석)'
                  : 'End day of the analysis period (analyze from next day to Sunday)'}
              </p>
            </div>
          </div>

          {/* 2. 가격 입력 (시작 요일 시가 자동 + 종료 요일 종가 수동) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-dark-500 mb-1">
                {isKo 
                  ? `분석 시작 요일(${['일', '월', '화', '수', '목', '금', '토'][params.start_day ?? 0]}요일) 시가 (자동 로드)` 
                  : `Start Day (${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][params.start_day ?? 0]}) Open (Auto-loaded)`}
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  value={startDayOpen}
                  readOnly
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-300 cursor-not-allowed"
                />
                {isLoadingOHLCV && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <RefreshCw className="w-4 h-4 animate-spin text-dark-400" />
                  </div>
                )}
              </div>
              <p className="text-xs text-dark-500 mt-1">
                {isKo 
                  ? 'API에서 최근 시작 요일 시가를 자동으로 불러옵니다'
                  : 'Automatically loaded from API (latest start day open)'}
              </p>
            </div>
            
            <div>
              <label className="block text-xs text-dark-500 mb-1">
                {isKo 
                  ? `분석 종료 요일(${['일', '월', '화', '수', '목', '금', '토'][params.end_day ?? 1]}요일) 종가 (수동 입력)` 
                  : `End Day (${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][params.end_day ?? 1]}) Close (Manual Input)`}
              </label>
              <input
                type="number"
                step="0.01"
                value={endDayClose}
                onChange={(e) => {
                  const value = e.target.value === '' ? '' : parseFloat(e.target.value);
                  setEndDayClose(value);
                }}
                placeholder={isKo ? '예: 47500' : 'e.g., 47500'}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
              />
              <p className="text-xs text-dark-500 mt-1">
                {isKo 
                  ? '종료 요일 종가를 입력하면 하락/상승이 자동으로 판단되고 임계값이 계산됩니다'
                  : 'Enter end day close price to auto-detect direction and calculate threshold'}
              </p>
            </div>
          </div>

          {/* 임계값 표시 */}
          {startDayOpen && endDayClose && typeof startDayOpen === 'number' && typeof endDayClose === 'number' && startDayOpen > 0 && (
            <div className="p-3 bg-dark-800 rounded-lg">
              <div className="text-xs text-dark-400 mb-1">
                {isKo ? '계산된 임계값 (자동 판단)' : 'Calculated Threshold (Auto-detected)'}
              </div>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-sm font-semibold ${
                  endDayClose < startDayOpen ? 'text-red-400' : 'text-emerald-400'
                }`}>
                  {endDayClose < startDayOpen 
                    ? (isKo ? '📉 하락' : '📉 Drop')
                    : (isKo ? '📈 상승' : '📈 Rise')}
                </span>
                <span className="text-lg font-bold text-dark-300">
                  {endDayClose < startDayOpen
                    ? (params.deep_drop_threshold * 100).toFixed(2)
                    : (params.deep_rise_threshold * 100).toFixed(2)}%
                </span>
              </div>
              <div className="text-xs text-dark-500 mt-1">
                {isKo 
                  ? `(${startDayOpen} → ${endDayClose})`
                  : `(${startDayOpen} → ${endDayClose})`}
              </div>
            </div>
          )}

          {/* 3. RSI 범위 설정 */}
          <div>
            <label className="block text-sm text-dark-400 mb-1">
              {isKo ? 'RSI 범위' : 'RSI Range'}
            </label>
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="text-xs text-dark-500 mb-1 block">
                  {isKo ? '최소' : 'Min'}
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  max="100"
                  value={params.rsi_min}
                  onChange={(e) =>
                    setParams({
                      ...params,
                      rsi_min: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div className="flex-1">
                <label className="text-xs text-dark-500 mb-1 block">
                  {isKo ? '최대' : 'Max'}
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  max="100"
                  value={params.rsi_max}
                  onChange={(e) =>
                    setParams({
                      ...params,
                      rsi_max: parseFloat(e.target.value) || 40,
                    })
                  }
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                />
              </div>
            </div>
            <p className="text-xs text-dark-500 mt-1">
              {isKo
                ? `종료 요일 RSI가 ${params.rsi_min}~${params.rsi_max} 범위일 때 ${params.direction === 'down' ? '과매도' : '과매수'}로 판단 (상승: ${100 - params.rsi_max}~${100 - params.rsi_min})`
                : `Oversold/Overbought when end day RSI is in range ${params.rsi_min}~${params.rsi_max} (Up: ${100 - params.rsi_max}~${100 - params.rsi_min})`}
            </p>
          </div>
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
