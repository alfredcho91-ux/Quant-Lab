# routes/strategies.py
"""전략 관련 API"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from core.strategies import STRATS
from core.presets import load_presets, save_presets

router = APIRouter(prefix="/api", tags=["strategies"])


class PresetSaveRequest(BaseModel):
    name: str
    coin: str
    interval: str
    strat_id: str
    direction: str
    params: Dict[str, Any]


STRATEGY_EXPLANATIONS = {
    "Connors": {
        "ko": {
            "concept": "RSI(2)가 극단적으로 낮을 때(과매도) 가격 반등을 기대하고 매수. 단기 mean-reversion.",
            "Long": "RSI(2) < (100-RSI2_OB) 이면 매수",
            "Short": "RSI(2) > RSI2_OB 이면 매도",
            "regime": "횡보장/레인지 장세 (ADX 낮을 때)",
        },
        "en": {
            "concept": "Buy when RSI(2) is extremely low (oversold) expecting price bounce. Short-term mean-reversion.",
            "Long": "Buy when RSI(2) < (100-RSI2_OB)",
            "Short": "Sell when RSI(2) > RSI2_OB",
            "regime": "Range-bound market (low ADX)",
        },
    },
    "BB_OS": {
        "ko": {
            "concept": "볼린저밴드 하단 이탈 시 과매도로 보고 반등 매수. 밴드 회귀 전략.",
            "Long": "종가 < BB 하단 이면 매수",
            "Short": "종가 > BB 상단 이면 매도",
            "regime": "횡보장 (변동성 축소 후 확대 구간)",
        },
        "en": {
            "concept": "Buy when price breaks below BB lower band (oversold), expecting reversion to mean.",
            "Long": "Buy when close < BB Lower",
            "Short": "Sell when close > BB Upper",
            "regime": "Range market (after volatility contraction)",
        },
    },
}


@router.get("/strategies")
async def api_strategies():
    """Get list of available strategies"""
    try:
        return {"success": True, "data": STRATS}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


@router.get("/strategy-info/{strategy_id}")
async def api_strategy_info(
    strategy_id: str,
    lang: str = "ko",
    rsi_ob: int = 70,
    rsi2_ob: int = 80,
    ema_len: int = 200,
    sma1_len: int = 20,
    sma2_len: int = 60,
):
    """Get detailed explanation for a strategy"""
    rsi_os = 100 - rsi_ob
    rsi2_os = 100 - rsi2_ob
    
    explainers_ko = {
        "Connors": {
            "concept": "아주 짧은 RSI(2)로 극단의 과매도/과매수 구간에서 반등(되돌림)을 노리는 전략.",
            "Long": f"RSI(2) < {rsi2_os} & 가격 > EMA({ema_len}). 청산: TP/SL 또는 SMA({sma1_len}) 재돌파.",
            "Short": f"RSI(2) > {rsi2_ob} & 가격 < EMA({ema_len}). 청산: TP/SL 또는 SMA({sma1_len}) 재하향.",
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
    
    explainers_en = {
        "Connors": {
            "concept": "Very short RSI(2) reversion to capture snapbacks after extreme moves.",
            "Long": f"RSI(2) < {rsi2_os} & price > EMA({ema_len}). Exit: TP/SL or price crosses above SMA({sma1_len}) again.",
            "Short": f"RSI(2) > {rsi2_ob} & price < EMA({ema_len}). Exit: TP/SL or price crosses below SMA({sma1_len}) again.",
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
    
    explainers = explainers_ko if lang == "ko" else explainers_en
    
    if strategy_id not in explainers:
        return {"success": False, "error": f"Strategy {strategy_id} not found"}
    
    return {"success": True, "data": explainers[strategy_id]}


@router.get("/presets")
async def api_get_presets():
    """Get all saved presets"""
    try:
        presets = load_presets()
        return {"success": True, "data": presets}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/presets")
async def api_save_preset(request: PresetSaveRequest):
    """Save a preset"""
    try:
        presets = load_presets()
        presets[request.name] = {
            "coin": request.coin,
            "interval": request.interval,
            "strat_id": request.strat_id,
            "direction": request.direction,
            "params": request.params,
            }
        save_presets(presets)
        return {"success": True, "message": "Preset saved"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/presets/{name}")
async def api_delete_preset(name: str):
    """Delete a preset"""
    try:
        presets = load_presets()
        if name in presets:
            del presets[name]
            save_presets(presets)
        return {"success": True, "message": "Preset deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}
