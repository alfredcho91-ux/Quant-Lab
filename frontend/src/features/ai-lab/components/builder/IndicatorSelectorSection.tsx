import type { IndicatorDef } from '../../types';

interface IndicatorSelectorSectionProps {
  isKo: boolean;
  indicators: IndicatorDef[];
  selectedIndicators: string[];
  onToggleIndicator: (indicatorId: string) => void;
}

export default function IndicatorSelectorSection({
  isKo,
  indicators,
  selectedIndicators,
  onToggleIndicator,
}: IndicatorSelectorSectionProps) {
  return (
    <div>
      <div className="text-sm text-dark-300 mb-2">
        {isKo ? '사용 지표' : 'Indicators'}
      </div>
      <div className="flex flex-wrap gap-2">
        {indicators.map((indicator) => {
          const active = selectedIndicators.includes(indicator.id);
          return (
            <button
              key={indicator.id}
              onClick={() => onToggleIndicator(indicator.id)}
              className={`px-3 py-1.5 rounded-full text-xs border transition ${
                active
                  ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-200'
                  : 'bg-dark-800 border-dark-600 text-dark-300 hover:bg-dark-700'
              }`}
            >
              {indicator.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
