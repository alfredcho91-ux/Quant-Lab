import { BarChart3, FlaskConical, Gauge, Sigma } from 'lucide-react';
import MetricCard from '../../../components/MetricCard';
import type { ConditionalProbabilityAnalysis } from '../../../api/ai_lab';

interface ProbabilityAnalysisPanelProps {
  analysis: ConditionalProbabilityAnalysis;
  isKo: boolean;
}

function formatPct(value?: number | null): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'N/A';
  return `${value.toFixed(2)}%`;
}

function formatPValue(value?: number | null): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'N/A';
  if (value >= 0.001) return value.toFixed(3);
  return value.toExponential(2);
}

function clampPct(value?: number | null): number {
  if (typeof value !== 'number' || Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, value));
}

function pValueReliabilityLabel(
  level: 'Very High' | 'High' | 'Medium' | 'Low' | 'N/A' | undefined,
  isKo: boolean
): string {
  const key = level ?? 'N/A';
  if (isKo) {
    if (key === 'Very High') return '매우 높음';
    if (key === 'High') return '높음';
    if (key === 'Medium') return '보통';
    if (key === 'Low') return '낮음';
    return '판단 불가';
  }
  if (key === 'N/A') return 'N/A';
  return key;
}

function formatReliability(reliability: string, isKo: boolean): string {
  if (!isKo) return reliability;
  if (reliability === 'High Reliability') return '높은 신뢰도';
  if (reliability === 'Medium Reliability') return '중간 신뢰도';
  if (reliability === 'Low Reliability') return '낮은 신뢰도';
  return reliability;
}

function gatiMessage(score: number, isKo: boolean): string {
  if (score >= 75) return isKo ? '강한 통계 우위 구간' : 'Strong statistical edge';
  if (score >= 60) return isKo ? '우위가 확인되는 구간' : 'Moderate edge detected';
  if (score >= 45) return isKo ? '중립 구간 (필터 강화 권장)' : 'Neutral edge (tighten filters)';
  return isKo ? '우위 약함 (추가 필터 필요)' : 'Weak edge (add more filters)';
}

