import { HybridBacktestResult } from '../../../types/hybrid';

interface HybridBacktestResultProps {
  result: HybridBacktestResult;
  isKo: boolean;
}

export default function HybridBacktestResultComponent({ result, isKo }: HybridBacktestResultProps) {
  if (!result.success) return null;

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-white mb-4">
        {isKo ? '백테스팅 결과' : 'Backtest Results'}
      </h2>
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-4">
          <div>
            <div className="text-sm text-dark-400">{isKo ? '거래 수' : 'Trades'}</div>
            <div className="text-xl font-bold">{result.summary.n_trades}</div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? '승률' : 'Win Rate'}</div>
            <div className={`text-xl font-bold ${result.summary.win_rate > 50 ? 'text-primary-400' : 'text-red-400'}`}>
              {result.summary.win_rate.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? '총 수익률' : 'Total PnL'}</div>
            <div className={`text-xl font-bold ${result.summary.total_pnl > 0 ? 'text-primary-400' : 'text-red-400'}`}>
              {result.summary.total_pnl > 0 ? '+' : ''}
              {result.summary.total_pnl.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? '평균 수익률' : 'Avg PnL'}</div>
            <div className={`text-xl font-bold ${result.summary.avg_pnl > 0 ? 'text-primary-400' : 'text-red-400'}`}>
              {result.summary.avg_pnl > 0 ? '+' : ''}
              {result.summary.avg_pnl.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? 'Profit Factor' : 'Profit Factor'}</div>
            <div className={`text-xl font-bold ${result.summary.profit_factor && result.summary.profit_factor > 1 ? 'text-primary-400' : 'text-red-400'}`}>
              {result.summary.profit_factor !== null
                ? result.summary.profit_factor.toFixed(2)
                : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? 'TP 적중률' : 'TP Hit Rate'}</div>
            <div className="text-xl font-bold text-primary-400">
              {result.summary.tp_hit_rate.toFixed(2)}%
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div>
            <div className="text-sm text-dark-400">{isKo ? '최대 수익' : 'Max PnL'}</div>
            <div className="text-lg font-bold text-primary-400">
              +{result.summary.max_pnl.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? '최대 손실' : 'Min PnL'}</div>
            <div className="text-lg font-bold text-red-400">
              {result.summary.min_pnl.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? 'SL 적중률' : 'SL Hit Rate'}</div>
            <div className="text-lg font-bold text-red-400">
              {result.summary.sl_hit_rate.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? '평균 보유' : 'Avg Hold'}</div>
            <div className="text-lg font-bold">
              {result.summary.avg_hold.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
