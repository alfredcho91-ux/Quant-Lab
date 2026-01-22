"""
하이브리드 전략 백테스팅 엔진

현실적인 TP/SL 기반 매매 시뮬레이션
"""

import pandas as pd
from typing import Dict, Any, Optional, List
import logging

from strategy.hybrid.logic import compute_refined_indicators, generate_strategy_signals
from strategy.common import calculate_profit_factor

logger = logging.getLogger(__name__)


def run_realistic_backtest(
    df: pd.DataFrame,
    signal: pd.Series,
    tp: float = 2.0,
    sl: float = 1.0,
    max_hold: int = 5,
) -> pd.DataFrame:
    """
    현실적 매매 시뮬레이션 엔진
    
    Args:
        df: OHLCV DataFrame
        signal: 진입 시그널 (boolean Series)
        tp: 익절 비율 (%)
        sl: 손절 비율 (%)
        max_hold: 최대 보유 기간 (봉 수)
    
    Returns:
        거래 결과 DataFrame
    """
    trades = []
    
    for i in range(len(df) - max_hold):
        if not signal.iloc[i]:
            continue
        
        entry_price = df['close'].iloc[i]
        tp_price = entry_price * (1 + tp / 100)
        sl_price = entry_price * (1 - sl / 100)
        
        exit_price = None
        reason = 'Time'
        hold_time = max_hold
        
        # 미래 봉을 하나씩 탐색하며 TP/SL 체크
        for j in range(1, max_hold + 1):
            curr_idx = i + j
            if curr_idx >= len(df):
                break
            
            # 손절 먼저 체크 (보수적 접근)
            if df['low'].iloc[curr_idx] <= sl_price:
                exit_price = sl_price
                reason = 'SL'
                hold_time = j
                break
            # 익절 체크
            elif df['high'].iloc[curr_idx] >= tp_price:
                exit_price = tp_price
                reason = 'TP'
                hold_time = j
                break
        
        if exit_price is None:
            exit_price = df['close'].iloc[i + max_hold]
        
        # 수익률 계산
        gross_return = ((exit_price - entry_price) / entry_price) * 100
        net_return = gross_return
        
        trades.append({
            'entry_idx': i,
            'exit_idx': i + hold_time,
            'entry_price': float(entry_price),
            'exit_price': float(exit_price),
            'pnl': float(net_return),
            'gross_pnl': float(gross_return),
            'reason': reason,
            'hold': hold_time,
            'is_win': net_return > 0,
        })
    
    return pd.DataFrame(trades)


def run_hybrid_backtest(
    df: pd.DataFrame,
    coin: str,
    interval: str,
    strategy: str,
    tp: float = 2.0,
    sl: float = 1.0,
    max_hold: int = 5,
) -> Dict[str, Any]:
    """
    하이브리드 전략 백테스팅
    
    Args:
        df: OHLCV DataFrame
        coin: 코인 심볼
        interval: 시간프레임
        strategy: 전략 이름
        tp: 익절 비율 (%)
        sl: 손절 비율 (%)
        max_hold: 최대 보유 기간
    
    Returns:
        백테스팅 결과 딕셔너리
    """
    try:
        # 지표 계산
        df_with_indicators = compute_refined_indicators(df)
        df_with_indicators = df_with_indicators.dropna()
        
        if len(df_with_indicators) == 0:
            return {
                "success": False,
                "error": "지표 계산 후 유효한 데이터가 없습니다"
            }
        
        # 시그널 생성
        signals = generate_strategy_signals(df_with_indicators)
        
        if strategy not in signals:
            return {
                "success": False,
                "error": f"알 수 없는 전략: {strategy}"
            }
        
        signal = signals[strategy]
        
        # 백테스팅 실행
        trades_df = run_realistic_backtest(
            df_with_indicators,
            signal,
            tp=tp,
            sl=sl,
            max_hold=max_hold,
        )
        
        if len(trades_df) == 0:
            return {
                "success": True,
                "coin": coin,
                "interval": interval,
                "strategy": strategy,
                "total_candles": len(df_with_indicators),
                "trades": [],
                "summary": {
                    "n_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "avg_pnl": 0,
                    "max_pnl": 0,
                    "min_pnl": 0,
                    "profit_factor": None,
                },
                "warnings": ["거래가 발생하지 않았습니다"],
            }
        
        # 통계 계산
        wins = trades_df[trades_df['is_win']]
        losses = trades_df[~trades_df['is_win']]
        
        win_rate = (len(wins) / len(trades_df) * 100) if len(trades_df) > 0 else 0
        total_pnl = float(trades_df['pnl'].sum())
        avg_pnl = float(trades_df['pnl'].mean())
        max_pnl = float(trades_df['pnl'].max())
        min_pnl = float(trades_df['pnl'].min())
        
        profit_factor = calculate_profit_factor(trades_df['pnl'])
        
        # TP/SL 통계
        tp_hit_rate = (trades_df['reason'] == 'TP').mean() * 100 if len(trades_df) > 0 else 0
        sl_hit_rate = (trades_df['reason'] == 'SL').mean() * 100 if len(trades_df) > 0 else 0
        time_exit_rate = (trades_df['reason'] == 'Time').mean() * 100 if len(trades_df) > 0 else 0
        
        return {
            "success": True,
            "coin": coin,
            "interval": interval,
            "strategy": strategy,
            "total_candles": len(df_with_indicators),
            "trades": trades_df.to_dict('records'),
            "summary": {
                "n_trades": len(trades_df),
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "max_pnl": round(max_pnl, 2),
                "min_pnl": round(min_pnl, 2),
                "profit_factor": float(profit_factor) if profit_factor is not None else None,
                "tp_hit_rate": round(tp_hit_rate, 2),
                "sl_hit_rate": round(sl_hit_rate, 2),
                "time_exit_rate": round(time_exit_rate, 2),
                "avg_hold": round(trades_df['hold'].mean(), 2),
            },
        }
        
    except Exception as e:
        logger.error(f"하이브리드 백테스팅 중 오류: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
