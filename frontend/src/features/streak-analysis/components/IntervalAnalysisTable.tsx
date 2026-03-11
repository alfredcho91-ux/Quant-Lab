/**
 * 구간별 승률 분석 테이블 컴포넌트
 * 조건부 분해(구간별 승률) 표
 */
import { Activity } from 'lucide-react';
import type {
  ConditionalHeatmap,
  ConditionalHeatmapCell,
  IntervalProbability,
  StreakAnalysisResult,
} from '../../../types';

interface IntervalAnalysisTableProps {
  result: StreakAnalysisResult;
  isKo: boolean;
}

function getHeatmapCellClass(cell: ConditionalHeatmapCell | undefined): string {
  if (!cell || cell.rate == null || cell.sample_size === 0) {
    return 'bg-dark-700/40 border-dark-700 text-dark-500';
  }

  const samplePenalty = cell.sample_size < 10 ? ' opacity-70' : '';
  if (cell.rate >= 65) {
    return `bg-primary-500/25 border-primary-500/35 text-primary-200${samplePenalty}`;
  }
  if (cell.rate >= 55) {
    return `bg-primary-500/12 border-primary-500/25 text-primary-100${samplePenalty}`;
  }
  if (cell.rate >= 45) {
    return `bg-dark-700/70 border-dark-600 text-dark-300${samplePenalty}`;
  }
  if (cell.rate >= 35) {
    return `bg-rose-500/12 border-rose-500/25 text-rose-100${samplePenalty}`;
  }
  return `bg-rose-500/25 border-rose-500/35 text-rose-200${samplePenalty}`;
}

