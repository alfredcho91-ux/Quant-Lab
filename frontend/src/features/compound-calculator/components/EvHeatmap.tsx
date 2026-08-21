import { Fragment } from 'react';
import {
  calculateEvPerR,
  HEATMAP_RR_VALUES,
  HEATMAP_WIN_RATES,
} from '../calculations';

interface EvHeatmapProps {
  isKo: boolean;
  slippage: number;
  nearestWinRate: number;
  nearestRr: number;
}

export function EvHeatmap({ isKo, slippage, nearestWinRate, nearestRr }: EvHeatmapProps) {
  return (
    <div className="card min-w-0 p-4 sm:p-5">
      <div className="mb-4 text-xs font-semibold uppercase text-dark-400">
        {isKo ? '손익비 × 승률 기대값 히트맵' : 'R:R x Win Rate EV Heatmap'}
      </div>
      <div className="max-w-full overflow-x-auto">
        <div
          className="grid min-w-[520px] gap-1"
          style={{
            gridTemplateColumns: `44px repeat(${HEATMAP_WIN_RATES.length}, minmax(44px, 1fr))`,
          }}
        >
          <div />
          {HEATMAP_WIN_RATES.map((rate) => (
            <div
              key={rate}
              className={`rounded px-2 py-2 text-center text-xs text-dark-400 ${
                rate === nearestWinRate ? 'font-bold text-dark-100' : ''
              }`}
            >
              {rate}%
            </div>
          ))}
          {HEATMAP_RR_VALUES.map((rrValue) => (
            <Fragment key={rrValue}>
              <div
                className={`rounded px-2 py-2 text-center text-xs text-dark-400 ${
                  rrValue === nearestRr ? 'font-bold text-dark-100' : ''
                }`}
              >
                {rrValue}R
              </div>
              {HEATMAP_WIN_RATES.map((rate) => {
                const ev = calculateEvPerR(rate, rrValue, slippage);
                const isActive = rate === nearestWinRate && rrValue === nearestRr;
                const toneClass =
                  ev > 0.3
                    ? 'bg-bull text-dark-950'
                    : ev > 0.1
                      ? 'bg-emerald-500/70 text-white'
                      : ev > 0
                        ? 'bg-emerald-500/15 text-emerald-300'
                        : ev > -0.1
                          ? 'bg-warning/20 text-warning'
                          : 'bg-bear/25 text-red-200';

                return (
                  <div
                    key={`${rrValue}-${rate}`}
                    className={`flex aspect-square items-center justify-center rounded text-[11px] font-semibold ${toneClass} ${
                      isActive ? 'ring-2 ring-primary-300 ring-offset-2 ring-offset-dark-900' : ''
                    }`}
                  >
                    {ev >= 0 ? '+' : ''}
                    {ev.toFixed(2)}
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-3 text-[11px] text-dark-400">
        <span className="inline-flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-sm bg-bull" />
          EV &gt; 0.3
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-sm bg-emerald-500/70" />
          EV &gt; 0.1
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-sm bg-warning/20" />
          EV &gt; -0.1
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2.5 w-2.5 rounded-sm bg-bear/25" />
          EV &lt; -0.1
        </span>
      </div>
    </div>
  );
}
