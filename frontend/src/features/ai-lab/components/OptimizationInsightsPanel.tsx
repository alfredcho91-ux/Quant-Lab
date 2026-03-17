import { Compass, LineChart, TrendingDown, TrendingUp } from 'lucide-react';
import MetricCard from '../../../components/MetricCard';
import type { OptimizationCharacteristicsAnalysis } from '../../../api/ai_lab';

interface OptimizationInsightsPanelProps {
  analysis: OptimizationCharacteristicsAnalysis;
  isKo: boolean;
}

function formatSignedPct(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return 'N/A';
  }
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function formatSignedPoints(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return 'N/A';
  }
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%p`;
}

function metricTrend(value: number | null | undefined): 'up' | 'down' | 'neutral' {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return 'neutral';
  }
  if (value > 0) {
    return 'up';
  }
  if (value < 0) {
    return 'down';
  }
  return 'neutral';
}

function directionLabel(direction: 'higher_better' | 'lower_better', isKo: boolean): string {
  if (isKo) {
    return direction === 'higher_better' ? '값이 높을수록 유리' : '값이 낮을수록 유리';
  }
  return direction === 'higher_better' ? 'Higher is better' : 'Lower is better';
}

export default function OptimizationInsightsPanel({ analysis, isKo }: OptimizationInsightsPanelProps) {
  const summary = analysis.summary;
  const pnlDelta =
    typeof summary.top_avg_oos_pnl === 'number' && typeof summary.bottom_avg_oos_pnl === 'number'
      ? summary.top_avg_oos_pnl - summary.bottom_avg_oos_pnl
      : null;
  const winRateDelta =
    typeof summary.top_avg_oos_win_rate === 'number' && typeof summary.bottom_avg_oos_win_rate === 'number'
      ? summary.top_avg_oos_win_rate - summary.bottom_avg_oos_win_rate
      : null;

  return (
    <div className="card p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Compass className="w-4 h-4 text-cyan-300" />
            {isKo ? '상승/하락 파라미터 특징 역산' : 'Rising/Falling Parameter Characteristics'}
          </h3>
          <p className="text-xs text-dark-400 mt-1">
            {isKo
              ? '최적화 상위/하위 결과 버킷을 비교해 성과 차이를 크게 만든 파라미터를 자동 추출했습니다.'
              : 'Top vs bottom optimization buckets were compared to extract parameters with the largest impact.'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-5 gap-3">
        <MetricCard
          label={isKo ? '탐색 횟수' : 'Trials'}
          value={summary.trial_count}
          icon={<LineChart className="w-4 h-4" />}
        />
        <MetricCard
          label={isKo ? '상위 OOS 수익률' : 'Top OOS PnL'}
          value={formatSignedPct(summary.top_avg_oos_pnl)}
          trend={metricTrend(summary.top_avg_oos_pnl)}
          icon={<TrendingUp className="w-4 h-4" />}
        />
        <MetricCard
          label={isKo ? '하위 OOS 수익률' : 'Bottom OOS PnL'}
          value={formatSignedPct(summary.bottom_avg_oos_pnl)}
          trend={metricTrend(summary.bottom_avg_oos_pnl)}
          icon={<TrendingDown className="w-4 h-4" />}
        />
        <MetricCard
          label={isKo ? '수익률 격차' : 'PnL Gap'}
          value={formatSignedPct(pnlDelta)}
          trend={metricTrend(pnlDelta)}
        />
        <MetricCard
          label={isKo ? '승률 격차' : 'Win Rate Gap'}
          value={formatSignedPoints(winRateDelta)}
          trend={metricTrend(winRateDelta)}
        />
      </div>

      <div className="space-y-3">
        <h4 className="text-xs uppercase tracking-wide text-dark-400">
          {isKo ? '핵심 파라미터 하이라이트' : 'Key Parameter Highlights'}
        </h4>
        {analysis.highlights.map((item) => (
          <div key={item.param} className="rounded-lg border border-dark-700 bg-dark-800/70 p-3 space-y-2">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-white">{item.label}</p>
              <p className="text-xs text-cyan-300">{directionLabel(item.direction, isKo)}</p>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="text-dark-300">
                {isKo ? '상위 평균' : 'Top mean'}: <span className="text-white">{item.top_mean}</span>
              </div>
              <div className="text-dark-300">
                {isKo ? '하위 평균' : 'Bottom mean'}: <span className="text-white">{item.bottom_mean}</span>
              </div>
            </div>
            <div className="space-y-1">
              <div className="h-2 rounded-full bg-dark-700 overflow-hidden">
                <div
                  className="h-full rounded-full bg-cyan-400"
                  style={{ width: `${Math.max(4, Math.min(100, item.effect_pct))}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] text-dark-400">
                <span>{item.interpretation}</span>
                <span>{item.effect_pct.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
