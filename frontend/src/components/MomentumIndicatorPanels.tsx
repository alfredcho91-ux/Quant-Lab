import { Activity, Gauge } from 'lucide-react';
import type { TrendIndicatorsResult } from '../types';
import { formatNum } from '../utils/format';
import { StochMiniChart } from './StochMiniChart';

export function MomentumIndicatorPanels({
  isKo,
  payload,
}: {
  isKo: boolean;
  payload: TrendIndicatorsResult;
}) {
  const { latest, series } = payload;
  const histDirectionLabel =
    latest.macd_hist_direction === 'rising'
      ? isKo
        ? '히스토그램 상승'
        : 'Histogram Rising'
      : latest.macd_hist_direction === 'falling'
        ? isKo
          ? '히스토그램 하락'
          : 'Histogram Falling'
        : isKo
          ? '히스토그램 보합'
          : 'Histogram Flat';

  return (
    <div className="flex min-w-0 flex-col gap-3">
      <section className="card min-w-0 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Activity className="h-4 w-4 text-primary-400" />
            MACD (12, 26, 9)
          </div>
          <span
            className={`rounded-md border px-2 py-1 text-[11px] font-medium ${
              latest.macd_hist_direction === 'rising'
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                : latest.macd_hist_direction === 'falling'
                  ? 'border-red-500/30 bg-red-500/10 text-red-300'
                  : 'border-dark-600 bg-dark-800 text-dark-300'
            }`}
          >
            {histDirectionLabel}
          </span>
        </div>
        <div className="mb-2 grid grid-cols-3 gap-2 text-xs">
          <div>
            <div className="text-dark-500">Line</div>
            <div className="font-mono text-primary-300">{formatNum(latest.macd, 3)}</div>
          </div>
          <div>
            <div className="text-dark-500">Signal</div>
            <div className="font-mono text-amber-400">{formatNum(latest.macd_signal, 3)}</div>
          </div>
          <div>
            <div className="text-dark-500">Histogram</div>
            <div
              className={`font-mono ${
                latest.macd_hist != null && latest.macd_hist >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {formatNum(latest.macd_hist, 3)}
            </div>
          </div>
        </div>
        <StochMiniChart
          tk={series.macd?.t ?? []}
          vk={series.macd?.v ?? []}
          td={series.macd_signal?.t}
          vd={series.macd_signal?.v}
          yRefs={[0]}
          showCrossLabels
          height={112}
        />
      </section>

      <section className="card min-w-0 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Gauge className="h-4 w-4 text-primary-400" />
            Stoch RSI (14, 14, 3, 3)
          </div>
        </div>
        <div className="mb-2 flex gap-5 text-xs">
          <div>
            <span className="text-dark-500">K </span>
            <span className="font-mono text-primary-300">{formatNum(latest.stoch_rsi_k, 1)}</span>
          </div>
          <div>
            <span className="text-dark-500">D </span>
            <span className="font-mono text-amber-400">{formatNum(latest.stoch_rsi_d, 1)}</span>
          </div>
        </div>
        <StochMiniChart
          tk={series.stoch_rsi_k?.t ?? []}
          vk={series.stoch_rsi_k?.v ?? []}
          td={series.stoch_rsi_d?.t}
          vd={series.stoch_rsi_d?.v}
          yRefs={[20, 80]}
          showCrossLabels
          height={112}
        />
      </section>
    </div>
  );
}
