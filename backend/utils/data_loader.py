# utils/data_loader.py
"""공통 데이터 로딩 유틸리티 함수"""

import pandas as pd
from typing import Optional, Tuple
from utils.data_service import fetch_live_data, load_csv_data


def load_data_for_analysis(
    coin: str,
    interval: str,
    use_csv: bool = False,
    total_candles: int = 3000
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    분석용 데이터를 로딩하는 공통 함수
    
    Args:
        coin: 코인 심볼 (예: 'BTC')
        interval: 타임프레임 (예: '1h')
        use_csv: CSV 사용 여부
        total_candles: API에서 가져올 봉 개수
    
    Returns:
        (DataFrame, source): 데이터프레임과 데이터 소스 ('csv' 또는 'api')
    
    Raises:
        ValueError: 데이터 로딩 실패 시
    """
    df = None
    source = "api"
    
    # CSV에서 로딩 시도
    if use_csv:
        df, _ = load_csv_data(coin, interval)
        if df is not None and not df.empty:
            source = "csv"
            return df, source
    
    # API에서 로딩
    if df is None or df.empty:
        df = fetch_live_data(f"{coin}/USDT", interval, total_candles=total_candles)
        source = "api"
    
    # 데이터 검증
    if df is None or df.empty:
        raise ValueError(f"Failed to load data for {coin}/{interval}")
    
    return df, source


def load_data_for_multi_intervals(
    coin: str,
    intervals: list[str],
    use_csv: bool = False,
    total_candles: int = 500
) -> dict[str, pd.DataFrame]:
    """
    여러 타임프레임의 데이터를 한 번에 로딩
    
    Args:
        coin: 코인 심볼
        intervals: 타임프레임 리스트
        use_csv: CSV 사용 여부
        total_candles: API에서 가져올 봉 개수
    
    Returns:
        dict: {interval: DataFrame} 형태의 딕셔너리
    """
    results = {}
    
    for interval in intervals:
        try:
            df, _ = load_data_for_analysis(coin, interval, use_csv, total_candles)
            results[interval] = df
        except ValueError:
            # 특정 타임프레임 로딩 실패 시 건너뛰기
            continue
    
    return results
