"""
주간 패턴 분석 설정 모듈

FilterConfig와 AnalysisConfig 클래스를 정의합니다.
"""

from dataclasses import dataclass
from typing import Optional
from strategy.weekly_pattern.indicators import IndicatorConfig

# 상수 정의
DEFAULT_DEEP_DROP_THRESHOLD = -0.05
DEFAULT_RSI_THRESHOLD = 40.0
DEFAULT_RSI_PERIOD = 14
DEFAULT_ATR_PERIOD = 14
DEFAULT_VOL_PERIOD = 20


@dataclass
class FilterConfig:
    """필터 설정"""
    direction: str = "down"  # "down" 또는 "up"
    deep_drop_threshold: float = DEFAULT_DEEP_DROP_THRESHOLD
    deep_rise_threshold: float = 0.05  # 깊은 상승 임계값 (+5%)
    rsi_threshold: float = DEFAULT_RSI_THRESHOLD
    
    def __post_init__(self):
        """유효성 검증"""
        if self.direction not in ["down", "up"]:
            raise ValueError(f"방향은 'down' 또는 'up'이어야 합니다: {self.direction}")
        if self.direction == "down" and self.deep_drop_threshold >= 0:
            raise ValueError(f"깊은 하락 임계값은 음수여야 합니다: {self.deep_drop_threshold}")
        if self.direction == "up" and self.deep_rise_threshold <= 0:
            raise ValueError(f"깊은 상승 임계값은 양수여야 합니다: {self.deep_rise_threshold}")
        if not (0 <= self.rsi_threshold <= 100):
            raise ValueError(f"RSI 임계값은 0-100 사이여야 합니다: {self.rsi_threshold}")


@dataclass
class AnalysisConfig:
    """분석 설정 (모든 설정 통합)"""
    coin: str
    deep_drop_threshold: float = DEFAULT_DEEP_DROP_THRESHOLD
    rsi_threshold: float = DEFAULT_RSI_THRESHOLD
    rsi_period: int = DEFAULT_RSI_PERIOD
    atr_period: int = DEFAULT_ATR_PERIOD
    vol_period: int = DEFAULT_VOL_PERIOD
    use_csv: bool = False  # 호환성 유지용
    direction: Optional[str] = None  # 선택적 방향 설정
    deep_rise_threshold: Optional[float] = None  # 선택적 상승 임계값
    
    def __post_init__(self):
        """유효성 검증"""
        if not self.coin:
            raise ValueError("코인 심볼은 필수입니다")
    
    @property
    def indicator_config(self) -> IndicatorConfig:
        """기술적 지표 설정 반환"""
        return IndicatorConfig(
            rsi_period=self.rsi_period,
            atr_period=self.atr_period,
            vol_period=self.vol_period
        )
    
    @property
    def filter_config(self) -> FilterConfig:
        """필터 설정 반환"""
        return FilterConfig(
            direction=self.direction or 'down',
            deep_drop_threshold=self.deep_drop_threshold,
            deep_rise_threshold=self.deep_rise_threshold or 0.05,
            rsi_threshold=self.rsi_threshold
        )
