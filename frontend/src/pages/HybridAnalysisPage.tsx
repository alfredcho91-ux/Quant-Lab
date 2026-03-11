import { usePageCommon } from '../hooks/usePageCommon';
import { BarChart2, AlertCircle } from 'lucide-react';
import { SkeletonAnalysis } from '../components/Skeleton';
import HybridParamsForm from '../features/hybrid-analysis/components/HybridParamsForm';
import HybridLiveResult from '../features/hybrid-analysis/components/HybridLiveResult';
import HybridBacktestResult from '../features/hybrid-analysis/components/HybridBacktestResult';
import { useHybridAnalysis } from '../features/hybrid-analysis/hooks/useHybridAnalysis';

export default function HybridAnalysisPage() {
  const {
    selectedCoin,
    selectedInterval,
    setSelectedCoin,
    setSelectedInterval,
    backtestParams,
    setBacktestParams,
    handleRunBacktest,
    handleRunLiveMode,
    backtestResult,
    liveModeResult,
    isLoading,
    backtestMutation,
    liveModeMutation,
  } = useHybridAnalysis();

  const { isKo } = usePageCommon();

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

      <HybridParamsForm
        selectedCoin={selectedCoin}
        setSelectedCoin={setSelectedCoin}
        selectedInterval={selectedInterval}
        setSelectedInterval={setSelectedInterval}
        backtestParams={backtestParams}
        setBacktestParams={setBacktestParams}
        onRunBacktest={handleRunBacktest}
        onRunLiveMode={handleRunLiveMode}
        isBacktestLoading={backtestMutation.isPending}
        isLiveModeLoading={liveModeMutation.isPending}
        isBacktestDisabled={isLoading}
      />

      {/* Live Mode Results */}
      {liveModeResult && liveModeResult.success && (
        <HybridLiveResult result={liveModeResult} isKo={isKo} />
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

      {/* Loading */}
      {isLoading && <SkeletonAnalysis />}

      {/* Backtest Results */}
      {backtestResult && backtestResult.success && (
        <HybridBacktestResult result={backtestResult} isKo={isKo} />
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
