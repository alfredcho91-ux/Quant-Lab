export const MARKET_COINS = ['BTC', 'ETH', 'SOL'] as const;

export type MarketCoin = (typeof MARKET_COINS)[number];

export const DEFAULT_MARKET_COIN: MarketCoin = 'BTC';

export function isMarketCoin(value: unknown): value is MarketCoin {
  return typeof value === 'string' && MARKET_COINS.includes(value as MarketCoin);
}

export const MARKET_INTERVALS = [
  '15m',
  '30m',
  '1h',
  '2h',
  '4h',
  '1d',
  '3d',
  '1w',
  '1M',
] as const;

export type MarketInterval = (typeof MARKET_INTERVALS)[number];

export const MARKET_INTERVAL_LABELS_KO: Partial<Record<MarketInterval, string>> = {
  '4h': '4시간봉',
  '1d': '날봉',
  '1w': '주봉',
  '1M': '달봉',
};

export const DEFAULT_MARKET_INTERVAL: MarketInterval = '4h';
