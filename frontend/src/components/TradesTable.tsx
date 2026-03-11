// Trades Table Component
import { useState } from 'react';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';
import type { Trade, RegimeStat } from '../types';
import { useLanguage } from '../store/useStore';
import { getLabels } from '../store/labels';

interface TradesTableProps {
  trades: Trade[];
  regimeStats?: RegimeStat[];
}

export default function TradesTable({ trades, regimeStats }: TradesTableProps) {
  const language = useLanguage();
  const labels = getLabels(language);
  const [activeTab, setActiveTab] = useState<'history' | 'regime'>('history');
  const [sortBy, setSortBy] = useState<'time' | 'pnl'>('time');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sortedTrades = [...trades].sort((a, b) => {
    if (sortBy === 'time') {
      const comparison = new Date(a['Entry Time']).getTime() - new Date(b['Entry Time']).getTime();
      return sortDir === 'asc' ? comparison : -comparison;
    } else {
      return sortDir === 'asc' ? a.PnL - b.PnL : b.PnL - a.PnL;
    }
  });

  const handleSort = (column: 'time' | 'pnl') => {
    if (sortBy === column) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDir('desc');
    }
  };

  const exportToCSV = () => {
    const headers = ['Entry Time', 'Exit Time', 'Direction', 'Entry Price', 'Exit Price', 'Outcome', 'Regime', 'PnL %'];
    const rows = trades.map((t) => [
      t['Entry Time'],
      t['Exit Time'],
      t.Direction,
      t['Entry Price'],
      t['Exit Price'],
      t.Outcome,
      t.Regime,
      (t.PnL * 100).toFixed(2),
    ]);
    
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'trades.csv';
    a.click();
  };

  const SortIcon = ({ column }: { column: 'time' | 'pnl' }) => {
    if (sortBy !== column) return null;
    return sortDir === 'asc' ? (
      <ChevronUp className="w-4 h-4 inline ml-1" />
    ) : (
      <ChevronDown className="w-4 h-4 inline ml-1" />
    );
  };

  return (
    <div className="card overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-dark-700">
        <button
          onClick={() => setActiveTab('history')}
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
        >
          {labels.history}
        </button>
        <button
          onClick={() => setActiveTab('regime')}
          className={`tab ${activeTab === 'regime' ? 'active' : ''}`}
        >
          {labels.regime_perf}
        </button>
        <div className="flex-1" />
        <button
          onClick={exportToCSV}
          className="p-2 text-dark-400 hover:text-dark-200 transition-colors"
          title="Export CSV"
        >
          <Download className="w-4 h-4" />
        </button>
      </div>

      {/* Trade History */}
      {activeTab === 'history' && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-dark-800/50">
              <tr>
                <th
                  className="px-4 py-3 text-left text-xs text-dark-400 uppercase cursor-pointer hover:text-dark-200"
                  onClick={() => handleSort('time')}
                >
                  Entry Time <SortIcon column="time" />
                </th>
                <th className="px-4 py-3 text-left text-xs text-dark-400 uppercase">
                  Exit Time
                </th>
                <th className="px-4 py-3 text-center text-xs text-dark-400 uppercase">
                  Direction
                </th>
                <th className="px-4 py-3 text-right text-xs text-dark-400 uppercase">
                  Entry
                </th>
                <th className="px-4 py-3 text-right text-xs text-dark-400 uppercase">
                  Exit
                </th>
                <th className="px-4 py-3 text-center text-xs text-dark-400 uppercase">
                  Outcome
                </th>
                <th className="px-4 py-3 text-center text-xs text-dark-400 uppercase">
                  Regime
                </th>
                <th
                  className="px-4 py-3 text-right text-xs text-dark-400 uppercase cursor-pointer hover:text-dark-200"
                  onClick={() => handleSort('pnl')}
                >
                  PnL % <SortIcon column="pnl" />
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700">
              {sortedTrades.slice(0, 100).map((trade, idx) => (
                <tr key={idx} className="hover:bg-dark-700/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs">
                    {new Date(trade['Entry Time']).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {new Date(trade['Exit Time']).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`badge ${
                        trade.Direction === 'Long' ? 'badge-bull' : 'badge-bear'
                      }`}
                    >
                      {trade.Direction}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    ${trade['Entry Price'].toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    ${trade['Exit Price'].toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-center text-xs">
                    {trade.Outcome}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`badge ${
                        trade.Regime === 'Bull'
                          ? 'badge-bull'
                          : trade.Regime === 'Bear'
                          ? 'badge-bear'
                          : 'badge-sideways'
                      }`}
                    >
                      {trade.Regime}
                    </span>
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono font-medium ${
                      trade.PnL > 0 ? 'text-bull' : 'text-bear'
                    }`}
                  >
                    {trade.PnL > 0 ? '+' : ''}
                    {(trade.PnL * 100).toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {trades.length > 100 && (
            <div className="p-4 text-center text-dark-400 text-sm">
              Showing 100 of {trades.length} trades
            </div>
          )}
        </div>
      )}

      {/* Regime Performance */}
      {activeTab === 'regime' && regimeStats && (
        <div className="p-4">
          <div className="grid gap-4 md:grid-cols-3">
            {regimeStats.map((stat) => (
              <div
                key={stat.Regime}
                className={`p-4 rounded-lg border ${
                  stat.Regime === 'Bull'
                    ? 'bg-bull/10 border-bull/20'
                    : stat.Regime === 'Bear'
                    ? 'bg-bear/10 border-bear/20'
                    : 'bg-warning/10 border-warning/20'
                }`}
              >
                <h4
                  className={`text-lg font-bold mb-3 ${
                    stat.Regime === 'Bull'
                      ? 'text-bull'
                      : stat.Regime === 'Bear'
                      ? 'text-bear'
                      : 'text-warning'
                  }`}
                >
                  {stat.Regime}
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-dark-400">Trades</span>
                    <span className="font-mono">{stat.Count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-400">Win Rate</span>
                    <span className="font-mono">{stat.WinRate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-400">Avg PnL</span>
                    <span
                      className={`font-mono ${
                        stat.AvgPnL > 0 ? 'text-bull' : 'text-bear'
                      }`}
                    >
                      {stat.AvgPnL > 0 ? '+' : ''}
                      {stat.AvgPnL.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
