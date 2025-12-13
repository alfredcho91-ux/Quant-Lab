# core/ui_common.py

from typing import Dict, List


def get_strategy_explainer(
    lang: str,
    rsi_ob: int,
    rsi2_ob: int,
    ema_len: int,
    sma1_len: int,
    sma2_len: int,
) -> Dict[str, Dict[str, str]]:
    """
    전략 설명 텍스트 (한국어 / English)
    """
    rsi_os = 100 - rsi_ob
    rsi2_os = 100 - rsi2_ob

    if lang == "English":
        return {
            "Connors": {
                "concept": "Very short RSI(2) reversion to capture snapbacks after extreme moves.",
                "Long": (
                    f"RSI(2) < {rsi2_os} & price > EMA({ema_len}). "
                    f"Exit: TP/SL or price crosses above SMA({sma1_len}) again."
                ),
                "Short": (
                    f"RSI(2) > {rsi2_ob} & price < EMA({ema_len}). "
                    f"Exit: TP/SL or price crosses below SMA({sma1_len}) again."
                ),
                "regime": "Range to mild trend; after panic drops/pumps.",
            },
            "Sqz": {
                "concept": "Volatility contraction (BB inside KC) followed by expansion = trend ignition.",
                "Long": "Squeeze was ON and just released; close > BB mid.",
                "Short": "Squeeze was ON and just released; close < BB mid.",
                "regime": "Right after volatility squeeze.",
            },
            "Turtle": {
                "concept": "Donchian breakout trend-following.",
                "Long": "Close breaks recent Donchian High & close > EMA.",
                "Short": "Close breaks recent Donchian Low & close < EMA.",
                "regime": "Strong Bull/Bear trends; beware whipsaws in ranges.",
            },
            "MR": {
                "concept": "Mean reversion after overshoot beyond the bands.",
                "Long": f"Close < BB low & RSI(14) < {rsi_os} & close > EMA.",
                "Short": f"Close > BB upper & RSI(14) > {rsi_ob} & close < EMA.",
                "regime": "Sideways or right after volatility blow-off.",
            },
            "RSI": {
                "concept": "Simple RSI(14) reversal using a single threshold.",
                "Long": f"RSI(14) < {rsi_os}.",
                "Short": f"RSI(14) > {rsi_ob}.",
                "regime": "Ranges/boxes.",
            },
            "MA": {
                "concept": "SMA1/SMA2 golden/death cross.",
                "Long": f"SMA({sma1_len}) crosses up SMA({sma2_len}).",
                "Short": f"SMA({sma1_len}) crosses down SMA({sma2_len}).",
                "regime": "Gentle emerging trends.",
            },
            "BB": {
                "concept": "Bollinger band breakout as momentum trigger.",
                "Long": "Close breaks the upper band (was below in prior bar).",
                "Short": "Close breaks the lower band (was above in prior bar).",
                "regime": "Early momentum phases.",
            },
            "Engulf": {
                "concept": "Bullish/Bearish engulfing candlestick reversal.",
                "Long": "Prev red, current green; current body engulfs previous body.",
                "Short": "Prev green, current red; current body engulfs previous body.",
                "regime": "Short-term reversals around turning points.",
            },
        }

    # ───────────────── 한국어 ─────────────────
    return {
        "Connors": {
            "concept": "아주 짧은 RSI(2)로 극단의 과매도/과매수 구간에서 반등(되돌림)을 노리는 전략.",
            "Long": (
                f"RSI(2) < {rsi2_os} & 가격 > EMA({ema_len}). "
                f"청산: TP/SL 또는 SMA({sma1_len}) 재돌파."
            ),
            "Short": (
                f"RSI(2) > {rsi2_ob} & 가격 < EMA({ema_len}). "
                f"청산: TP/SL 또는 SMA({sma1_len}) 재하향."
            ),
            "regime": "횡보~약한 추세, 급등락 직후 기술적 반등/반납.",
        },
        "Sqz": {
            "concept": "BB가 KC 안으로 들어가는 스퀴즈 후 재확장 시 추세 시작을 탄다.",
            "Long": "직전까지 스퀴즈 ON, 현재 해제 + 종가 BB 중단선 위.",
            "Short": "직전까지 스퀴즈 ON, 현재 해제 + 종가 BB 중단선 아래.",
            "regime": "변동성 수축 직후.",
        },
        "Turtle": {
            "concept": "Donchian 고가/저가 돌파 추세 추종.",
            "Long": "종가가 Donchian High 상향 돌파 & EMA 위.",
            "Short": "종가가 Donchian Low 하향 돌파 & EMA 아래.",
            "regime": "강한 불/베어 추세에 유리, 횡보 시 휩쏘 주의.",
        },
        "MR": {
            "concept": "밴드 밖 오버슈팅 후 평균 회귀.",
            "Long": f"종가 < BB 하단 & RSI(14) < {rsi_os} & EMA 위.",
            "Short": f"종가 > BB 상단 & RSI(14) > {rsi_ob} & EMA 아래.",
            "regime": "횡보 또는 과열 직후.",
        },
        "RSI": {
            "concept": "RSI(14) 단일 임계 기반 역추세 진입.",
            "Long": f"RSI(14) < {rsi_os}.",
            "Short": f"RSI(14) > {rsi_ob}.",
            "regime": "박스권/횡보.",
        },
        "MA": {
            "concept": "SMA1/SMA2 골든·데드 크로스.",
            "Long": f"SMA({sma1_len})가 SMA({sma2_len}) 상향 교차.",
            "Short": f"SMA({sma1_len})가 SMA({sma2_len}) 하향 교차.",
            "regime": "완만한 추세 발생/전환.",
        },
        "BB": {
            "concept": "볼밴 돌파를 모멘텀 시그널로 사용.",
            "Long": "상단 밴드 상향 돌파(이전 봉은 하단).",
            "Short": "하단 밴드 하향 돌파(이전 봉은 상단).",
            "regime": "초기 모멘텀.",
        },
        "Engulf": {
            "concept": "장악형 캔들 반전 패턴.",
            "Long": "이전 음봉 + 현재 양봉, 현재 몸통이 이전 몸통 장악.",
            "Short": "이전 양봉 + 현재 음봉, 현재 몸통이 이전 몸통 장악.",
            "regime": "전환 초입 단기 반전.",
        },
    }


