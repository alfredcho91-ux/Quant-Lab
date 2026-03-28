// Streak Analysis Page - 양봉/음봉 연속성 시뮬레이터
import { useQuery } from '@tanstack/react-query';
import { usePageCommon } from '../hooks/usePageCommon';
import { SkeletonAnalysis } from '../components/Skeleton';
import { Zap, AlertTriangle } from 'lucide-react';
import { useStreakAnalysisForm } from '../features/streak-analysis/hooks/useStreakAnalysisForm';
import AnalysisControls from '../features/streak-analysis/components/AnalysisControls';
import StatisticsSummary from '../features/streak-analysis/components/StatisticsSummary';
import VolatilityDataGrid from '../features/streak-analysis/components/VolatilityDataGrid';
import IntervalAnalysisTable from '../features/streak-analysis/components/IntervalAnalysisTable';
import { runTrendIndicators } from '../api/stats';

export default function StreakAnalysisPage() {
  const { isKo } = usePageCommon();

  const {
    useComplexPattern,
    setUseComplexPattern,
    condition1,
    setCondition1,
    condition2,
    setCondition2,
    minTotalBodyPct,
    setMinTotalBodyPct,
    params,
    setParams,
    handleCandleModeChange,
    mutation,
    handleRun,
  } = useStreakAnalysisForm();

  const result = mutation.data;
  const activeResultCandleMode = result?.analysis_mode?.parameters.candle_mode ?? params.candle_mode ?? 'standard';
  const activeResultCandleModeLabel =
    activeResultCandleMode === 'heikin_ashi'
      ? (isKo ? '하이킨아시 캔들 기준' : 'Heikin-Ashi Basis')
      : (isKo ? '일반 캔들 기준' : 'Standard Candle Basis');
  const moveLabel =
    params.direction === 'green' ? (isKo ? '상승' : 'Up') : (isKo ? '하락' : 'Down');

  // Fetch current indicators for highlighting in Conditional Breakdown
  const { data: trendData } = useQuery({
    queryKey: ['trendIndicators', params.coin, params.interval],
    queryFn: () => runTrendIndicators({ coin: params.coin, interval: params.interval, use_csv: false }),
    refetchInterval: 60000, // 1 minute
  });

  const currentValues = trendData?.latest ? {
    rsi: trendData.latest.rsi,
    disp: trendData.latest.close && trendData.latest.sma20 ? (trendData.latest.close / trendData.latest.sma20) * 100 : null,
    atr: trendData.latest.atr_pct,
  } : undefined;

  const getStrategyAdvice = () => {
    if (!result || result.continuation_rate === null) return null;
    const rate = result.continuation_rate;
    if (rate < 30) {
      return {
        type: 'reversal',
        color: 'from-rose-500 to-pink-500',
        bgColor: 'bg-rose-500/10 border-rose-500/30',
        icon: <AlertTriangle className="w-6 h-6" />,
        title: isKo ? '🔥 강력한 역추세(반전) 구간!' : '🔥 Strong Reversal Zone!',
        desc: isKo
          ? `${moveLabel}이 멈출 확률이 매우 높습니다. 반대 포지션을 고려하세요.`
          : `High probability that ${moveLabel} trend will stop. Consider opposite position.`,
      };
    } else if (rate > 60) {
      return {
        type: 'trend',
        color: 'from-primary-500 to-primary-600',
        bgColor: 'bg-primary-500/10 border-primary-500/30',
        icon: <Zap className="w-6 h-6" />,
        title: isKo ? '🚀 추세 관성이 강한 구간!' : '🚀 Strong Trend Momentum!',
        desc: isKo
          ? `${moveLabel} 방향으로 홀딩이 유리합니다. 추세를 따라가세요.`
          : `Holding in ${moveLabel} direction is favorable. Follow the trend.`,
      };
    }
    return null;
  };

  const advice = result ? getStrategyAdvice() : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-amber-500/10 via-orange-500/5 to-transparent rounded-2xl" />
        <div className="relative p-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <span className="text-3xl">🏹</span>
            WolQuant AI: {isKo ? '양봉/음봉 연속성 시뮬레이터' : 'Candle Streak Simulator'}
          </h1>
          <p className="text-dark-400 mt-2">
            {isKo
              ? 'n개의 연속 양봉/음봉 이후 추세 지속 vs 반전 확률을 분석합니다'
              : 'Analyzes trend continuation vs reversal probability after n consecutive candles'}
          </p>
        </div>
      </div>

      {/* Controls */}
      <AnalysisControls
        useComplexPattern={useComplexPattern}
        condition1={condition1}
        condition2={condition2}
        minTotalBodyPct={minTotalBodyPct}
        candleMode={params.candle_mode ?? 'standard'}
        ema200Position={params.ema_200_position ?? null}
        isPending={mutation.isPending}
        isKo={isKo}
        onUseComplexPatternChange={setUseComplexPattern}
        onCondition1Change={setCondition1}
        onCondition2Change={setCondition2}
        onMinTotalBodyPctChange={setMinTotalBodyPct}
        onCandleModeChange={handleCandleModeChange}
        onEma200PositionChange={(value) =>
          setParams((prev) => ({ ...prev, ema_200_position: value }))
        }
        onRun={handleRun}
      />

      {/* Loading Skeleton */}
      {mutation.isPending && <SkeletonAnalysis />}

      {/* Results */}
      {!mutation.isPending &&
        result &&
        (result.total_cases > 0 || (result.mode === 'complex' && result.complex_pattern_analysis)) && (
          <div className="space-y-6 animate-in fade-in duration-500">
            <div className="card p-4 border border-sky-500/20 bg-sky-500/5">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="font-semibold text-sky-300">
                  {isKo ? '계산 기준' : 'Calculation Basis'}
                </span>
                <span className="px-2 py-1 rounded-full bg-sky-500/15 border border-sky-500/30 text-sky-200 font-medium">
                  {activeResultCandleModeLabel}
                </span>
              </div>
              <p className="mt-2 text-xs text-dark-300">
                {activeResultCandleMode === 'heikin_ashi'
                  ? isKo
                    ? '현재 결과는 연속봉과 패턴 판정에만 하이킨아시를 사용하고, RSI/ATR/Disparity/EMA 200은 원본 OHLC 기준으로 계산합니다.'
                    : 'This result uses Heikin-Ashi candles only for streak and pattern detection, while RSI/ATR/Disparity/EMA 200 stay on the original OHLC prices.'
                  : isKo
                    ? '현재 결과는 원본 OHLC 기준으로 연속봉과 지표를 계산합니다.'
                    : 'This result uses the original OHLC candles for both streak detection and derived indicators.'}
              </p>
            </div>

            {/* Statistics Summary */}
            <StatisticsSummary result={result} direction={params.direction} isKo={isKo} />

            {/* Volatility Data Grid */}
            <VolatilityDataGrid result={result} direction={params.direction} isKo={isKo} />

            {/* Interval Analysis Table */}
            <IntervalAnalysisTable result={result} isKo={isKo} currentValues={currentValues} />

            {/* Strategy Advice */}
            {advice && (
              <div className={`card p-6 border ${advice.bgColor}`}>
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${advice.color} text-white`}>
                    {advice.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white mb-1">{advice.title}</h3>
                    <p className="text-dark-300">{advice.desc}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

      {/* No Data */}
      {result && result.total_cases === 0 && (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold text-white mb-2">
            {result.filter_status?.status === 'filtered_out'
              ? isKo
                ? '필터에 의해 제거됨'
                : 'Filtered Out'
              : result.filter_status?.status === 'no_pattern_match'
                ? isKo
                  ? '패턴 매칭 없음'
                  : 'No Pattern Match'
                : isKo
                  ? '데이터 부족'
                  : 'Insufficient Data'}
          </h3>
          {result.filter_status?.status === 'filtered_out' ? (
            <div className="space-y-2 text-dark-300">
              <p>
                {isKo
                  ? '모든 매칭된 패턴이 필터 조건에 맞지 않습니다.'
                  : 'All matched patterns were removed by filters.'}
              </p>
              {result.filter_status.total_matches && (
                <p className="text-sm text-dark-400">
                  {isKo
                    ? `총 매칭: ${result.filter_status.total_matches}개`
                    : `Total matches: ${result.filter_status.total_matches}`}
                </p>
              )}
              <p className="text-sm text-dark-500 mt-4">
                {isKo
                  ? '필터 조건을 완화하거나 패턴을 조정해 보세요.'
                  : 'Try relaxing filter conditions or adjusting the pattern.'}
              </p>
            </div>
          ) : result.filter_status?.status === 'no_pattern_match' ? (
            <p className="text-dark-400">
              {isKo ? '패턴을 조정해 보세요.' : 'Try adjusting the pattern.'}
            </p>
          ) : (
            <p className="text-dark-400">{isKo ? 'n값을 조정해 보세요.' : 'Try adjusting n.'}</p>
          )}
        </div>
      )}

      {mutation.isError && (
        <div className="card p-6 bg-rose-500/10 border-rose-500/30">
          <div className="text-rose-400">
            {isKo ? '분석 중 오류가 발생했습니다.' : 'Error occurred.'}
          </div>
        </div>
      )}
    </div>
  );
}
