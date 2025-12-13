// API client for WolGem Quant Master
import axios from 'axios';
import type {
  MarketPrice,
  FearGreedIndex,
  Strategy,
  StrategyInfo,
  BacktestParams,
  BacktestResult,
  SRLevel,
  Preset,
  MaCrossParams,
  MaCrossResult,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Market Data
export async function getMarketPrices(): Promise<Record<string, MarketPrice> | null> {
  try {
    const res = await api.get<ApiResponse<Record<string, MarketPrice>>>('/market/prices');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function getFearGreedIndex(): Promise<FearGreedIndex | null> {
  try {
    const res = await api.get<ApiResponse<FearGreedIndex>>('/market/fear-greed');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

// Timeframes
export async function getTimeframes(coin: string): Promise<{
  all: string[];
  binance: string[];
  csv: string[];
} | null> {
  try {
    const res = await api.get<ApiResponse<{ all: string[]; binance: string[]; csv: string[] }>>(
      `/timeframes/${coin}`
    );
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

// Strategies
export async function getStrategies(): Promise<Strategy[] | null> {
  try {
    const res = await api.get<ApiResponse<Strategy[]>>('/strategies');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function getStrategyInfo(
  strategyId: string,
  lang: string = 'ko',
  params?: {
    rsi_ob?: number;
    rsi2_ob?: number;
    ema_len?: number;
    sma1_len?: number;
    sma2_len?: number;
  }
): Promise<StrategyInfo | null> {
  try {
    const res = await api.get<ApiResponse<StrategyInfo>>(`/strategy-info/${strategyId}`, {
      params: { lang, ...params },
    });
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

// OHLCV Data
export async function getOHLCV(
  coin: string,
  interval: string,
  useCsv: boolean = false,
  limit: number = 3000
): Promise<{ data: unknown[]; source: string; count: number } | null> {
  try {
    const res = await api.get(`/ohlcv/${coin}/${interval}`, {
      params: { use_csv: useCsv, limit },
    });
    return res.data.success ? res.data : null;
  } catch {
    return null;
  }
}

// Backtest
export async function runBacktest(params: BacktestParams): Promise<BacktestResult | null> {
  try {
    const res = await api.post<{
      success: boolean;
      chart_data: BacktestResult['chart_data'];
      trades: BacktestResult['trades'];
      summary: BacktestResult['summary'];
      error?: string;
    }>('/backtest', params);
    
    if (res.data.success) {
      return {
        chart_data: res.data.chart_data,
        trades: res.data.trades,
        summary: res.data.summary,
      };
    }
    console.error('Backtest error:', res.data.error);
    return null;
  } catch (err) {
    console.error('Backtest request failed:', err);
    return null;
  }
}

// Support/Resistance
export async function getSupportResistance(
  coin: string,
  interval: string,
  options?: {
    lookback?: number;
    tolerance_pct?: number;
    min_touches?: number;
    show_pivots?: boolean;
    htf_option?: string;
  }
): Promise<SRLevel[] | null> {
  try {
    const res = await api.get<ApiResponse<SRLevel[]>>(`/support-resistance/${coin}/${interval}`, {
      params: options,
    });
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

// Presets
export async function getPresets(): Promise<Record<string, Preset> | null> {
  try {
    const res = await api.get<ApiResponse<Record<string, Preset>>>('/presets');
    return res.data.success ? res.data.data! : null;
  } catch {
    return null;
  }
}

export async function savePreset(
  name: string,
  coin: string,
  interval: string,
  stratId: string,
  direction: string,
  params: Partial<BacktestParams>
): Promise<boolean> {
  try {
    const res = await api.post<ApiResponse<null>>('/presets', {
      name,
      coin,
      interval,
      strat_id: stratId,
      direction,
      params,
    });
    return res.data.success;
  } catch {
    return false;
  }
}

export async function deletePreset(name: string): Promise<boolean> {
  try {
    const res = await api.delete<ApiResponse<null>>(`/presets/${name}`);
    return res.data.success;
  } catch {
    return false;
  }
}

// MA Cross Statistics
export async function runMaCross(params: MaCrossParams): Promise<MaCrossResult | null> {
  try {
    const res = await api.post<{
      success: boolean;
      data: MaCrossResult['data'];
      cross_type: string;
      available_pairs: string[];
      horizons: number[];
      error?: string;
    }>('/ma-cross', params);
    
    if (res.data.success) {
      return {
        data: res.data.data,
        cross_type: res.data.cross_type,
        available_pairs: res.data.available_pairs,
        horizons: res.data.horizons,
      };
    }
    console.error('MA Cross error:', res.data.error);
    return null;
  } catch (err) {
    console.error('MA Cross request failed:', err);
    return null;
  }
}

