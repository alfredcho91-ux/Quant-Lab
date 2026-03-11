// Trading Journal Page
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getJournal, addJournalEntry, deleteJournalEntry } from '../api/client';
import { useLanguage, useSelectedCoin } from '../store/useStore';
import type { JournalEntry } from '../types';
import { PlusCircle, Trash2, X } from 'lucide-react';

const OUTCOMES = ['Win', 'Loss', 'Breakeven'];
const EMOTIONS = ['Calm', 'Anxious', 'Greedy', 'Fearful', 'Confident', 'FOMO'];
const DIRECTIONS = ['Long', 'Short'];

export default function JournalPage() {
  const language = useLanguage();
  const selectedCoin = useSelectedCoin();
  const isKo = language === 'ko';
  const queryClient = useQueryClient();

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<Partial<JournalEntry>>({
    symbol: `${selectedCoin}/USDT`,
    direction: 'Long',
    outcome: 'Win',
    emotion: 'Calm',
  });

  const { data: entries, isLoading } = useQuery({
    queryKey: ['journal'],
    queryFn: getJournal,
  });

  const addMutation = useMutation({
    mutationFn: addJournalEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal'] });
      setShowForm(false);
      setFormData({
        symbol: `${selectedCoin}/USDT`,
        direction: 'Long',
        outcome: 'Win',
        emotion: 'Calm',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteJournalEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal'] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addMutation.mutate(formData);
  };

  // Calculate stats
  const stats = {
    total: entries?.length || 0,
    wins: entries?.filter((e) => e.outcome === 'Win').length || 0,
    losses: entries?.filter((e) => e.outcome === 'Loss').length || 0,
    totalPnl: entries?.reduce((sum, e) => sum + (e.pnl_pct || 0), 0) || 0,
  };
  const winRate = stats.total > 0 ? (stats.wins / stats.total) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            📒 {isKo ? '매매 일지' : 'Trading Journal'}
          </h1>
          <p className="text-dark-400 mt-1">
            {isKo ? '거래 기록 및 복기 관리' : 'Track and review your trades'}
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary flex items-center gap-2"
        >
          <PlusCircle className="w-5 h-5" />
          {isKo ? '새 기록' : 'New Entry'}
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-white">{stats.total}</div>
          <div className="text-sm text-dark-400">{isKo ? '총 거래' : 'Total Trades'}</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-primary-400">{winRate.toFixed(1)}%</div>
          <div className="text-sm text-dark-400">{isKo ? '승률' : 'Win Rate'}</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-bull">{stats.wins}</div>
          <div className="text-sm text-dark-400">{isKo ? '수익' : 'Wins'}</div>
        </div>
        <div className="card p-4 text-center">
          <div className={`text-2xl font-bold ${stats.totalPnl >= 0 ? 'text-bull' : 'text-bear'}`}>
            {stats.totalPnl >= 0 ? '+' : ''}{stats.totalPnl.toFixed(2)}%
          </div>
          <div className="text-sm text-dark-400">{isKo ? '총 PnL' : 'Total PnL'}</div>
        </div>
      </div>

      {/* New Entry Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">{isKo ? '새 거래 기록' : 'New Trade Entry'}</h2>
              <button onClick={() => setShowForm(false)} className="text-dark-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {/* Symbol */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '심볼' : 'Symbol'}</label>
                  <input
                    type="text"
                    value={formData.symbol || ''}
                    onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                    placeholder="BTC/USDT"
                  />
                </div>

                {/* Timeframe */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '타임프레임' : 'Timeframe'}</label>
                  <input
                    type="text"
                    value={formData.timeframe || ''}
                    onChange={(e) => setFormData({ ...formData, timeframe: e.target.value })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                    placeholder="1h"
                  />
                </div>

                {/* Direction */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '방향' : 'Direction'}</label>
                  <select
                    value={formData.direction || 'Long'}
                    onChange={(e) => setFormData({ ...formData, direction: e.target.value })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  >
                    {DIRECTIONS.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>

                {/* Entry Price */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '진입가' : 'Entry Price'}</label>
                  <input
                    type="number"
                    step="any"
                    value={formData.entry_price || ''}
                    onChange={(e) => setFormData({ ...formData, entry_price: parseFloat(e.target.value) || undefined })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  />
                </div>

                {/* Exit Price */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '청산가' : 'Exit Price'}</label>
                  <input
                    type="number"
                    step="any"
                    value={formData.exit_price || ''}
                    onChange={(e) => setFormData({ ...formData, exit_price: parseFloat(e.target.value) || undefined })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  />
                </div>

                {/* PnL % */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">PnL %</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.pnl_pct || ''}
                    onChange={(e) => setFormData({ ...formData, pnl_pct: parseFloat(e.target.value) || undefined })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  />
                </div>

                {/* Outcome */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '결과' : 'Outcome'}</label>
                  <select
                    value={formData.outcome || 'Win'}
                    onChange={(e) => setFormData({ ...formData, outcome: e.target.value })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  >
                    {OUTCOMES.map((o) => (
                      <option key={o} value={o}>{o}</option>
                    ))}
                  </select>
                </div>

                {/* Emotion */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '감정' : 'Emotion'}</label>
                  <select
                    value={formData.emotion || 'Calm'}
                    onChange={(e) => setFormData({ ...formData, emotion: e.target.value })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  >
                    {EMOTIONS.map((e) => (
                      <option key={e} value={e}>{e}</option>
                    ))}
                  </select>
                </div>

                {/* Strategy */}
                <div>
                  <label className="block text-sm text-dark-400 mb-1">{isKo ? '전략' : 'Strategy'}</label>
                  <input
                    type="text"
                    value={formData.strategy_id || ''}
                    onChange={(e) => setFormData({ ...formData, strategy_id: e.target.value })}
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                    placeholder={isKo ? '사용한 전략' : 'Strategy used'}
                  />
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm text-dark-400 mb-1">{isKo ? '태그' : 'Tags'}</label>
                <input
                  type="text"
                  value={formData.tags || ''}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  placeholder={isKo ? '쉼표로 구분 (예: breakout, reversal)' : 'Comma separated (e.g., breakout, reversal)'}
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm text-dark-400 mb-1">{isKo ? '노트' : 'Notes'}</label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  placeholder={isKo ? '거래에 대한 메모...' : 'Notes about this trade...'}
                />
              </div>

              {/* Mistakes */}
              <div>
                <label className="block text-sm text-dark-400 mb-1">{isKo ? '실수/교훈' : 'Mistakes/Lessons'}</label>
                <textarea
                  value={formData.mistakes || ''}
                  onChange={(e) => setFormData({ ...formData, mistakes: e.target.value })}
                  rows={2}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm"
                  placeholder={isKo ? '실수나 배운점...' : 'What went wrong or what you learned...'}
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="flex-1 py-2 bg-dark-700 rounded-lg text-dark-300 hover:bg-dark-600"
                >
                  {isKo ? '취소' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending}
                  className="flex-1 btn-primary py-2 disabled:opacity-50"
                >
                  {addMutation.isPending ? (isKo ? '저장 중...' : 'Saving...') : (isKo ? '저장' : 'Save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Journal Entries */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">{isKo ? '거래 기록' : 'Trade History'}</h3>
        
        {isLoading ? (
          <div className="text-center py-8 text-dark-400">{isKo ? '로딩 중...' : 'Loading...'}</div>
        ) : !entries || entries.length === 0 ? (
          <div className="text-center py-8 text-dark-400">
            {isKo ? '기록된 거래가 없습니다.' : 'No trades recorded yet.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-700">
                  <th className="text-left py-2 px-3">{isKo ? '날짜' : 'Date'}</th>
                  <th className="text-left py-2 px-3">{isKo ? '심볼' : 'Symbol'}</th>
                  <th className="text-center py-2 px-3">{isKo ? '방향' : 'Dir'}</th>
                  <th className="text-right py-2 px-3">{isKo ? '진입' : 'Entry'}</th>
                  <th className="text-right py-2 px-3">{isKo ? '청산' : 'Exit'}</th>
                  <th className="text-right py-2 px-3">PnL</th>
                  <th className="text-center py-2 px-3">{isKo ? '결과' : 'Result'}</th>
                  <th className="text-center py-2 px-3">{isKo ? '감정' : 'Emotion'}</th>
                  <th className="text-center py-2 px-3"></th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b border-dark-800 hover:bg-dark-800/50">
                    <td className="py-2 px-3 text-xs font-mono">
                      {entry.datetime?.slice(0, 10) || '-'}
                    </td>
                    <td className="py-2 px-3 font-medium">{entry.symbol || '-'}</td>
                    <td className={`py-2 px-3 text-center ${entry.direction === 'Long' ? 'text-bull' : 'text-bear'}`}>
                      {entry.direction || '-'}
                    </td>
                    <td className="py-2 px-3 text-right font-mono">
                      {entry.entry_price?.toLocaleString() || '-'}
                    </td>
                    <td className="py-2 px-3 text-right font-mono">
                      {entry.exit_price?.toLocaleString() || '-'}
                    </td>
                    <td className={`py-2 px-3 text-right font-mono ${
                      (entry.pnl_pct || 0) >= 0 ? 'text-bull' : 'text-bear'
                    }`}>
                      {entry.pnl_pct != null ? `${entry.pnl_pct >= 0 ? '+' : ''}${entry.pnl_pct.toFixed(2)}%` : '-'}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        entry.outcome === 'Win'
                          ? 'bg-bull/20 text-bull'
                          : entry.outcome === 'Loss'
                          ? 'bg-bear/20 text-bear'
                          : 'bg-dark-600 text-dark-300'
                      }`}>
                        {entry.outcome || '-'}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center text-dark-400 text-xs">
                      {entry.emotion || '-'}
                    </td>
                    <td className="py-2 px-3">
                      <button
                        onClick={() => entry.id && deleteMutation.mutate(entry.id)}
                        className="text-dark-500 hover:text-red-400 transition-colors"
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
