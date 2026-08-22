import { Loader2, AlertCircle } from 'lucide-react';
import type { IndicatorProjection } from '../types';

interface IndicatorProjectionCardProps {
  interval: string;
  isKo: boolean;
  data?: IndicatorProjection;
  isLoading: boolean;
  isError: boolean;
}

export function IndicatorProjectionCard({ data, interval, isKo, isLoading, isError }: IndicatorProjectionCardProps) {
  if (isLoading) {
    return (
      <div className="card flex min-h-[120px] items-center justify-center p-4">
        <Loader2 className="w-6 h-6 animate-spin text-primary-400" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="card border border-red-500/30 bg-red-500/5 p-4">
        <div className="text-red-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {isKo ? '예측 데이터를 불러오지 못했습니다.' : 'Failed to load price projections.'}
        </div>
      </div>
    );
  }

  const { current_price, current_rsi, vwaps, rolling_vwaps, rsi_30_price, rsi_70_price } = data;
  const vwapLabels = {
    day: isKo ? '일간 VWAP' : 'Daily VWAP',
    week: isKo ? '주간 VWAP' : 'Weekly VWAP',
    month: isKo ? '월간 VWAP' : 'Monthly VWAP',
    quarter: isKo ? '분기 VWAP' : 'Quarterly VWAP',
    year: isKo ? '연간 VWAP' : 'Yearly VWAP',
  };

  const calculateDiff = (target: number, current: number) => {
    if (!current) return 0;
    return ((target - current) / current) * 100;
  };

  const formatPrice = (price: number) => {
    if (price < 1) return price.toFixed(6);
    if (price < 10) return price.toFixed(4);
    return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };
  
  const formatDiff = (diff: number) => `${diff > 0 ? '+' : ''}${diff.toFixed(2)}%`;

  const renderTargetRow = (key: string, label: string, targetPrice: number) => {
    const diff = calculateDiff(targetPrice, current_price);
    const colorClass = diff > 0 ? 'text-green-400' : 'text-red-400';
    
    return (
      <div key={key} className="grid grid-cols-[1fr_auto] items-center gap-2 rounded border border-dark-700 bg-dark-800/50 px-2.5 py-2">
        <span className="text-xs text-dark-400">{label}</span>
        <span className="text-right font-mono">
          <span className="text-sm font-bold text-white">{formatPrice(targetPrice)}</span>
          <span className={`ml-1.5 text-[11px] font-medium ${colorClass}`}>{formatDiff(diff)}</span>
        </span>
      </div>
    );
  };

  return (
    <div className="card p-3">
      <div className="flex items-start justify-between gap-2 mb-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="w-1 h-4 bg-primary-500 rounded-full"></span>
          {isKo ? `가격 예측 (${interval})` : `Price Projections (${interval})`}
        </h2>
        <div className="shrink-0 text-[11px] text-dark-400">
          {isKo ? '현재가' : 'Current'} <span className="text-white font-mono ml-1">{formatPrice(current_price)}</span>
        </div>
      </div>
      
      <div className="space-y-1.5">
        <div className="grid grid-cols-[1fr_auto] items-center gap-2 rounded border border-dark-700 bg-dark-800/50 px-2.5 py-2">
          <span className="text-xs text-dark-400">{isKo ? '현재 RSI(14)' : 'Current RSI(14)'}</span>
          <span className={`font-mono text-sm font-bold ${current_rsi != null && current_rsi >= 50 ? 'text-primary-400' : 'text-red-400'}`}>
            {current_rsi != null ? current_rsi.toFixed(1) : '—'}
          </span>
        </div>
        {renderTargetRow('rsi-30', 'RSI 30', rsi_30_price)}
        {renderTargetRow('rsi-70', 'RSI 70', rsi_70_price)}
        {vwaps.map(({ anchor, value }) =>
          value != null ? renderTargetRow(`vwap-${anchor}`, vwapLabels[anchor], value) : null,
        )}
        {rolling_vwaps.map(({ window, value }) =>
          value != null ? renderTargetRow(`rolling-vwap-${window}`, `VWAP(${window})`, value) : null,
        )}
      </div>
    </div>
  );
}