def get_labels(lang: str, csv_tfs: List[str]) -> Dict[str, object]:
    """
    화면에 쓰이는 문자열/라벨 모음 (한국어 / English)
    """
    csv_info = ", ".join(csv_tfs) if csv_tfs else ("None" if lang == "English" else "없음")

    if lang == "English":
        return {
            "sidebar_title": "💎 WolGem's Quant Master",
            "sidebar_caption": "8 Strategies • RSI Single Knobs • Chart on Top",
            "coin_select": "Select Coin",
            "menu_title": "Menu",
            "menu_backtest": "🚀 Backtest",
            "menu_pattern": "📈 Pattern / Candle Stats",
            "menu_ma_cross": "📊 MA Cross Stats",
            "menu_journal": "📝 Trading Journal",          # ← 매매 일지 메뉴
            "menu_scanner": "📊 Strategy Scanner",
            "menu_pattern_scanner": "📡 Pattern Scanner",

            "title_backtest": "🚀 {coin} 8-Strategy Backtest",
            "title_pattern": "📈 Pattern / Candle Statistics Lab",
            "title_journal": "📝 Trading Journal",          # ← 매매 일지 타이틀

            "journal_new_entry": "New Journal Entry",
            "journal_list": "Past Entries",

            "price_help": "CSV available: " + csv_info,
            "interval": "Candle Interval",
            "data_src": "Data Source",
            "data_csv": "📂 CSV",
            "data_api": "📡 API",

            "leverage": "⚡ Leverage",
            "fees_title": "### 💸 Fees (%)",
            "entry_fee": "Entry Fee (%)",
            "exit_fee": "Exit Fee (%)",

            "params": "🎛️ Parameters",
            "rsi14_ob": "RSI(14) Overbought (Oversold=100-this)",
            "rsi2_ob": "RSI(2) Overbought (Oversold=100-this)",
            "ema_len": "EMA Length",
            "sma1_len": "SMA1 Length",
            "sma2_len": "SMA2 Length",
            "adx_thr": "ADX Threshold (Regime)",
            "donch": "Donchian Lookback (Turtle)",

            "choose": "🎮 Strategy & Direction",
            "strategy": "Strategy",
            "direction": "Direction",
            "dir_opts": ["Long", "Short"],

            "expander_edu": "📘 Strategy Explainer (Beginner)",
            "edu_concept": "**Concept**",
            "edu_long": "**Long Rule**",
            "edu_short": "**Short Rule**",
            "edu_regime": "**Best Regime**",
            "edu_note": "※ TP/SL, max bars, fees & leverage follow the settings below.",

            "tp": "Take-Profit TP (%)",
            "sl": "Stop-Loss SL (%)",
            "maxbars": "Max Holding Bars",

            "no_data": "⚠️ No signals for these conditions. Try adjusting timeframe/parameters.",
            "summary": "### 📊 Summary",
            "trades": "Trades",
            "winrate": "Win Rate",
            "cumret": "Final Return (CAGR-like)",
            "liqcnt": "Liquidations",

            "regime_perf": "### 🗺️ Performance by Regime",
            "equity": "### 📈 Equity Curve",
            "history": "### 📝 Trade History",

            "scanner_title": "📊 Live Strategy Scanner (8)",
            "scanner_timeframe": "Timeframe",
            "scanner_update": "Update",

            "regime_map_title": "🗺️ Market Regime Map",
            "regime_map_chart_title": "Price & Regime (ADX + EMA filter)",
        }

    # ───────────────── 한국어 라벨 ─────────────────
    return {
        "sidebar_title": "💎 월젬의 퀀트 마스터",
        "sidebar_caption": "8 Strategies • RSI Single Knobs • Chart on Top",
        "coin_select": "코인 선택",
        "menu_title": "메뉴",
        "menu_backtest": "🚀 백테스트",
        "menu_pattern": "📈 패턴/캔들 통계",
        "menu_ma_cross": "📊 MA 크로스 통계",
        "menu_journal": "📝 매매 일지",              # ← 매매 일지 메뉴
        "menu_scanner": "📊 전략 스캐너",
        "menu_pattern_scanner": "📡 패턴 스캐너",

        "title_backtest": "🚀 {coin} 8개 전략 백테스트",
        "title_pattern": "📈 패턴/캔들 통계 연구실",
        "title_journal": "📝 매매 일지",             # ← 매매 일지 타이틀

        "journal_new_entry": "새 매매 일지 작성",
        "journal_list": "이전 일지 목록",

        "price_help": "CSV 보유: " + csv_info,
        "interval": "봉 기간",
        "data_src": "데이터 소스",
        "data_csv": "📂 CSV",
        "data_api": "📡 API",

        "leverage": "⚡ 레버리지",
        "fees_title": "### 💸 수수료(%)",
        "entry_fee": "진입 수수료(%)",
        "exit_fee": "청산 수수료(%)",

        "params": "🎛️ 파라미터",
        "rsi14_ob": "RSI(14) 과매수 (과매도=100-이값)",
        "rsi2_ob": "RSI(2) 과매수 (과매도=100-이값)",
        "ema_len": "EMA 길이",
        "sma1_len": "SMA1 길이",
        "sma2_len": "SMA2 길이",
        "adx_thr": "ADX 임계값 (장세구분)",
        "donch": "Donchian 기간 (Turtle)",

        "choose": "🎮 전략 & 방향 선택",
        "strategy": "전략",
        "direction": "포지션",
        "dir_opts": ["Long", "Short"],

        "expander_edu": "📘 전략 설명 (초보자용)",
        "edu_concept": "**개념**",
        "edu_long": "**매수(롱) 규칙**",
        "edu_short": "**매도(숏) 규칙**",
        "edu_regime": "**유리한 장세**",
        "edu_note": "※ TP/SL, 최대보유봉, 수수료/레버리지는 아래 설정을 따릅니다.",

        "tp": "익절 TP (%)",
        "sl": "손절 SL (%)",
        "maxbars": "최대 보유 봉 수",

        "no_data": "⚠️ 해당 조건에서 신호가 없습니다. (타임프레임/파라미터를 조정해보세요)",
        "summary": "### 📊 결과 요약",
        "trades": "거래 횟수",
        "winrate": "승률",
        "cumret": "최종 수익률(복리)",
        "liqcnt": "청산 횟수",

        "regime_perf": "### 🗺️ 장세별 성과",
        "equity": "### 📈 누적 수익률",
        "history": "### 📝 거래 내역",

        "scanner_title": "📊 실시간 전략 스캐너 (8)",
        "scanner_timeframe": "Timeframe",
        "scanner_update": "Update",

        "regime_map_title": "🗺️ Market Regime Map",
        "regime_map_chart_title": "가격과 장세(ADX + EMA 필터)",
    }