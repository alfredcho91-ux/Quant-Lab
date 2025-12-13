// Global state management with Zustand
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Language, Coin, MenuPage, BacktestParams } from '../types';

interface AppState {
  // UI State
  language: Language;
  selectedCoin: Coin;
  currentPage: MenuPage;
  sidebarCollapsed: boolean;
  
  // Backtest Parameters
  backtestParams: BacktestParams;
  
  // Actions
  setLanguage: (lang: Language) => void;
  setSelectedCoin: (coin: Coin) => void;
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
  rsi2_ob: 80,
  ema_len: 200,
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
      selectedCoin: 'BTC',
      currentPage: 'backtest',
      sidebarCollapsed: false,
      backtestParams: defaultBacktestParams,
      
      // Actions
      setLanguage: (lang) => set({ language: lang }),
      
      setSelectedCoin: (coin) =>
        set((state) => ({
          selectedCoin: coin,
          backtestParams: { ...state.backtestParams, coin },
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
        selectedCoin: state.selectedCoin,
        backtestParams: state.backtestParams,
      }),
    }
  )
);

// Selectors
export const useLanguage = () => useStore((state) => state.language);
export const useSelectedCoin = () => useStore((state) => state.selectedCoin);
export const useCurrentPage = () => useStore((state) => state.currentPage);
export const useBacktestParams = () => useStore((state) => state.backtestParams);

