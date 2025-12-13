// Labels and translations
import type { Language } from '../types';

export interface Labels {
  sidebar_title: string;
  sidebar_caption: string;
  coin_select: string;
  menu_title: string;
  menu_backtest: string;
  menu_pattern: string;
  menu_ma_cross: string;
  menu_journal: string;
  menu_scanner: string;
  menu_pattern_scanner: string;
  title_backtest: string;
  title_pattern: string;
  title_journal: string;
  price_help: string;
  interval: string;
  data_src: string;
  data_csv: string;
  data_api: string;
  leverage: string;
  fees_title: string;
  entry_fee: string;
  exit_fee: string;
  params: string;
  rsi14_ob: string;
  rsi2_ob: string;
  ema_len: string;
  sma1_len: string;
  sma2_len: string;
  adx_thr: string;
  donch: string;
  choose: string;
  strategy: string;
  direction: string;
  dir_opts: string[];
  expander_edu: string;
  edu_concept: string;
  edu_long: string;
  edu_short: string;
  edu_regime: string;
  edu_note: string;
  tp: string;
  sl: string;
  maxbars: string;
  no_data: string;
  summary: string;
  trades: string;
  winrate: string;
  cumret: string;
  liqcnt: string;
  regime_perf: string;
  equity: string;
  history: string;
  run_backtest: string;
  loading: string;
  fear_greed: string;
}

const labels_ko: Labels = {
  sidebar_title: '💎 월젬의 퀀트 마스터',
  sidebar_caption: '8 Strategies • RSI Single Knobs • Chart on Top',
  coin_select: '코인 선택',
  menu_title: '메뉴',
  menu_backtest: '🚀 백테스트',
  menu_pattern: '📈 패턴/캔들 통계',
  menu_ma_cross: '📊 MA 크로스 통계',
  menu_journal: '📝 매매 일지',
  menu_scanner: '📊 전략 스캐너',
  menu_pattern_scanner: '📡 패턴 스캐너',
  title_backtest: '{coin} 8개 전략 백테스트',
  title_pattern: '📈 패턴/캔들 통계 연구실',
  title_journal: '📝 매매 일지',
  price_help: 'CSV 보유: ',
  interval: '봉 기간',
  data_src: '데이터 소스',
  data_csv: '📂 CSV',
  data_api: '📡 API',
  leverage: '⚡ 레버리지',
  fees_title: '💸 수수료(%)',
  entry_fee: '진입 수수료(%)',
  exit_fee: '청산 수수료(%)',
  params: '🎛️ 파라미터',
  rsi14_ob: 'RSI(14) 과매수',
  rsi2_ob: 'RSI(2) 과매수',
  ema_len: 'EMA 길이',
  sma1_len: 'MA1 길이',
  sma2_len: 'MA2 길이',
  adx_thr: 'ADX 임계값',
  donch: 'Donchian 기간',
  choose: '🎮 전략 & 방향 선택',
  strategy: '전략',
  direction: '포지션',
  dir_opts: ['Long', 'Short'],
  expander_edu: '📘 전략 설명 (초보자용)',
  edu_concept: '개념',
  edu_long: '매수(롱) 규칙',
  edu_short: '매도(숏) 규칙',
  edu_regime: '유리한 장세',
  edu_note: '※ TP/SL, 최대보유봉, 수수료/레버리지는 아래 설정을 따릅니다.',
  tp: '익절 TP (%)',
  sl: '손절 SL (%)',
  maxbars: '최대 보유 봉 수',
  no_data: '⚠️ 해당 조건에서 신호가 없습니다. (타임프레임/파라미터를 조정해보세요)',
  summary: '결과 요약',
  trades: '거래 횟수',
  winrate: '승률',
  cumret: '누적 수익률',
  liqcnt: '청산 횟수',
  regime_perf: '장세별 성과',
  equity: '누적 수익률',
  history: '거래 내역',
  run_backtest: '백테스트 실행',
  loading: '로딩 중...',
  fear_greed: '공포/탐욕 지수',
};

const labels_en: Labels = {
  sidebar_title: '💎 WolGems Quant Master',
  sidebar_caption: '8 Strategies • RSI Single Knobs • Chart on Top',
  coin_select: 'Select Coin',
  menu_title: 'Menu',
  menu_backtest: '🚀 Backtest',
  menu_pattern: '📈 Pattern / Candle Stats',
  menu_ma_cross: '📊 MA Cross Stats',
  menu_journal: '📝 Trading Journal',
  menu_scanner: '📊 Strategy Scanner',
  menu_pattern_scanner: '📡 Pattern Scanner',
  title_backtest: '{coin} 8-Strategy Backtest',
  title_pattern: '📈 Pattern / Candle Statistics Lab',
  title_journal: '📝 Trading Journal',
  price_help: 'CSV available: ',
  interval: 'Candle Interval',
  data_src: 'Data Source',
  data_csv: '📂 CSV',
  data_api: '📡 API',
  leverage: '⚡ Leverage',
  fees_title: '💸 Fees (%)',
  entry_fee: 'Entry Fee (%)',
  exit_fee: 'Exit Fee (%)',
  params: '🎛️ Parameters',
  rsi14_ob: 'RSI(14) Overbought',
  rsi2_ob: 'RSI(2) Overbought',
  ema_len: 'EMA Length',
  sma1_len: 'MA1 Length',
  sma2_len: 'MA2 Length',
  adx_thr: 'ADX Threshold',
  donch: 'Donchian Lookback',
  choose: '🎮 Strategy & Direction',
  strategy: 'Strategy',
  direction: 'Direction',
  dir_opts: ['Long', 'Short'],
  expander_edu: '📘 Strategy Explainer (Beginner)',
  edu_concept: 'Concept',
  edu_long: 'Long Rule',
  edu_short: 'Short Rule',
  edu_regime: 'Best Regime',
  edu_note: '※ TP/SL, max bars, fees & leverage follow the settings below.',
  tp: 'Take-Profit TP (%)',
  sl: 'Stop-Loss SL (%)',
  maxbars: 'Max Holding Bars',
  no_data: '⚠️ No signals for these conditions. Try adjusting timeframe/parameters.',
  summary: 'Summary',
  trades: 'Trades',
  winrate: 'Win Rate',
  cumret: 'Total Return',
  liqcnt: 'Liquidations',
  regime_perf: 'Performance by Regime',
  equity: 'Equity Curve',
  history: 'Trade History',
  run_backtest: 'Run Backtest',
  loading: 'Loading...',
  fear_greed: 'Fear & Greed Index',
};

export function getLabels(lang: Language): Labels {
  return lang === 'ko' ? labels_ko : labels_en;
}

