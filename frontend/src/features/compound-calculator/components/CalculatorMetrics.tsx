import { formatCompactWon, formatPercent, metricToneClass } from '../calculations';
import type { Tone } from '../types';

function MetricTile({ label, value, tone }: { label: string; value: string; tone: Tone }) {
  return (
    <div className="min-w-0 rounded-lg border border-dark-700 bg-dark-800/70 p-4">
      <div className="text-xs text-dark-400">{label}</div>
      <div className={`mt-1 break-words font-mono text-xl font-bold ${metricToneClass[tone]}`}>
        {value}
      </div>
    </div>
  );
}

interface CalculatorMetricsProps {
  isKo: boolean;
  initialCapital: number;
  evPerR: number;
  finalCapital: number;
  roi: number;
  maxDrawdown: number;
  worstCaseDrawdown: number;
}

export function CalculatorMetrics({
  isKo,
  initialCapital,
  evPerR,
  finalCapital,
  roi,
  maxDrawdown,
  worstCaseDrawdown,
}: CalculatorMetricsProps) {
  return (
    <div className="grid min-w-0 gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <MetricTile
        label={isKo ? '기대값 (EV per R)' : 'EV per R'}
        value={`${evPerR >= 0 ? '+' : ''}${evPerR.toFixed(3)}R`}
        tone={evPerR > 0 ? 'positive' : evPerR < 0 ? 'negative' : 'warning'}
      />
      <MetricTile
        label={isKo ? '최종 자본 (복리)' : 'Final Capital'}
        value={`₩${formatCompactWon(finalCapital)}`}
        tone={finalCapital >= initialCapital ? 'positive' : 'negative'}
      />
      <MetricTile
        label={isKo ? '총 수익률' : 'Total ROI'}
        value={formatPercent(roi)}
        tone={roi >= 0 ? 'positive' : 'negative'}
      />
      <MetricTile
        label={isKo ? '최대 드로우다운' : 'Max Drawdown'}
        value={`${maxDrawdown.toFixed(1)}%`}
        tone={maxDrawdown < 20 ? 'positive' : maxDrawdown < 40 ? 'warning' : 'negative'}
      />
      <MetricTile
        label={isKo ? '최악 순서 MDD' : 'Worst-order MDD'}
        value={`${worstCaseDrawdown.toFixed(1)}%`}
        tone={
          worstCaseDrawdown < 20 ? 'positive' : worstCaseDrawdown < 40 ? 'warning' : 'negative'
        }
      />
    </div>
  );
}
