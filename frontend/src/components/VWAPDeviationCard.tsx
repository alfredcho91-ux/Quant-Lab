import { AlertCircle, Loader2 } from 'lucide-react';

import type { IndicatorProjection } from '../types';

const ZONE_LABELS = {
  center: { ko: 'VWAP 중심권', en: 'VWAP center range' },
  upper_expansion: { ko: '상단 확장', en: 'Upper expansion' },
  strong_upper: { ko: '강한 상단 이격', en: 'Strong upper extension' },
  extreme_upper: { ko: '극단적 상단 이격', en: 'Extreme upper extension' },
  lower_expansion: { ko: '하단 확장', en: 'Lower expansion' },
  strong_lower: { ko: '강한 하단 이격', en: 'Strong lower extension' },
  extreme_lower: { ko: '극단적 하단 이격', en: 'Extreme lower extension' },
} as const;

function formatPrice(value: number): string {
  if (value < 1) return value.toFixed(6);
  if (value < 10) return value.toFixed(4);
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function VWAPDeviationCard({
  interval,
  data,
  isKo,
  isLoading,
  isError,
}: {
  interval: string;
  data?: IndicatorProjection;
  isKo: boolean;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) return <div className="card flex min-h-[110px] items-center justify-center p-4"><Loader2 className="h-5 w-5 animate-spin text-primary-400" /></div>;
  const deviation = data?.vwap_deviation;
  if (isError || !deviation) return <div className="card border border-red-500/30 bg-red-500/5 p-4 text-xs text-red-400"><AlertCircle className="mr-1 inline h-3.5 w-3.5" />{isKo ? 'VWAP 편차를 불러오지 못했습니다.' : 'VWAP deviation is unavailable.'}</div>;

  const sigma = deviation.sigma;
  const zone = ZONE_LABELS[deviation.zone as keyof typeof ZONE_LABELS];
  return (
    <div className="card p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-dark-300">{interval.toUpperCase()} {isKo ? '월간 VWAP' : 'Monthly VWAP'}</span>
        <span className="font-mono text-base font-bold text-primary-300">{sigma == null ? '—' : `${sigma >= 0 ? '+' : ''}${sigma.toFixed(2)}σ`}</span>
      </div>
      <div className="mt-1 text-[11px] text-dark-500">{zone?.[isKo ? 'ko' : 'en'] ?? deviation.zone}</div>
      <div className="mt-3 grid grid-cols-3 gap-1 text-[10px] text-dark-500">
        {[1, 2, 3].map((band) => <span key={band}>{band}σ <strong className="ml-0.5 font-mono text-dark-200">{formatPrice(deviation.bands[String(band)])}</strong></span>)}
      </div>
    </div>
  );
}
