"""
분석 컨텍스트 모듈

분석 파라미터를 불변 객체로 관리하는 Context 패턴 구현
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 상수 정의 (순환 참조 방지)
RSI_THRESHOLD_DEFAULT = 60.0

# 지원되는 interval 목록 (정규화용)
VALID_INTERVALS = {"1d", "12h", "4h", "1h", "15m", "30m", "2h", "3d", "1w", "8h", "1M"}

# 요일 이름 (월요일=0, 일요일=6)
WEEKDAY_NAMES_KO = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
WEEKDAY_NAMES_EN = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


@dataclass(frozen=True)
class AnalysisContext:
    """
    분석 컨텍스트 (불변 객체)
    
    SSOT: models/request.py의 StreakAnalysisParams와 필드 1:1 대응
    필드 추가/수정 시 양쪽 모두 수정 필요
    """
    coin: str
    interval: str
    n_streak: int
    direction: str
    use_complex_pattern: bool = False
    complex_pattern: Optional[List[int]] = None
    rsi_threshold: float = RSI_THRESHOLD_DEFAULT
    min_total_body_pct: Optional[float] = None  # N개 연속 봉의 몸통 총합 최소값
    timezone_offset: Optional[int] = None
    
    @classmethod
    def from_params(cls, params: Dict[str, Any]) -> 'AnalysisContext':
        """
        파라미터 딕셔너리로부터 Context 생성
        
        SSOT 단순화: StreakAnalysisParams와 필드명이 동일하므로
        직접 매핑 (누락 위험 최소화)
        
        Args:
            params: 파라미터 딕셔너리
        
        Returns:
            AnalysisContext 인스턴스
        """
        # interval 정규화 (유효하지 않은 값은 기본값 사용)
        interval = params.get('interval', '1d')
        if interval not in VALID_INTERVALS:
            logger.warning(f"Invalid interval '{interval}', using default '1d'")
            interval = '1d'
        
        return cls(
            coin=params.get('coin', 'SOL'),
            interval=interval,
            n_streak=params.get('n_streak', 6),
            direction=params.get('direction', 'green'),
            use_complex_pattern=params.get('use_complex_pattern', False),
            complex_pattern=params.get('complex_pattern'),
            rsi_threshold=params.get('rsi_threshold', RSI_THRESHOLD_DEFAULT),
            min_total_body_pct=params.get('min_total_body_pct'),
            timezone_offset=params.get('timezone_offset'),
        )
    
    def determine_mode(self) -> str:
        """
        Mode 결정 (simple 또는 complex)
        
        Returns:
            'simple' 또는 'complex'
        """
        if self.use_complex_pattern and self.complex_pattern and len(self.complex_pattern) > 0:
            return "complex"
        return "simple"
    
    def validate(self) -> Optional[Dict[str, Any]]:
        """
        Context 검증 - 에러가 있으면 에러 딕셔너리 반환, 없으면 None
        
        Returns:
            에러 딕셔너리 또는 None
        """
        if self.use_complex_pattern:
            if not self.complex_pattern or len(self.complex_pattern) == 0:
                return {
                    "success": False,
                    "error": "복합 패턴이 비어있습니다",
                    "message": "1차/2차 조건을 모두 설정해주세요",
                    "mode": "complex"
                }
            
            # 조정 구간 검증: 상승 구간과 하락 구간이 모두 있어야 함
            has_rise = any(x == 1 for x in self.complex_pattern)
            has_drop = any(x == -1 for x in self.complex_pattern)
            
            if not (has_rise and has_drop):
                return {
                    "success": False,
                    "error": "복합 패턴 분석 실패",
                    "message": "상승 구간과 조정 구간이 모두 필요합니다",
                    "suggestions": [
                        "1차 조건: 상승(양봉) 또는 하락(음봉)",
                        "2차 조건: 반대 방향 선택",
                        f"현재 패턴: {self.complex_pattern}"
                    ],
                    "pattern": self.complex_pattern,
                    "mode": "complex"
                }
        return None
