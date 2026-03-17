import type { IndicatorDef } from './types';

export const AI_BUILDER_INDICATOR_LIBRARY: IndicatorDef[] = [
  {
    id: 'rsi',
    label: 'RSI(14)',
    params: { length: 14, oversold: 30, overbought: 70 },
    descriptionKo: '과매수/과매도 구간으로 모멘텀 반전 타이밍을 판단합니다.',
    descriptionEn: 'Measures momentum and identifies overbought/oversold reversal zones.',
  },
  {
    id: 'sma',
    label: 'SMA',
    params: { fast: 20, slow: 50, long: 100 },
    descriptionKo: '이동평균 레벨과 교차로 추세 방향을 확인합니다.',
    descriptionEn: 'Uses moving-average levels and crossovers to confirm trend direction.',
  },
  {
    id: 'macd',
    label: 'MACD',
    params: { fast: 12, slow: 26, signal: 9 },
    descriptionKo: '히스토그램/시그널 변화로 추세 전환과 가속을 포착합니다.',
    descriptionEn: 'Captures trend shifts and momentum acceleration via histogram/signal changes.',
  },
  {
    id: 'adx',
    label: 'ADX(14)',
    params: { length: 14, threshold: 25 },
    descriptionKo: '추세 강도를 수치화해 횡보장 필터로 사용합니다.',
    descriptionEn: 'Quantifies trend strength and helps filter out range-bound conditions.',
  },
  {
    id: 'slow_stoch',
    label: '3 Slow Stochastic',
    params: { k: 20, smoothK: 12, smoothD: 12 },
    descriptionKo: 'K/D 교차로 단기 진입/청산 타이밍을 보조합니다.',
    descriptionEn: 'Uses K/D crossovers for short-term entry and exit timing.',
  },
  {
    id: 'atr',
    label: 'ATR%',
    params: { length: 14, minVol: 0.8 },
    descriptionKo: '변동성 수준을 반영해 저변동 구간 진입을 제한합니다.',
    descriptionEn: 'Applies a volatility filter to avoid low-volatility setups.',
  },
];

export const AI_BUILDER_PROMPT_SAMPLES_KO = [
  'RSI 과매도 반등 + SMA20 상향 돌파일 때 롱 진입. TP 2.5%, SL 1.2%',
  'SMA50 위에서 MACD 히스토그램이 0 상향 돌파하면 롱, 최대 24봉 보유',
  'ADX 25 이상 추세장에서 Slow Stochastic 골든크로스면 롱',
];

export const AI_BUILDER_PROMPT_SAMPLES_EN = [
  'Enter long when RSI rebounds from oversold and price breaks above SMA20. TP 2.5%, SL 1.2%',
  'Go long when MACD histogram crosses above 0 while price is above SMA50, max hold 24 bars',
  'In ADX >= 25 trend regime, go long on Slow Stochastic golden cross',
];
