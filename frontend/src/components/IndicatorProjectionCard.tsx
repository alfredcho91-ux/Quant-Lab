import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getIndicatorProjection } from '../api/stats';
import { Loader2, AlertCircle } from 'lucide-react';

interface IndicatorProjectionCardProps {
  coin: string;
  interval: string;
}

export function IndicatorProjectionCard({ coin, interval }: IndicatorProjectionCardProps) {
  const [targetStoch, setTargetStoch] = useState<number>(20);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['indicatorProjection', coin, interval],
    queryFn: () => getIndicatorProjection(coin, interval),
    enabled: !!coin && !!interval,
    staleTime: 60 * 1000, // 1 minute
  });

  if (isLoading) {
    return (
      <div className="card p-4 flex items-center justify-center min-h-[120px] mt-4">
        <Loader2 className="w-6 h-6 animate-spin text-primary-400" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card p-4 mt-4 border border-red-500/30 bg-red-500/5">
        <div className="text-red-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          예측 데이터를 불러오지 못했습니다. (API 에러)
        </div>
      </div>
    );
  }

  const { current_price, rsi_30_price, rsi_70_price, stoch_hh, stoch_ll } = data;

  let dynamicStochPrice = 0;
  if (stoch_hh !== undefined && stoch_ll !== undefined) {
    dynamicStochPrice = (targetStoch / 100) * (stoch_hh - stoch_ll) + stoch_ll;
  } else {
    if (targetStoch === 20) dynamicStochPrice = data.stoch_20_price;
    else if (targetStoch === 80) dynamicStochPrice = data.stoch_80_price;
  }

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

  const renderItem = (label: string, targetPrice: number) => {
    const diff = calculateDiff(targetPrice, current_price);
    // Green for positive (price needs to go up), Red for negative (price needs to go down)
    const colorClass = diff > 0 ? 'text-green-400' : 'text-red-400';
    
    return (
      <div className="flex flex-col items-center p-3 bg-dark-800/50 rounded-lg border border-dark-700 hover:border-dark-600 transition-colors">
        <span className="text-xs text-dark-400 mb-1.5">{label}</span>
        <span className="text-sm font-bold text-white mb-1 font-mono">{formatPrice(targetPrice)}</span>
        <span className={`text-xs font-mono font-medium ${colorClass} px-1.5 py-0.5 rounded bg-dark-900/50`}>
          {formatDiff(diff)}
        </span>
      </div>
    );
  };

  const renderDynamicStoch = () => {
    const diff = calculateDiff(dynamicStochPrice, current_price);
    const colorClass = diff > 0 ? 'text-green-400' : 'text-red-400';

    return (
      <div className="col-span-2 flex flex-col p-3 bg-dark-800/50 rounded-lg border border-dark-700 hover:border-dark-600 transition-colors">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-dark-400">Stoch Target: <span className="text-primary-400 font-bold">{targetStoch}</span></span>
          <input 
            type="range" 
            min="0" 
            max="100" 
            step="1"
            value={targetStoch} 
            onChange={(e) => setTargetStoch(Number(e.target.value))}
            className="w-24 h-1.5 bg-dark-600 rounded-lg appearance-none cursor-pointer accent-primary-500"
          />
        </div>
        <div className="flex justify-between items-end">
          <span className="text-sm font-bold text-white font-mono">{formatPrice(dynamicStochPrice)}</span>
          <span className={`text-xs font-mono font-medium ${colorClass} px-1.5 py-0.5 rounded bg-dark-900/50`}>
            {formatDiff(diff)}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="card p-4 mt-4 border-t border-dark-700/50">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="w-1 h-4 bg-primary-500 rounded-full"></span>
          Price Projections ({interval})
        </h2>
        <div className="text-xs text-dark-400">
          Current: <span className="text-white font-mono ml-1">{formatPrice(current_price)}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {renderItem('RSI 30', rsi_30_price)}
        {renderItem('RSI 70', rsi_70_price)}
        {renderDynamicStoch()}
      </div>
    </div>
  );
}
