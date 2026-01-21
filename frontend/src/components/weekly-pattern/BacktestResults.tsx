// 주간 패턴 분석 - 백테스팅 결과 컴포넌트

import { Play } from 'lucide-react';
import type { WeeklyPatternBacktestResult } from '../../types';

interface BacktestResultsProps {
  backtestResult: WeeklyPatternBacktestResult;
  isKo: boolean;
}

export function BacktestResults({ backtestResult, isKo }: BacktestResultsProps) {
  if (!backtestResult || !backtestResult.success) return null;

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Play className="w-5 h-5 text-cyan-400" />
        {isKo ? '백테스팅 결과' : 'Backtest Results'}
      </h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? '총 거래 수' : 'Total Trades'}
          </div>
          <div className="text-2xl font-bold">{backtestResult.summary.n_trades}</div>
        </div>
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? '반등 확률' : 'Rebound Rate'}
          </div>
          <div className={`text-2xl font-bold ${backtestResult.summary.win_rate > 50 ? 'text-emerald-400' : 'text-red-400'}`}>
            {backtestResult.summary.win_rate.toFixed(2)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? '총 수익률' : 'Total PnL'}
          </div>
          <div className={`text-2xl font-bold ${backtestResult.summary.total_pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {backtestResult.summary.total_pnl >= 0 ? '+' : ''}{backtestResult.summary.total_pnl.toFixed(2)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? '평균 수익률' : 'Avg PnL'}
          </div>
          <div className={`text-2xl font-bold ${backtestResult.summary.avg_pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {backtestResult.summary.avg_pnl >= 0 ? '+' : ''}{backtestResult.summary.avg_pnl.toFixed(2)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? 'Profit Factor' : 'Profit Factor'}
          </div>
          <div className={`text-2xl font-bold ${backtestResult.summary.profit_factor > 1 ? 'text-emerald-400' : 'text-red-400'}`}>
            {backtestResult.summary.profit_factor === Infinity ? '∞' : backtestResult.summary.profit_factor.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? '최대 수익' : 'Max PnL'}
          </div>
          <div className="text-xl font-bold text-emerald-400">
            +{backtestResult.summary.max_pnl.toFixed(2)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? '최대 손실' : 'Min PnL'}
          </div>
          <div className="text-xl font-bold text-red-400">
            {backtestResult.summary.min_pnl.toFixed(2)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-dark-400 mb-1">
            {isKo ? '필터링된 주' : 'Filtered Weeks'}
          </div>
          <div className="text-xl font-bold">
            {backtestResult.filtered_weeks}
          </div>
        </div>
      </div>

      {/* 거래 내역 테이블 */}
      {backtestResult.trades && backtestResult.trades.length > 0 && (
        <div className="mt-6">
          <h3 className="text-md font-semibold mb-3">
            {isKo ? '거래 내역' : 'Trade History'}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-700">
                  <th className="text-left py-2 px-3 text-dark-400">{isKo ? '진입일' : 'Entry Date'}</th>
                  <th className="text-left py-2 px-3 text-dark-400">{isKo ? '청산일' : 'Exit Date'}</th>
                  <th className="text-right py-2 px-3 text-dark-400">{isKo ? '진입가' : 'Entry Price'}</th>
                  <th className="text-right py-2 px-3 text-dark-400">{isKo ? '청산가' : 'Exit Price'}</th>
                  <th className="text-right py-2 px-3 text-dark-400">{isKo ? '수익률' : 'Return %'}</th>
                  <th className="text-right py-2 px-3 text-dark-400">{isKo ? '주 초반 하락' : 'Early Drop %'}</th>
                  <th className="text-right py-2 px-3 text-dark-400">RSI</th>
                </tr>
              </thead>
              <tbody>
                {backtestResult.trades.map((trade, idx) => (
                  <tr key={idx} className="border-b border-dark-800 hover:bg-dark-800/50">
                    <td className="py-2 px-3 text-dark-300">{trade.entry_date}</td>
                    <td className="py-2 px-3 text-dark-300">{trade.exit_date}</td>
                    <td className="py-2 px-3 text-right font-mono text-dark-300">{trade.entry_price.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right font-mono text-dark-300">{trade.exit_price.toFixed(2)}</td>
                    <td className={`py-2 px-3 text-right font-mono font-bold ${trade.pnl_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-dark-300">{trade.ret_early.toFixed(2)}%</td>
                    <td className="py-2 px-3 text-right font-mono text-dark-300">{trade.rsi_tue.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