function IntervalBlock({
  title,
  prefixIcon,
  data,
  isKo,
}: {
  title: string;
  prefixIcon: string;
  data: Record<string, IntervalProbability>;
  isKo: boolean;
}) {
  return (
    <div className="bg-dark-800 rounded-xl p-4">
      <div className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
        {prefixIcon} {title}
        <span className="text-dark-500 text-xs font-normal">
          ({Object.keys(data).length}
          {isKo ? '개 구간 테스트' : ' intervals tested'})
        </span>
      </div>
      <div className="space-y-2">
        {Object.entries(data).map(([interval, row]) => {
          const isHighProb = row.rate >= 60 && row.sample_size >= 10;
          const isNominalSig = row.is_significant;
          const isBonfSig = row.bonferroni?.is_significant_after_correction;
          return (
            <div
              key={interval}
              className={`rounded-lg px-3 py-2 ${
                isHighProb && isBonfSig
                  ? 'bg-primary-500/20 border border-primary-500/30'
                  : isHighProb
                    ? 'bg-amber-500/10 border border-amber-500/20'
                    : 'bg-dark-700/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-dark-300 text-sm font-mono">{interval}</span>
                <div className="flex items-center gap-2">
                  <span
                    className={`font-bold ${
                      isHighProb
                        ? 'text-primary-400'
                        : row.rate >= 50
                          ? 'text-amber-400'
                          : 'text-rose-400'
                    }`}
                  >
                    {row.rate}%
                  </span>
                  <span className="text-dark-500 text-xs">
                    ({row.sample_size}
                    {isKo ? '건' : ''})
                  </span>
                  {isHighProb && isBonfSig && <span className="text-primary-400 text-xs">✓✓</span>}
                  {isHighProb && isNominalSig && !isBonfSig && (
                    <span className="text-amber-400 text-xs">✓</span>
                  )}
                </div>
              </div>
              <div className="mt-1.5 flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-dark-600 rounded-full relative">
                  <div
                    className="absolute h-full bg-dark-400 rounded-full"
                    style={{
                      left: `${Math.max(0, row.ci_lower)}%`,
                      width: `${Math.min(100, row.ci_upper) - Math.max(0, row.ci_lower)}%`,
                    }}
                  />
                  <div
                    className="absolute w-1.5 h-1.5 bg-white rounded-full top-0"
                    style={{ left: `${row.rate}%`, transform: 'translateX(-50%)' }}
                  />
                </div>
                <span className="text-dark-500 text-xs whitespace-nowrap">
                  [{row.ci_lower}~{row.ci_upper}]
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function HeatmapBlock({ heatmap, isKo }: { heatmap: ConditionalHeatmap; isKo: boolean }) {
  const xBins = heatmap.x_bins ?? [];
  const yBins = heatmap.y_bins ?? [];
  if (xBins.length === 0 || yBins.length === 0) {
    return null;
  }

  return (
    <div className="bg-dark-800 rounded-xl p-4">
      <div className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
        🧩 {isKo ? '조건 결합 히트맵' : 'Condition Heatmap'} ({heatmap.x_label} × {heatmap.y_label})
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px] border-separate border-spacing-1 text-xs">
          <thead>
            <tr>
              <th className="text-left text-dark-400 font-medium px-2 py-1 whitespace-nowrap">
                {heatmap.y_label} \ {heatmap.x_label}
              </th>
              {xBins.map((xBin) => (
                <th key={xBin} className="text-center text-dark-400 font-medium px-2 py-1 whitespace-nowrap">
                  {xBin}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yBins.map((yBin) => (
              <tr key={yBin}>
                <th className="text-left text-dark-400 font-medium px-2 py-2 whitespace-nowrap">{yBin}</th>
                {xBins.map((xBin) => {
                  const cell = heatmap.cells?.[yBin]?.[xBin];
                  return (
                    <td
                      key={`${yBin}-${xBin}`}
                      className={`relative rounded border px-2 py-2 text-center align-middle ${getHeatmapCellClass(
                        cell
                      )}`}
                    >
                      {cell?.bonferroni_significant && (
                        <span className="absolute right-1 top-1 text-[10px] text-primary-300">✓✓</span>
                      )}
                      {!cell?.bonferroni_significant && cell?.is_significant && (
                        <span className="absolute right-1 top-1 text-[10px] text-amber-300">✓</span>
                      )}
                      <div className="font-semibold leading-tight">
                        {cell?.rate == null ? '—' : `${cell.rate.toFixed(1)}%`}
                      </div>
                      <div className="text-[10px] text-dark-400 leading-tight">
                        n={cell?.sample_size ?? 0}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-xs text-dark-500">
        {isKo
          ? `총 ${heatmap.total_samples} 샘플, 테스트 셀 ${heatmap.tested_cells}, 다중비교 통과 셀 ${heatmap.significant_cells}`
          : `${heatmap.total_samples} samples, ${heatmap.tested_cells} tested cells, ${heatmap.significant_cells} Bonferroni-significant cells`}
      </div>
    </div>
  );
}

export default function IntervalAnalysisTable({ result, isKo }: IntervalAnalysisTableProps) {
  const rsiByInterval = result.rsi_by_interval;
  const dispByInterval =
    result.disp_by_interval ?? result.complex_pattern_analysis?.disp_by_interval;
  const atrByInterval =
    result.atr_by_interval ?? result.complex_pattern_analysis?.atr_by_interval;
  const rsiAtrHeatmap =
    result.rsi_atr_heatmap ?? result.complex_pattern_analysis?.rsi_atr_heatmap;

  const hasRSI = !!rsiByInterval && Object.keys(rsiByInterval).length > 0;
  const hasDisp = !!dispByInterval && Object.keys(dispByInterval).length > 0;
  const hasAtr = !!atrByInterval && Object.keys(atrByInterval).length > 0;
  const hasHeatmap =
    !!rsiAtrHeatmap &&
    Array.isArray((rsiAtrHeatmap as { x_bins?: unknown[] }).x_bins) &&
    Array.isArray((rsiAtrHeatmap as { y_bins?: unknown[] }).y_bins) &&
    (rsiAtrHeatmap as { x_bins: unknown[] }).x_bins.length > 0 &&
    (rsiAtrHeatmap as { y_bins: unknown[] }).y_bins.length > 0;

  if (!hasRSI && !hasDisp && !hasAtr && !hasHeatmap) {
    return null;
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Activity className="w-5 h-5 text-green-400" />
        {isKo ? '📊 조건부 분해 분석 (95% 신뢰구간)' : '📊 Conditional Breakdown (95% CI)'}
      </h3>
      <p className="text-dark-400 text-sm mb-4">
        {isKo
          ? '패턴 완성 시점의 조건별(지표 구간별) 다음 봉 양봉 확률. ⚠️ 다중비교 보정 적용됨'
          : 'Next-candle green probability by condition buckets. ⚠️ Bonferroni correction applied'}
      </p>

      <div className="grid grid-cols-1 gap-4">
        {hasRSI && (
          <IntervalBlock
            title={isKo ? '패턴 완성 시점 RSI 구간' : 'RSI at Pattern Completion'}
            prefixIcon="📈"
            data={rsiByInterval}
            isKo={isKo}
          />
        )}
        {hasDisp && dispByInterval && (
          <IntervalBlock
            title={isKo ? '패턴 완성 시점 이격도(Disparity) 구간' : 'Disparity at Pattern Completion'}
            prefixIcon="📏"
            data={dispByInterval}
            isKo={isKo}
          />
        )}
        {hasAtr && atrByInterval && (
          <IntervalBlock
            title={isKo ? '패턴 완성 시점 ATR% 구간' : 'ATR% at Pattern Completion'}
            prefixIcon="🌊"
            data={atrByInterval}
            isKo={isKo}
          />
        )}
        {hasHeatmap && rsiAtrHeatmap && <HeatmapBlock heatmap={rsiAtrHeatmap} isKo={isKo} />}
      </div>

      <div className="mt-3 pt-3 border-t border-dark-700 flex flex-wrap gap-3 text-xs">
        <span className="text-primary-400">✓✓ {isKo ? '다중비교 통과' : 'Bonferroni sig'}</span>
        <span className="text-amber-400">{isKo ? '단순 유의' : 'Nominal sig'} ✓</span>
      </div>

      {/* 통계 해석 안내 */}
      <div className="mt-4 p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl">
        <div className="text-blue-400 font-semibold mb-2">
          📖 {isKo ? '통계 해석 가이드' : 'Statistical Guide'}
        </div>
        <ul className="text-dark-400 text-sm space-y-1">
          <li>
            • <span className="text-primary-400">✓✓</span>:{' '}
            {isKo
              ? 'Bonferroni 보정 후에도 유의 (다중비교 고려) - 가장 신뢰도 높음'
              : 'Significant after Bonferroni - highest confidence'}
          </li>
          <li>
            • <span className="text-amber-400">✓</span>:{' '}
            {isKo
              ? 'p<0.05 유의하나, 다중비교 보정 미통과 - 참고만'
              : 'p<0.05 but not Bonferroni significant - use with caution'}
          </li>
          <li>
            •{' '}
            {isKo
              ? '샘플 30개 이상일 때 신뢰구간이 가장 안정적'
              : 'CI most stable with 30+ samples'}
          </li>
        </ul>
      </div>
    </div>
  );
}
