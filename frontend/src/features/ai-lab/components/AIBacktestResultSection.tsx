import Chart from '../../../components/LazyChart';
import MetricCard from '../../../components/MetricCard';
import TradesTable from '../../../components/TradesTable';
import type { BacktestResult } from '../../../types';
import type { Direction } from '../types';

interface AIBacktestResultSectionProps {
  isKo: boolean;
  result: BacktestResult | null;
  strategyDisplayName: string;
  selectedStrategyId: string;
  direction: Direction;
  runInterval: string;
}

export default function AIBacktestResultSection({
  isKo,
  result,
  strategyDisplayName,
  selectedStrategyId,
  direction,
  runInterval,
}: AIBacktestResultSectionProps) {
  if (!result) return null;

  return (
    <div className="space-y-4 animate-slide-up">
      <div className="card p-5">
        <div className="text-sm text-dark-400 mb-3">
          {isKo ? '실행 전략' : 'Executed strategy'}:{' '}
          <span className="text-white">{strategyDisplayName}</span> (
          {selectedStrategyId} · {direction} · {runInterval})
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard
            label={isKo ? '거래 수' : 'Trades'}
            value={result.summary.n_trades}
          />
          <MetricCard
            label={isKo ? '승률' : 'Win Rate'}
            value={`${result.summary.win_rate.toFixed(2)}%`}
            trend={result.summary.win_rate >= 50 ? 'up' : 'down'}
          />
          <MetricCard
            label={isKo ? '누적 수익률' : 'Total PnL'}
            value={`${result.summary.total_pnl >= 0 ? '+' : ''}${result.summary.total_pnl.toFixed(2)}%`}
            trend={result.summary.total_pnl >= 0 ? 'up' : 'down'}
          />
          <MetricCard
            label={isKo ? '청산 횟수' : 'Liquidations'}
            value={result.summary.liq_count ?? 0}
            trend={(result.summary.liq_count ?? 0) > 0 ? 'down' : 'neutral'}
          />
        </div>
      </div>

      <Chart
        data={result.chart_data}
        trades={result.trades}
        title={`${strategyDisplayName} • ${direction}`}
        showBB
        showMA
        height={560}
      />

      {result.trades.length > 0 ? (
        <TradesTable trades={result.trades} regimeStats={result.summary.regime_stats} />
      ) : (
        <div className="card p-5 text-sm text-dark-300">
          {isKo
            ? '해당 조건에서는 트레이드가 발생하지 않았습니다. 방향/전략/파라미터를 조정해보세요.'
            : 'No trades for this setup. Try changing direction/strategy/params.'}
        </div>
      )}
    </div>
  );
}