export default function ProbabilityAnalysisPanel({ analysis, isKo }: ProbabilityAnalysisPanelProps) {
  const probability = analysis.summary.probability_rate ?? null;
  const ciLower = analysis.summary.ci_lower ?? null;
  const ciUpper = analysis.summary.ci_upper ?? null;
  const center = analysis.confidence_band.center ?? probability ?? null;
  const gati = analysis.summary.gati_index ?? 0;
  const baseline = analysis.confidence_band.baseline ?? 50;
  const pReliability = pValueReliabilityLabel(analysis.summary.p_value_reliability, isKo);
  const targetLabel =
    analysis.condition.target_side === 'bull'
      ? (isKo ? '양봉' : 'Bull candle')
      : (isKo ? '음봉' : 'Bear candle');

  return (
    <div className="space-y-4 animate-slide-up">
      <div className="grid grid-cols-2 xl:grid-cols-5 gap-3">
        <MetricCard
          label={isKo ? '표본 수' : 'Samples'}
          value={analysis.summary.sample_count}
          icon={<FlaskConical className="w-4 h-4" />}
        />
        <MetricCard
          label={isKo ? '성공 수' : 'Success'}
          value={analysis.summary.success_count}
          trend="up"
          icon={<BarChart3 className="w-4 h-4" />}
        />
        <MetricCard
          label={isKo ? '다음봉 확률' : 'Next Candle Prob'}
          value={formatPct(probability)}
          trend={typeof probability === 'number' && probability >= 50 ? 'up' : 'down'}
          icon={<Sigma className="w-4 h-4" />}
        />
        <MetricCard
          label={isKo ? '통계 신뢰도' : 'Stat Reliability'}
          value={`${pReliability} (${formatPValue(analysis.summary.p_value)})`}
          trend={typeof analysis.summary.p_value === 'number' && analysis.summary.p_value < 0.05 ? 'up' : 'neutral'}
        />
        <MetricCard
          label="GATI"
          value={`${gati.toFixed(2)}`}
          trend={gati >= 60 ? 'up' : gati >= 45 ? 'neutral' : 'down'}
          icon={<Gauge className="w-4 h-4" />}
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3">
            {isKo ? '결과 분포' : 'Outcome Distribution'}
          </h3>
          <div className="space-y-3">
            {analysis.outcome_bars.map((bar) => (
              <div key={bar.key}>
                <div className="flex items-center justify-between text-xs text-dark-300 mb-1">
                  <span>
                    {isKo
                      ? (bar.key === 'success' ? '성공' : '실패')
                      : (bar.key === 'success' ? 'Success' : 'Failure')}
                  </span>
                  <span>{bar.count} ({bar.rate_pct.toFixed(2)}%)</span>
                </div>
                <div className="h-2 rounded-full bg-dark-700 overflow-hidden">
                  <div
                    className={`h-full ${bar.key === 'success' ? 'bg-bull' : 'bg-bear'}`}
                    style={{
                      width: bar.rate_pct <= 0 ? '0%' : `${Math.max(2, Math.min(100, bar.rate_pct))}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3">
            {isKo ? '신뢰구간 밴드 (95% Wilson)' : 'Confidence Band (95% Wilson)'}
          </h3>
          {center === null ? (
            <p className="text-xs text-dark-400">{isKo ? '표본 부족으로 계산 불가' : 'Not enough samples to estimate.'}</p>
          ) : (
            <div className="space-y-2">
              <div className="relative h-10 rounded-md bg-dark-800 border border-dark-700">
                <div className="absolute left-0 right-0 top-1/2 h-[2px] -translate-y-1/2 bg-dark-600" />
                <div className="absolute top-2 bottom-2 w-[1px] bg-dark-300/70" style={{ left: `${clampPct(baseline)}%` }} />
                {ciLower !== null && ciUpper !== null && (
                  <div
                    className="absolute top-1/2 h-[6px] -translate-y-1/2 rounded-full bg-cyan-400/80"
                    style={{
                      left: `${clampPct(ciLower)}%`,
                      width: `${Math.max(0.5, clampPct(ciUpper) - clampPct(ciLower))}%`,
                    }}
                  />
                )}
                <div
                  className="absolute top-1/2 w-2 h-2 -translate-y-1/2 -translate-x-1/2 rounded-full bg-white border border-cyan-300"
                  style={{ left: `${clampPct(center)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] text-dark-400">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
              <p className="text-xs text-dark-300">
                {isKo ? '중앙 확률' : 'Center'}: <span className="text-white">{formatPct(center)}</span> |
                {' '}
                CI: <span className="text-white">{formatPct(ciLower)} ~ {formatPct(ciUpper)}</span>
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="card p-4 space-y-2">
        <h3 className="text-sm font-semibold text-white">
          {isKo ? '상세 분석' : 'Detailed Analysis'}
        </h3>
        <p className="text-xs text-dark-300">
          {isKo ? '조건' : 'Condition'}: <span className="text-dark-100">{analysis.condition.condition_text}</span>
          {' '}| {analysis.coin} {analysis.interval} ({analysis.source})
        </p>
        <p className="text-xs text-dark-300">
          {isKo ? '타깃 이벤트' : 'Target event'}: <span className="text-dark-100">{targetLabel}</span>
          {' '}| {isKo ? '신뢰도' : 'Reliability'}: <span className="text-dark-100">{formatReliability(analysis.summary.reliability, isKo)}</span>
        </p>
        <p className="text-xs text-dark-300">
          {isKo ? '통계 신뢰도(p-value)' : 'Stat reliability (p-value)'}:
          {' '}<span className="text-dark-100">{pReliability}</span>
          {' '}({formatPValue(analysis.summary.p_value)})
        </p>
        <p className="text-xs text-dark-300">
          GATI = 45% Edge + 25% Significance + 20% Sample + 10% Reliability
        </p>
        <p className="text-xs text-primary-300">{gatiMessage(gati, isKo)}</p>
      </div>
    </div>
  );
}
