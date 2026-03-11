// Labels and translations
import type { Language } from '../types';

export interface Labels {
  sidebar_title: string;
  sidebar_caption: string;
  coin_select: string;
  menu_title: string;
  menu_backtest: string;
  menu_backtest_advanced: string;
  menu_strategy_scanner: string;
  menu_pattern: string;
  menu_bb_mid: string;
  menu_combo_filter: string;
  menu_multi_tf_squeeze: string;
  menu_journal: string;
  menu_scanner: string;
  menu_pattern_scanner: string;
  menu_streak_analysis: string;
  menu_trend_judgment: string;
  menu_ai_backtest_lab: string;
  menu_ai_backtest_builder: string;
  menu_hybrid_analysis: string;
  menu_weekly_pattern: string;
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
  sma_main_len: string;
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
  trading_principles_title: string;
  trading_principles: string[];
}

const labels_ko: Labels = {
  sidebar_title: '💎 퀀트 마스터',
  sidebar_caption: '8 Strategies • RSI Single Knobs • Chart on Top',
  coin_select: '코인 선택',
  menu_title: '메뉴',
  menu_backtest: '🚀 백테스트',
  menu_backtest_advanced: '🔬 고급 백테스트',
  menu_strategy_scanner: '📡 전략 스캐너',
  menu_pattern: '📈 패턴/캔들 통계',
  menu_bb_mid: '📊 볼밴 중단 터치',
  menu_combo_filter: '🧪 통합 필터 테스트',
  menu_multi_tf_squeeze: '📐 멀티 TF 스퀴즈',
  menu_journal: '📝 매매 일지',
  menu_scanner: '📊 전략 스캐너',
  menu_pattern_scanner: '🔍 패턴 스캐너',
  menu_streak_analysis: '🏹 연속 봉 분석',
  menu_trend_judgment: '📊 추세판단',
  menu_ai_backtest_lab: '🤖 AI 백테스트 랩',
  menu_ai_backtest_builder: '🛠️ AI 전략 빌더',
  menu_hybrid_analysis: '⚡ 하이브리드 전략',
  menu_weekly_pattern: '📅 주간 패턴 분석',
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
  sma_main_len: '메인 SMA 길이',
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
  trading_principles_title: '트레이딩 원칙',
  trading_principles: [
    '추세대로 친다 (쿠엉 등 참조).',
    '배율은 추세/역추세/자리 조건에 따라 다르게 적용한다.',
    '진입 타이밍은 큰 봉 마감 전후(4h/1d/1w)와 퀀트 베이스를 함께 본다.',
    '타점은 트레이딩 원칙대로만 실행한다.',
    '추세 합류 매매는 가능하되, 스토캐스틱과 위치(20이평 위/아래)를 반드시 확인한다.',
    '애매하면 안 탄다. 못 버티는 포지션은 진입하지 않는다.',
  ],
};

const labels_en: Labels = {
  sidebar_title: '💎 Quant Master',
  sidebar_caption: '8 Strategies • RSI Single Knobs • Chart on Top',
  coin_select: 'Select Coin',
  menu_title: 'Menu',
  menu_backtest: '🚀 Backtest',
  menu_backtest_advanced: '🔬 Advanced Backtest',
  menu_strategy_scanner: '📡 Strategy Scanner',
  menu_pattern: '📈 Pattern / Candle Stats',
  menu_bb_mid: '📊 BB Mid Touch',
  menu_combo_filter: '🧪 Combo Filter Test',
  menu_multi_tf_squeeze: '📐 Multi-TF Squeeze',
  menu_journal: '📝 Trading Journal',
  menu_scanner: '📊 Strategy Scanner',
  menu_pattern_scanner: '🔍 Pattern Scanner',
  menu_streak_analysis: '🏹 Candle Streak',
  menu_trend_judgment: '📊 Trend Judgment',
  menu_ai_backtest_lab: '🤖 AI Backtest Lab',
  menu_ai_backtest_builder: '🛠️ AI Strategy Builder',
  menu_hybrid_analysis: '⚡ Hybrid Strategy',
  menu_weekly_pattern: '📅 Weekly Pattern',
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
  sma_main_len: 'Main SMA Length',
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
  trading_principles_title: 'Trading Principles',
  trading_principles: [
    'Trade with the trend (reference: Kuung, etc.).',
    'Adjust leverage by context: trend, counter-trend, and key price zone.',
    'Time entries around large-candle close (4h/1d/1w) with quant confirmation.',
    'Execute entries only according to your trading playbook.',
    'Trend-following entries are allowed, but confirm Stochastic and 20-MA position first.',
    'If ambiguous, skip. Do not enter positions you cannot hold.',
  ],
};

export function getLabels(lang: Language): Labels {
  return lang === 'ko' ? labels_ko : labels_en;
}
