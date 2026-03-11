// Global state management with Zustand
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Language, Coin, MenuPage, BacktestParams } from '../types';

const INTERVALS = ['15m', '1h', '2h', '4h', '1d', '3d', '1w', '1M'] as const;
export type Interval = (typeof INTERVALS)[number];
export type BackgroundTheme = 'default' | 'white' | 'black';

interface AppState {
  // UI State
  language: Language;
  backgroundTheme: BackgroundTheme;
  selectedCoin: Coin;
  selectedInterval: Interval;
  currentPage: MenuPage;
  sidebarCollapsed: boolean;
  
  // Backtest Parameters
  backtestParams: BacktestParams;
  
  // Actions
  setLanguage: (lang: Language) => void;
  setBackgroundTheme: (theme: BackgroundTheme) => void;
  setSelectedCoin: (coin: Coin) => void;
  setSelectedInterval: (interval: Interval) => void;
  setCurrentPage: (page: MenuPage) => void;
  toggleSidebar: () => void;
  updateBacktestParams: (params: Partial<BacktestParams>) => void;
  resetBacktestParams: () => void;
}

const defaultBacktestParams: BacktestParams = {
  coin: 'BTC',
  interval: '1h',
  strategy_id: 'Connors',
  direction: 'Long',
  tp_pct: 2.0,
  sl_pct: 1.0,
  max_bars: 48,
  leverage: 10,
  entry_fee_pct: 0.04,
  exit_fee_pct: 0.04,
  rsi_ob: 70,
  sma_main_len: 200,
  sma1_len: 20,
  sma2_len: 60,
  adx_thr: 25,
  donch: 20,
  bb_length: 20,
  bb_std_mult: 2.0,
  atr_length: 20,
  kc_mult: 1.5,
  vol_ma_length: 20,
  vol_spike_k: 2.0,
  macd_fast: 12,
  macd_slow: 26,
  macd_signal: 9,
  use_csv: false,
};

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Initial state
      language: 'ko',
      backgroundTheme: 'default',
      selectedCoin: 'BTC',
      selectedInterval: '4h',
      currentPage: 'backtest',
      sidebarCollapsed: false,
      backtestParams: defaultBacktestParams,
      
      // Actions
      setLanguage: (lang) => set({ language: lang }),
      setBackgroundTheme: (theme) => set({ backgroundTheme: theme }),
      
      setSelectedCoin: (coin) =>
        set((state) => ({
          selectedCoin: coin,
          backtestParams: { ...state.backtestParams, coin },
        })),
      
      setSelectedInterval: (interval) =>
        set((state) => ({
          selectedInterval: interval,
          backtestParams: { ...state.backtestParams, interval },
        })),
      
      setCurrentPage: (page) => set({ currentPage: page }),
      
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      updateBacktestParams: (params) =>
        set((state) => ({
          backtestParams: { ...state.backtestParams, ...params },
        })),
      
      resetBacktestParams: () =>
        set((state) => ({
          backtestParams: { ...defaultBacktestParams, coin: state.selectedCoin },
        })),
    }),
    {
      name: 'wolgem-quant-storage',
      partialize: (state) => ({
        language: state.language,
        backgroundTheme: state.backgroundTheme,
        selectedCoin: state.selectedCoin,
        selectedInterval: state.selectedInterval,
        backtestParams: state.backtestParams,
      }),
      merge: (persistedState, currentState) => {
        const incoming = (persistedState as Partial<AppState>) ?? {};
        const persistedParams =
          (incoming.backtestParams as Partial<BacktestParams> & { ema_len?: number }) ?? {};
        const normalizedParams: BacktestParams = {
          ...defaultBacktestParams,
          ...persistedParams,
          sma_main_len:
            persistedParams.sma_main_len ??
            persistedParams.ema_len ??
            defaultBacktestParams.sma_main_len,
        };

        return {
          ...currentState,
          ...incoming,
          backtestParams: normalizedParams,
        };
      },
    }
  )
);

// Selectors
export const useLanguage = () => useStore((state) => state.language);
export const useBackgroundTheme = () => useStore((state) => state.backgroundTheme);
export const useSelectedCoin = () => useStore((state) => state.selectedCoin);
export const useCurrentPage = () => useStore((state) => state.currentPage);
export const useSelectedInterval = () => useStore((state) => state.selectedInterval);
export const useSidebarCollapsed = () => useStore((state) => state.sidebarCollapsed);
export const useBacktestParams = () => useStore((state) => state.backtestParams);
export const useSetLanguage = () => useStore((state) => state.setLanguage);
export const useSetBackgroundTheme = () => useStore((state) => state.setBackgroundTheme);
export const useSetSelectedCoin = () => useStore((state) => state.setSelectedCoin);
export const useSetSelectedInterval = () => useStore((state) => state.setSelectedInterval);
export const useSetCurrentPage = () => useStore((state) => state.setCurrentPage);
export const useToggleSidebar = () => useStore((state) => state.toggleSidebar);
export const useUpdateBacktestParams = () => useStore((state) => state.updateBacktestParams);
export const useResetBacktestParams = () => useStore((state) => state.resetBacktestParams);
