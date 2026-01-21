# models/request.py
"""Request models for API endpoints"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class StreakAnalysisParams(BaseModel):
    """
    연속봉 분석 파라미터 (SSOT: AnalysisContext와 1:1 대응)
    
    Note:
        필드 추가/수정 시 strategy/streak/common.py의 
        AnalysisContext도 함께 수정해야 함
    """
    coin: str = "SOL"
    interval: str = "1d"
    n_streak: int = 6
    direction: str = "green"
    # 복합 패턴 분석 옵션
    use_complex_pattern: bool = False
    complex_pattern: Optional[List[int]] = None  # 예: [1, 1, 1, 1, 1, -1, -1] (5양-2음)
    # 동적 필터 임계값 (확장성 개선)
    rsi_threshold: float = 60.0  # RSI 필터 임계값
    min_total_body_pct: Optional[float] = None  # N개 연속 봉의 몸통 총합 최소값 (예: 10.0 = 10% 이상)
    # 시간대 설정 (EST 기준, DST 자동 처리됨)
    timezone_offset: int = -5  # EST: -5, EDT: -4 (pytz로 자동 처리)


class BacktestParams(BaseModel):
    coin: str = "BTC"
    interval: str = "1h"
    strategy_id: str = "Connors"
    direction: str = "Long"
    tp_pct: float = 2.0
    sl_pct: float = 1.0
    max_bars: int = 48
    leverage: int = 10
    entry_fee_pct: float = 0.04
    exit_fee_pct: float = 0.04
    rsi_ob: int = 70
    rsi2_ob: int = 80
    ema_len: int = 200
    sma1_len: int = 20
    sma2_len: int = 60
    adx_thr: int = 25
    donch: int = 20
    bb_length: int = 20
    bb_std_mult: float = 2.0
    atr_length: int = 20
    kc_mult: float = 1.5
    vol_ma_length: int = 20
    vol_spike_k: float = 2.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    use_csv: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PresetSaveRequest(BaseModel):
    name: str
    coin: str
    interval: str
    strat_id: str
    direction: str
    params: Dict[str, Any]


class AdvancedBacktestParams(BaseModel):
    coin: str = "BTC"
    interval: str = "1h"
    strategy_id: str = "Connors"
    direction: str = "Long"
    tp_pct: float = 2.0
    sl_pct: float = 1.0
    max_bars: int = 48
    leverage: int = 10
    entry_fee_pct: float = 0.04
    exit_fee_pct: float = 0.04
    rsi_ob: int = 70
    rsi2_ob: int = 80
    ema_len: int = 200
    sma1_len: int = 20
    sma2_len: int = 60
    adx_thr: int = 25
    donch: int = 20
    bb_length: int = 20
    bb_std_mult: float = 2.0
    atr_length: int = 20
    kc_mult: float = 1.5
    vol_ma_length: int = 20
    vol_spike_k: float = 2.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    use_csv: bool = False
    # Advanced options
    train_ratio: float = 0.7  # 70% train, 30% test
    monte_carlo_runs: int = 1000


class PatternScanParams(BaseModel):
    coin: str = "BTC"
    intervals: List[str] = ["1h", "4h"]
    tp_pct: float = 1.0
    horizon: int = 3
    mode: str = "natural"  # "natural" or "position"
    position: str = "long"  # "long" or "short" (when mode="position")
    use_csv: bool = False


class ScannerParams(BaseModel):
    coin: str = "BTC"
    interval: str = "1h"
    strategies: List[str] = []  # Empty = all strategies
    use_csv: bool = False


class JournalEntry(BaseModel):
    datetime: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    direction: Optional[str] = None
    strategy_id: Optional[str] = None
    size: Optional[float] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    r_multiple: Optional[float] = None
    outcome: Optional[str] = None
    emotion: Optional[str] = None
    tags: Optional[str] = None
    mistakes: Optional[str] = None
    notes: Optional[str] = None


class WeeklyPatternParams(BaseModel):
    coin: str = "ETH"
    interval: str = "1d"  # 주간 분석이므로 1d 필수
    deep_drop_threshold: float = -0.05  # 깊은 하락 임계값 (-5%)
    rsi_threshold: float = 40  # 과매도 임계값
    use_csv: bool = False


class WeeklyPatternManualParams(BaseModel):
    """주간 패턴 수동 입력 백테스트 파라미터"""
    coin: str = "ETH"
    monday_open: float  # 월요일 시가
    tuesday_close: float  # 화요일 종가
    wednesday_date: str  # 수요일 날짜 (YYYY-MM-DD 형식, 수요일 시가를 찾기 위해 필요)
    use_csv: bool = False
