// Backtest Page Component
import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Play, Loader2, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import {
  useBacktestParams,
  useLanguage,
  useSelectedCoin,
  useUpdateBacktestParams,
} from '../store/useStore';
import { getLabels } from '../store/labels';
import { getStrategies, getTimeframes, runBacktest } from '../api/client';
import Chart from '../components/LazyChart';
import MetricCard from '../components/MetricCard';
import ParamsPanel from '../components/ParamsPanel';
import StrategyExplainer from '../components/StrategyExplainer';
import TradesTable from '../components/TradesTable';
import DataSourceToggle from '../components/DataSourceToggle';
import type { BacktestResult, Strategy } from '../types';

export default function BacktestPage() {
  const language = useLanguage();
  const selectedCoin = useSelectedCoin();
  const backtestParams = useBacktestParams();
  const updateBacktestParams = useUpdateBacktestParams();
  const labels = getLabels(language);
  const [result, setResult] = useState<BacktestResult | null>(null);

  // Fetch strategies
  const { data: strategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: getStrategies,
    staleTime: Infinity,
  });

  // Fetch timeframes
  const { data: timeframes } = useQuery({
    queryKey: ['timeframes', selectedCoin],
    queryFn: () => getTimeframes(selectedCoin),
    staleTime: 60000,
  });

  // Backtest mutation
  const backtestMutation = useMutation({
    mutationFn: runBacktest,
    onSuccess: (data) => {
      if (data) {
        setResult(data);
      }
    },
  });

  const handleRunBacktest = useCallback(() => {
    backtestMutation.mutate({
      ...backtestParams,
      coin: selectedCoin,
    });
  }, [backtestMutation, backtestParams, selectedCoin]);

  const selectedStrategy = strategies?.find(
    (s: Strategy) => s.id === backtestParams.strategy_id
  );
  const strategyName =
    language === 'ko' ? selectedStrategy?.name_ko : selectedStrategy?.name_en;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">
            🚀 {labels.title_backtest.replace('{coin}', selectedCoin)}
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {language === 'ko'
              ? '8개 전략을 선택하고 백테스트를 실행해보세요.'
              : 'Select from 8 strategies and run backtests.'}
          </p>
        </div>
        <button
          onClick={handleRunBacktest}
          disabled={backtestMutation.isPending}
          className="btn btn-primary flex items-center gap-2 px-6"
        >
          {backtestMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Play className="w-5 h-5" />
          )}
          {labels.run_backtest}
        </button>
      </div>

      {/* Strategy & Direction Selection */}
      <div className="card p-4">
        <h3 className="text-lg font-semibold mb-4">{labels.choose}</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Interval */}
          <div className="space-y-2">
            <label className="text-xs text-dark-400 uppercase">{labels.interval}</label>
            <select
              value={backtestParams.interval}
              onChange={(e) => updateBacktestParams({ interval: e.target.value })}
              className="w-full"
            >
              {timeframes?.all.map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </div>

          {/* Strategy */}
          <div className="space-y-2">
            <label className="text-xs text-dark-400 uppercase">{labels.strategy}</label>
            <select
              value={backtestParams.strategy_id}
              onChange={(e) => updateBacktestParams({ strategy_id: e.target.value })}
              className="w-full"
            >
              {strategies?.map((s: Strategy) => (
                <option key={s.id} value={s.id}>
                  {language === 'ko' ? s.name_ko : s.name_en}
                </option>
              ))}
            </select>
          </div>

          {/* Direction */}
          <div className="space-y-2">
            <label className="text-xs text-dark-400 uppercase">{labels.direction}</label>
            <div className="flex gap-2">
              <button
                onClick={() => updateBacktestParams({ direction: 'Long' })}
                className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-all ${
                  backtestParams.direction === 'Long'
                    ? 'bg-bull/20 text-bull border border-bull/30'
                    : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                Long
              </button>
              <button
                onClick={() => updateBacktestParams({ direction: 'Short' })}
                className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-all ${
                  backtestParams.direction === 'Short'
                    ? 'bg-bear/20 text-bear border border-bear/30'
                    : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
                }`}
              >
                <TrendingDown className="w-4 h-4" />
                Short
              </button>
            </div>
          </div>

          {/* Data Source */}
          <div className="space-y-2">
            <DataSourceToggle />
            {timeframes?.csv && timeframes.csv.length > 0 && (
              <p className="text-xs text-dark-500">
                {labels.price_help}
                {timeframes.csv.join(', ')}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Strategy Explainer */}
      {backtestParams.strategy_id && (
        <StrategyExplainer strategyId={backtestParams.strategy_id} />
      )}

      {/* Chart */}
      {result && result.chart_data.length > 0 && (
        <Chart
          data={result.chart_data}
          trades={result.trades}
          title={`${strategyName} • ${backtestParams.direction}`}
          showBB={true}
          showMA={true}
          height={600}
        />
      )}

      {/* Results Summary */}
      {result && (
        <div className="space-y-4 animate-slide-up">
          <h3 className="text-lg font-semibold">{labels.summary}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label={labels.trades}
              value={`${result.summary.n_trades}회`}
            />
            <MetricCard
              label={labels.winrate}
              value={`${result.summary.win_rate.toFixed(2)}%`}
              trend={result.summary.win_rate >= 50 ? 'up' : 'down'}
            />
            <MetricCard
              label={labels.cumret}
              value={`${result.summary.total_pnl >= 0 ? '+' : ''}${result.summary.total_pnl.toFixed(1)}%`}
              trend={result.summary.total_pnl >= 0 ? 'up' : 'down'}
            />
            <MetricCard
              label={labels.liqcnt}
              value={`${result.summary.liq_count}회`}
              icon={result.summary.liq_count > 0 ? <AlertTriangle className="w-4 h-4 text-bear" /> : null}
              trend={result.summary.liq_count > 0 ? 'down' : 'neutral'}
            />
          </div>
        </div>
      )}

      {/* No Data Warning */}
      {result && result.trades.length === 0 && (
        <div className="card p-6 text-center">
          <AlertTriangle className="w-12 h-12 text-warning mx-auto mb-3" />
          <p className="text-dark-300">{labels.no_data}</p>
        </div>
      )}

      {/* Parameters Panel */}
      <ParamsPanel />

      {/* Trades Table */}
      {result && result.trades.length > 0 && (
        <TradesTable
          trades={result.trades}
          regimeStats={result.summary.regime_stats}
        />
      )}
    </div>
  );
}
