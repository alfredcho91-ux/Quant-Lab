// Sidebar component
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronLeft,
  ChevronRight,
  Rocket,
  BarChart3,
  Activity,
  Globe,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { getLabels } from '../store/labels';
import { getMarketPrices, getFearGreedIndex } from '../api/client';
import type { Coin, Language } from '../types';

const COINS: Coin[] = ['BTC', 'ETH', 'SOL', 'XRP'];

const menuItems = [
  { path: '/backtest', icon: Rocket, labelKey: 'menu_backtest' as const },
  { path: '/pattern', icon: BarChart3, labelKey: 'menu_pattern' as const },
  { path: '/scanner', icon: Activity, labelKey: 'menu_scanner' as const },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    language,
    selectedCoin,
    sidebarCollapsed,
    setLanguage,
    setSelectedCoin,
    toggleSidebar,
  } = useStore();

  const labels = getLabels(language);

  // Fetch market prices
  const { data: prices } = useQuery({
    queryKey: ['marketPrices'],
    queryFn: getMarketPrices,
    refetchInterval: 30000,
  });

  // Fetch Fear & Greed Index
  const { data: fng } = useQuery({
    queryKey: ['fearGreed'],
    queryFn: getFearGreedIndex,
    refetchInterval: 300000,
  });

  const currentPrice = prices?.[selectedCoin];

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-dark-900/95 backdrop-blur-xl border-r border-dark-700 
        flex flex-col transition-all duration-300 z-50 ${
          sidebarCollapsed ? 'w-16' : 'w-72'
        }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <h1 className="text-lg font-bold bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent">
              {labels.sidebar_title}
            </h1>
          )}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-5 h-5 text-dark-400" />
            ) : (
              <ChevronLeft className="w-5 h-5 text-dark-400" />
            )}
          </button>
        </div>
      </div>

      {/* Language Toggle */}
      {!sidebarCollapsed && (
        <div className="px-4 py-3 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-dark-400" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as Language)}
              className="flex-1 bg-dark-800 border-dark-600 text-sm"
            >
              <option value="ko">한국어</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>
      )}

      {/* Coin Selection */}
      <div className={`border-b border-dark-700 ${sidebarCollapsed ? 'p-2' : 'p-4'}`}>
        {sidebarCollapsed ? (
          <div className="flex flex-col gap-1">
            {COINS.map((coin) => (
              <button
                key={coin}
                onClick={() => setSelectedCoin(coin)}
                className={`p-2 rounded-lg text-xs font-medium transition-all ${
                  selectedCoin === coin
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'text-dark-400 hover:bg-dark-700'
                }`}
              >
                {coin}
              </button>
            ))}
          </div>
        ) : (
          <>
            <label className="text-xs text-dark-400 uppercase tracking-wide mb-2 block">
              {labels.coin_select}
            </label>
            <div className="grid grid-cols-4 gap-1">
              {COINS.map((coin) => (
                <button
                  key={coin}
                  onClick={() => setSelectedCoin(coin)}
                  className={`py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    selectedCoin === coin
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
                  }`}
                >
                  {coin}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Price Display */}
      {!sidebarCollapsed && currentPrice && (
        <div className="px-4 py-3 border-b border-dark-700">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono">
              ${currentPrice.last.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </span>
            <span
              className={`text-sm font-medium ${
                currentPrice.percentage >= 0 ? 'text-bull' : 'text-bear'
              }`}
            >
              {currentPrice.percentage >= 0 ? '+' : ''}
              {currentPrice.percentage.toFixed(2)}%
            </span>
          </div>
        </div>
      )}

      {/* Fear & Greed Index */}
      {!sidebarCollapsed && fng && (
        <div className="px-4 py-3 border-b border-dark-700">
          <label className="text-xs text-dark-400 uppercase tracking-wide mb-2 block">
            {labels.fear_greed}
          </label>
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold font-mono">{fng.value}</span>
            <span className="text-xs text-dark-400">{fng.value_classification}</span>
          </div>
          <div className="progress-bar mt-2">
            <div
              className="progress-bar-fill"
              style={{ width: `${Math.min(100, Math.max(0, parseInt(fng.value)))}%` }}
            />
          </div>
        </div>
      )}

      {/* Menu */}
      <nav className="flex-1 p-2">
        <div className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-500/20 to-green-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'text-dark-300 hover:bg-dark-800 hover:text-dark-100'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-400' : ''}`} />
                {!sidebarCollapsed && (
                  <span className="font-medium">{labels[item.labelKey]}</span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      {!sidebarCollapsed && (
        <div className="p-4 border-t border-dark-700">
          <p className="text-xs text-dark-500 text-center">
            {labels.sidebar_caption}
          </p>
        </div>
      )}
    </aside>
  );
}

