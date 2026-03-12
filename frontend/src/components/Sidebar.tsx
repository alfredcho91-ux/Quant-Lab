// Sidebar component
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Activity,
  Palette,
  Globe,
  Target,
  Layers,
  Search,
  BookOpen,
  Radio,
  Flame,
  Zap,
  Bot,
  Rocket,
  FlaskConical,
} from 'lucide-react';
import {
  useBackgroundTheme,
  useLanguage,
  useSelectedCoin,
  useSelectedInterval,
  useSetBackgroundTheme,
  useSetLanguage,
  useSetSelectedCoin,
  useSetSelectedInterval,
  useSidebarCollapsed,
  useToggleSidebar,
} from '../store/useStore';
import { getLabels } from '../store/labels';
import { getMarketPrices, getFearGreedIndex } from '../api/client';
import type { Coin, Language } from '../types';
import type { BackgroundTheme, Interval } from '../store/useStore';

const COINS: Coin[] = ['BTC', 'ETH', 'SOL', 'XRP'];
const INTERVALS: Interval[] = ['15m', '30m', '1h', '2h', '4h', '1d', '3d', '1w', '1M'];

const menuItems = [
  // 주요 분석 페이지 (맨 위)
  { path: '/ai-backtest-lab', icon: Bot, labelKey: 'menu_ai_backtest_lab' as const },
  { path: '/trend-judgment', icon: Activity, labelKey: 'menu_trend_judgment' as const },
  { path: '/streak-analysis', icon: Flame, labelKey: 'menu_streak_analysis' as const },
  { path: '/bb-mid', icon: Target, labelKey: 'menu_bb_mid' as const },
  { path: '/hybrid-analysis', icon: Zap, labelKey: 'menu_hybrid_analysis' as const },
  // 기타 분석 페이지
  { path: '/combo-filter', icon: Layers, labelKey: 'menu_combo_filter' as const },
  { path: '/pattern', icon: BarChart3, labelKey: 'menu_pattern' as const },
  { path: '/pattern-scanner', icon: Search, labelKey: 'menu_pattern_scanner' as const },
  { path: '/strategy-scanner', icon: Radio, labelKey: 'menu_strategy_scanner' as const },
  // 백테스트 페이지 복구
  { path: '/backtest', icon: Rocket, labelKey: 'menu_backtest' as const },
  { path: '/backtest-advanced', icon: FlaskConical, labelKey: 'menu_backtest_advanced' as const },
  { path: '/journal', icon: BookOpen, labelKey: 'menu_journal' as const },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [principlesCollapsed, setPrinciplesCollapsed] = useState(true);
  const language = useLanguage();
  const backgroundTheme = useBackgroundTheme();
  const selectedCoin = useSelectedCoin();
  const selectedInterval = useSelectedInterval();
  const sidebarCollapsed = useSidebarCollapsed();
  const setLanguage = useSetLanguage();
  const setBackgroundTheme = useSetBackgroundTheme();
  const setSelectedCoin = useSetSelectedCoin();
  const setSelectedInterval = useSetSelectedInterval();
  const toggleSidebar = useToggleSidebar();

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
  const sidebarThemeClass =
    backgroundTheme === 'white'
      ? 'bg-white/95 border-slate-200'
      : backgroundTheme === 'black'
        ? 'bg-black/95 border-neutral-800'
        : 'bg-dark-900/95 border-dark-700';

  return (
    <aside
      className={`fixed left-0 top-0 h-screen backdrop-blur-xl border-r
        flex flex-col transition-all duration-300 z-50 ${
          sidebarThemeClass
        } ${
          sidebarCollapsed ? 'w-16' : 'w-72'
        }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <h1 className="text-lg font-bold" style={{ color: '#072ac8' }}>
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
            <div className="flex items-center gap-1 shrink-0">
              <Palette className="w-4 h-4 text-dark-400" />
              <select
                value={backgroundTheme}
                onChange={(e) => setBackgroundTheme(e.target.value as BackgroundTheme)}
                className="w-20 bg-dark-800 border-dark-600 text-xs px-2 py-1"
                title={language === 'ko' ? '배경색' : 'Background'}
              >
                <option value="default">{language === 'ko' ? '기본' : 'Default'}</option>
                <option value="white">{language === 'ko' ? '흰색' : 'White'}</option>
                <option value="black">{language === 'ko' ? '검은색' : 'Black'}</option>
              </select>
            </div>
            <div className="flex items-center gap-1 flex-1 min-w-0">
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
        </div>
      )}

      {/* 코인 선택 & 봉 기간 (통합) */}
      <div className={`border-b border-dark-700 ${sidebarCollapsed ? 'p-2' : 'p-4'}`}>
        {sidebarCollapsed ? (
          <div className="flex flex-col gap-1.5">
            {COINS.map((coin) => (
              <button
                key={coin}
                onClick={() => setSelectedCoin(coin)}
                className={`p-2 rounded-lg text-xs font-medium transition-all ${
                  selectedCoin === coin
                    ? 'bg-primary-500/20 text-primary-400'
                    : 'text-dark-400 hover:bg-dark-700'
                }`}
              >
                {coin}
              </button>
            ))}
            <select
              value={selectedInterval}
              onChange={(e) => setSelectedInterval(e.target.value as Interval)}
              className="w-full bg-dark-800 border border-dark-600 rounded text-xs py-1.5 mt-0.5"
              title={labels.interval}
            >
              {INTERVALS.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>
        ) : (
          <>
            <label className="text-xs text-dark-400 uppercase tracking-wide mb-2 block">
              {labels.coin_select} · {labels.interval}
            </label>
            <div className="grid grid-cols-4 gap-1">
              {COINS.map((coin) => (
                <button
                  key={coin}
                  onClick={() => setSelectedCoin(coin)}
                  className={`py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    selectedCoin === coin
                      ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                      : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
                  }`}
                >
                  {coin}
                </button>
              ))}
            </div>
            <select
              value={selectedInterval}
              onChange={(e) => setSelectedInterval(e.target.value as Interval)}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm mt-2"
            >
              {INTERVALS.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
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

      {/* Trading Principles */}
      <div className={`border-b border-dark-700 ${sidebarCollapsed ? 'px-2 py-2' : 'px-4 py-3'}`}>
        {sidebarCollapsed ? (
          <div
            className="text-[10px] text-center text-primary-300 bg-primary-500/10 border border-primary-500/20 rounded-md py-1"
            title={labels.trading_principles.join('\n')}
          >
            {language === 'ko' ? '원칙' : 'Rules'}
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-dark-400 uppercase tracking-wide">
                {labels.trading_principles_title}
              </label>
              <button
                onClick={() => setPrinciplesCollapsed((prev) => !prev)}
                className="text-[10px] text-dark-400 hover:text-dark-200 flex items-center gap-1"
              >
                {principlesCollapsed
                  ? (language === 'ko' ? '펼치기' : 'Expand')
                  : (language === 'ko' ? '접기' : 'Collapse')}
                {principlesCollapsed ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
              </button>
            </div>
            {!principlesCollapsed && (
              <ol className="space-y-1">
                {labels.trading_principles.map((rule, index) => (
                  <li key={`${index}-${rule}`} className="flex gap-2 text-[11px] leading-relaxed text-dark-200">
                    <span className="text-primary-400 font-semibold">{index + 1}.</span>
                    <span>{rule}</span>
                  </li>
                ))}
              </ol>
            )}
          </>
        )}
      </div>

      {/* Menu */}
      <nav className="flex-1 p-2 overflow-y-auto">
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
                    ? 'bg-gradient-to-r from-primary-500/20 to-primary-500/10 text-primary-400 border border-primary-500/20'
                    : 'text-dark-300 hover:bg-dark-800 hover:text-dark-100'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-primary-400' : ''}`} />
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
