import type { IndicatorDef } from '../types';

function formatIndicatorParams(params: Record<string, number>): string {
  return Object.entries(params)
    .map(([key, value]) => `${key}:${value}`)
    .join(', ');
}

interface IndicatorCatalogProps {
  indicators: IndicatorDef[];
  selectedIndicatorIds: string[];
  showSelectionState: boolean;
  isKo: boolean;
}

export default function IndicatorCatalog({
  indicators,
  selectedIndicatorIds,
  showSelectionState,
  isKo,
}: IndicatorCatalogProps) {
  return (
    <div className="card p-5">
      <h3 className="font-semibold text-white mb-1">
        {isKo ? '참고용 인디케이터' : 'Reference Indicators'}
      </h3>
      <p className="text-xs text-dark-400 mb-3">
        {isKo
          ? 'AI 해석을 돕기 위한 참고 목록입니다. 실행 파라미터(JSON)는 별도 섹션에서 확인합니다.'
          : 'Reference list for AI interpretation. Executable JSON params are shown in a separate section.'}
      </p>
      <div className="space-y-2">
        {indicators.map((indicator) => {
          const active = selectedIndicatorIds.includes(indicator.id);
          return (
            <div
              key={`guide-${indicator.id}`}
              className={`rounded-lg border px-3 py-2 ${
                showSelectionState && active
                  ? 'border-cyan-500/40 bg-cyan-500/10'
                  : 'border-dark-700 bg-dark-800/40'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm font-medium text-white">{indicator.label}</div>
                {showSelectionState ? (
                  <div className={`text-[10px] ${active ? 'text-cyan-300' : 'text-dark-500'}`}>
                    {active ? (isKo ? '선택됨' : 'Selected') : (isKo ? '미선택' : 'Off')}
                  </div>
                ) : null}
              </div>
              <div className="text-xs text-dark-300 mt-1">
                {isKo ? indicator.descriptionKo : indicator.descriptionEn}
              </div>
              <div className="text-[11px] text-dark-500 mt-1 font-mono">
                params: {formatIndicatorParams(indicator.params)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
