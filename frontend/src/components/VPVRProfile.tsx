import type { VPVRData } from '../types';

export const CHART_BOTTOM_AXIS = 28;

function formatPrice(value: number): string {
  const digits = value >= 1_000 ? 0 : value >= 1 ? 2 : 4;
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export function VPVRProfile({
  vpvr,
  height,
  isKo,
  priceAxisMin,
  priceAxisMax,
}: {
  vpvr: VPVRData;
  height: number;
  isKo: boolean;
  priceAxisMin: number;
  priceAxisMax: number;
}) {
  const bins = vpvr.bins.slice().sort((a, b) => b.price_high - a.price_high);
  const maxVolume = Math.max(...bins.map((bin) => bin.volume_pct), 1);
  const plotHeight = Math.max(height - CHART_BOTTOM_AXIS, 1);
  const priceRange = Math.max(priceAxisMax - priceAxisMin, Number.EPSILON);
  const priceToY = (price: number) => ((priceAxisMax - price) / priceRange) * plotHeight;

  return (
    <aside className="relative hidden w-28 shrink-0 border-l border-dark-700 bg-dark-800/40 sm:block sm:w-36" style={{ height }}>
      <div className="absolute inset-x-0 top-0 z-10 px-2 py-1.5 text-[10px] font-semibold text-dark-300">
        VPVR
      </div>
      <div className="absolute inset-x-1 top-0" style={{ bottom: CHART_BOTTOM_AXIS }}>
        {bins.map((bin) => {
          if (bin.volume <= 0 || bin.price_high <= priceAxisMin || bin.price_low >= priceAxisMax) return null;
          const color = bin.is_poc ? 'bg-amber-400/85' : bin.is_value_area ? 'bg-primary-400/60' : 'bg-dark-500/50';
          const top = Math.max(0, priceToY(bin.price_high));
          const bottom = Math.min(plotHeight, priceToY(bin.price_low));
          const binHeight = Math.max(1, bottom - top);

          return (
            <div
              key={`${bin.price_low}-${bin.price_high}`}
              className="absolute right-0 flex items-center justify-end"
              style={{ top, height: binHeight, width: '100%' }}
              title={`${formatPrice(bin.price_low)} - ${formatPrice(bin.price_high)}`}
            >
              <div
                className={`min-w-1 ${color}`}
                style={{
                  height: `${Math.max(1, binHeight * 0.72)}px`,
                  width: `${Math.max(4, (bin.volume_pct / maxVolume) * 100)}%`,
                }}
              >
                {bin.is_poc && <span className="block px-1 text-right text-[9px] font-medium text-dark-950">POC</span>}
              </div>
            </div>
          );
        })}
      </div>
      <div className="absolute inset-x-0 bottom-0 h-7 border-t border-dark-700 px-2 py-1.5 text-[9px] text-dark-500">
        {isKo ? '노랑 POC · 파랑 VA' : 'Amber POC · Blue VA'}
      </div>
    </aside>
  );
}
