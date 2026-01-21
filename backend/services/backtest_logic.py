# services/backtest_logic.py
"""백테스트 비즈니스 로직 - FastAPI 독립적"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy import stats
import sys
from pathlib import Path

# strategy 모듈 import를 위한 경로 설정
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from strategy.common import (
    calculate_sharpe_ratio_unified,
    calculate_max_drawdown_unified,
    calculate_t_test_unified,
    calculate_profit_factor,
)


def calculate_advanced_stats(trades_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate advanced statistics for backtest results (리팩토링: 통합 함수 사용)."""
    if trades_df.empty:
        return {
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "max_drawdown": None,
            "max_drawdown_pct": None,
            "profit_factor": None,
            "avg_win": None,
            "avg_loss": None,
            "win_loss_ratio": None,
            "t_statistic": None,
            "p_value": None,
            "is_significant": False,
        }
    
    pnls = trades_df["PnL"].values
    n_trades = len(pnls)
    pnls_series = pd.Series(pnls)
    
    # Basic stats
    mean_pnl = np.mean(pnls)
    std_pnl = np.std(pnls, ddof=1) if n_trades > 1 else 0
    
    # Sharpe Ratio (통합 함수 사용)
    sharpe = calculate_sharpe_ratio_unified(pnls_series, period='daily')
    
    # Sortino Ratio (using downside deviation)
    negative_pnls = pnls[pnls < 0]
    downside_std = np.std(negative_pnls, ddof=1) if len(negative_pnls) > 1 else 0
    sortino = (mean_pnl / downside_std * np.sqrt(252)) if downside_std > 0 else None
    
    # Max Drawdown (통합 함수 사용 - cumsum 방식)
    mdd_result = calculate_max_drawdown_unified(pnls_series, method='cumsum')
    max_dd = mdd_result.get("max_drawdown")
    max_dd_pct = mdd_result.get("max_drawdown_pct")
    
    # Profit Factor (통합 함수 사용)
    profit_factor = calculate_profit_factor(pnls_series)
    
    # Win/Loss averages
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    avg_win = float(np.mean(wins)) if len(wins) > 0 else 0
    avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0
    win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else None
    
    # T-test (통합 함수 사용)
    t_test_result = calculate_t_test_unified(pnls_series)
    t_stat = t_test_result.get("t_statistic")
    p_value = t_test_result.get("p_value")
    is_significant = t_test_result.get("is_significant", False)
    
    return {
        "sharpe_ratio": float(sharpe) if sharpe is not None else None,
        "sortino_ratio": float(sortino) if sortino is not None else None,
        "max_drawdown": float(max_dd * 100) if max_dd is not None else None,  # as percentage
        "max_drawdown_pct": float(max_dd_pct) if max_dd_pct is not None else None,
        "profit_factor": float(profit_factor) if profit_factor is not None else None,
        "avg_win": float(avg_win * 100),
        "avg_loss": float(avg_loss * 100),
        "win_loss_ratio": float(win_loss_ratio) if win_loss_ratio is not None else None,
        "t_statistic": float(t_stat) if t_stat is not None else None,
        "p_value": float(p_value) if p_value is not None else None,
        "is_significant": is_significant,
    }


def run_monte_carlo(pnls: np.ndarray, n_runs: int = 1000) -> Dict[str, Any]:
    """Run Monte Carlo simulation by shuffling trade order."""
    if len(pnls) < 5:
        return {
            "mean_final_pnl": None,
            "ci_lower": None,
            "ci_upper": None,
            "worst_case": None,
            "best_case": None,
        }
    
    final_pnls = []
    max_dds = []
    
    for _ in range(n_runs):
        shuffled = np.random.permutation(pnls)
        cumulative = np.cumsum(shuffled)
        final_pnls.append(cumulative[-1])
        
        peak = np.maximum.accumulate(cumulative)
        dd = peak - cumulative
        max_dds.append(np.max(dd))
    
    final_pnls = np.array(final_pnls)
    
    return {
        "mean_final_pnl": float(np.mean(final_pnls) * 100),
        "ci_lower": float(np.percentile(final_pnls, 2.5) * 100),
        "ci_upper": float(np.percentile(final_pnls, 97.5) * 100),
        "worst_case": float(np.min(final_pnls) * 100),
        "best_case": float(np.max(final_pnls) * 100),
        "median_max_dd": float(np.median(max_dds) * 100),
    }
