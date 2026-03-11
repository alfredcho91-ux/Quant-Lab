# core/indicators.py
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Literal, Optional


def set_bollinger_columns(
    df: pd.DataFrame,
    mid: pd.Series,
    upper: pd.Series,
    lower: pd.Series,
) -> pd.DataFrame:
    """
    볼린저 밴드 컬럼 명을 대문자/소문자 스키마로 동시 유지한다.
    - legacy: BB_Mid / BB_Up / BB_Low
    - newer:  BB_mid / BB_upper / BB_lower
    """
    df["BB_Mid"] = mid
    df["BB_Up"] = upper
    df["BB_Low"] = lower

    df["BB_mid"] = mid
    df["BB_upper"] = upper
    df["BB_lower"] = lower
    return df


def _true_range(df: pd.DataFrame) -> pd.Series:
    """표준 True Range 계산."""
    prev_close = df["close"].shift(1)
    return pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def compute_rsi_wilder(series: pd.Series, length: int = 14) -> pd.Series:
    """Wilder(RMA) 방식 RSI."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where(avg_gain != 0, 0.0)
    return rsi


def compute_atr_wilder(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Wilder(RMA) 방식 ATR."""
    tr = _true_range(df)
    return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def compute_adx_wilder(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Wilder(RMA) 방식 ADX."""
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    atr = compute_atr_wilder(df, length=length)
    plus_di = 100 * (
        plus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
        / atr.replace(0, np.nan)
    )
    minus_di = 100 * (
        minus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
        / atr.replace(0, np.nan)
    )
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def calculate_adx(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    ADX 계산 함수 (하위 호환용).

    내부 구현은 compute_adx_wilder()와 동일하게 유지해,
    전략/라이브 지표 간 계산식 불일치를 방지한다.
    """
    return compute_adx_wilder(df, length=length)


def prepare_strategy_data(
    df: pd.DataFrame,
    rsi_ob_level: int = 70,      # RSI(14) overbought (20~80); oversold = 100 - this
    sma_main_len: int = 200,
    sma1_len: int = 20,
    sma2_len: int = 60,
    adx_threshold: int = 25,
    donch_lookback: int = 20,
    # 🔹 변동성 파라미터 (볼밴/ATR/KC)
    bb_length: int = 20,
    bb_std_mult: float = 2.0,
    atr_length: int = 20,
    kc_mult: float = 1.5,
    # 🔹 거래량 파라미터 (거래량 MA + 스파이크)
    vol_ma_length: int = 20,
    vol_spike_k: float = 2.0,
    # 🔹 MACD 파라미터
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
) -> pd.DataFrame:
    """
    전략용 데이터 준비 함수.
    app.py에 있던 prepare_strategy_data를 그대로 옮겨온 것입니다.
    """
    if len(df) < 100:
        return df

    df = df.copy()

    rsi_os_level = 100 - rsi_ob_level
    # ───────── 추세: SMA / MA ─────────
    df["SMA_main"] = df["close"].rolling(sma_main_len).mean()
    df["SMA_1"] = df["close"].rolling(sma1_len).mean()
    df["SMA_2"] = df["close"].rolling(sma2_len).mean()
    df["SMA_200"] = df["close"].rolling(200).mean()  # 참고용

    # ───────── 모멘텀: RSI(14, Wilder) ─────────
    df["RSI"] = compute_rsi_wilder(df["close"], length=14)

    # ───────── MACD (12, 26, 9 기본) ─────────
    ema_fast = df["close"].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=macd_slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=macd_signal, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    # ───────── ADX & Regime (Wilder) ─────────
    df["ADX"] = compute_adx_wilder(df, length=14)
    df["Regime"] = np.select(
        [
            (df["ADX"] < adx_threshold),
            (df["ADX"] >= adx_threshold) & (df["close"] > df["SMA_main"]),
            (df["ADX"] >= adx_threshold) & (df["close"] <= df["SMA_main"]),
        ],
        ["Sideways", "Bull", "Bear"],
        default="Sideways",
    )

    # ───────── 변동성: Bollinger, Keltner, Squeeze ─────────
    bb_mid = df["close"].rolling(bb_length).mean()
    bb_std = df["close"].rolling(bb_length).std()
    bb_up = bb_mid + bb_std_mult * bb_std
    bb_low = bb_mid - bb_std_mult * bb_std
    set_bollinger_columns(df, bb_mid, bb_up, bb_low)
    df["BB_Std"] = bb_std

    df["TR"] = _true_range(df)
    df["ATR"] = compute_atr_wilder(df, length=atr_length)
    df["KC_Up"] = bb_mid + kc_mult * df["ATR"]
    df["KC_Low"] = bb_mid - kc_mult * df["ATR"]
    df["Squeeze_On"] = (df["BB_Up"] < df["KC_Up"]) & (df["BB_Low"] > df["KC_Low"])

    # ───────── Donchian ─────────
    df["Donch_High"] = df["high"].rolling(donch_lookback).max().shift(1)
    df["Donch_Low"] = df["low"].rolling(donch_lookback).min().shift(1)

    # ───────── 캔들 패턴 헬퍼 ─────────
    df["Open_Prev"] = df["open"].shift(1)
    df["Close_Prev"] = df["close"].shift(1)

    # ───────── 거래량 지표: Volume MA & Spike ─────────
    df["Vol_MA"] = df["volume"].rolling(vol_ma_length).mean()
    df["Vol_Spike"] = df["volume"] > (vol_spike_k * df["Vol_MA"])

    # ───────── 시그널들 ─────────
    df["Sig_Connors_Long"] = (df["close"] > df["SMA_main"]) & (
        df["RSI"] < rsi_os_level
    )
    df["Sig_Connors_Short"] = (df["close"] < df["SMA_main"]) & (
        df["RSI"] > rsi_ob_level
    )

    df["Sig_Sqz_Long"] = (
        (df["Squeeze_On"].shift(1) == True)
        & (df["Squeeze_On"] == False)
        & (df["close"] > df["BB_Mid"])
    )
    df["Sig_Sqz_Short"] = (
        (df["Squeeze_On"].shift(1) == True)
        & (df["Squeeze_On"] == False)
        & (df["close"] < df["BB_Mid"])
    )

    df["Sig_Turtle_Long"] = (df["close"] > df["Donch_High"]) & (
        df["close"] > df["SMA_main"]
    )
    df["Sig_Turtle_Short"] = (df["close"] < df["Donch_Low"]) & (
        df["close"] < df["SMA_main"]
    )

    df["Sig_MR_Long"] = (
        (df["close"] > df["SMA_main"])
        & (df["close"] < df["BB_Low"])
        & (df["RSI"] < rsi_os_level)
    )
    df["Sig_MR_Short"] = (
        (df["close"] < df["SMA_main"])
        & (df["close"] > df["BB_Up"])
        & (df["RSI"] > rsi_ob_level)
    )

    df["Sig_RSI_Long"] = df["RSI"] < rsi_os_level
    df["Sig_RSI_Short"] = df["RSI"] > rsi_ob_level

    df["Sig_MA_Long"] = (df["SMA_1"] > df["SMA_2"]) & (
        df["SMA_1"].shift(1) <= df["SMA_2"].shift(1)
    )
    df["Sig_MA_Short"] = (df["SMA_1"] < df["SMA_2"]) & (
        df["SMA_1"].shift(1) >= df["SMA_2"].shift(1)
    )

    df["Sig_BB_Long"] = (df["close"] > df["BB_Up"]) & (
        df["close"].shift(1) <= df["BB_Up"].shift(1)
    )
    df["Sig_BB_Short"] = (df["close"] < df["BB_Low"]) & (
        df["close"].shift(1) >= df["BB_Low"].shift(1)
    )

    engulf_bull = (df["open"] <= df["Close_Prev"]) & (
        df["close"] >= df["Open_Prev"]
    )
    engulf_bear = (df["open"] >= df["Close_Prev"]) & (
        df["close"] <= df["Open_Prev"]
    )
    df["Sig_Engulf_Long"] = (
        (df["Close_Prev"] < df["Open_Prev"])
        & (df["close"] > df["open"])
        & engulf_bull
    )
    df["Sig_Engulf_Short"] = (
        (df["Close_Prev"] > df["Open_Prev"])
        & (df["close"] < df["open"])
        & engulf_bear
    )

    # attrs (정보용)
    df.attrs["RSI_OB"] = rsi_ob_level
    df.attrs["RSI_OS"] = 100 - rsi_ob_level
    df.attrs["SMA_MAIN_LEN"] = sma_main_len
    df.attrs["SMA1_LEN"] = sma1_len
    df.attrs["SMA2_LEN"] = sma2_len
    df.attrs["BB_LEN"] = bb_length
    df.attrs["BB_STD"] = bb_std_mult
    df.attrs["ATR_LEN"] = atr_length
    df.attrs["KC_MULT"] = kc_mult
    df.attrs["VOL_MA_LEN"] = vol_ma_length
    df.attrs["VOL_SPIKE_K"] = vol_spike_k
    df.attrs["MACD_FAST"] = macd_fast
    df.attrs["MACD_SLOW"] = macd_slow
    df.attrs["MACD_SIGNAL"] = macd_signal

    return df


def compute_rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index) 계산 함수.
    내부적으로 Wilder's Smoothing(compute_rsi_wilder)을 사용하여
    전략/백테스트 엔진과 일관성을 유지합니다.
    
    Args:
        series: 가격 시리즈 (보통 close)
        length: RSI 기간 (기본값: 14)
    
    Returns:
        RSI 값 시리즈
    """
    return compute_rsi_wilder(series, length)


def calculate_smas(df: pd.DataFrame, pairs: List[List[int]]) -> pd.DataFrame:
    """
    필요한 SMA들을 계산하여 DataFrame에 추가
    
    Args:
        df: OHLCV DataFrame
        pairs: SMA 길이 쌍 리스트 (예: [[5, 20], [20, 60]])
    
    Returns:
        SMA 컬럼이 추가된 DataFrame
    """
    df = df.copy()
    all_lengths = sorted({x for pair in pairs for x in pair})
    for length in all_lengths:
        col = f"SMA{length}"
        if col not in df.columns:
            df[col] = df["close"].rolling(length, min_periods=length).mean()
    return df


def add_bb_indicators(
    df: pd.DataFrame,
    bb_length: int = 20,
    bb_std_mult: float = 2.0,
    rsi_length: int = 14,
    sma200_length: int = 200,
) -> pd.DataFrame:
    """
    BB, RSI, SMA200 인디케이터를 계산하여 DataFrame에 추가
    
    Args:
        df: OHLCV DataFrame
        bb_length: 볼린저밴드 기간 (기본값: 20)
        bb_std_mult: 볼린저밴드 표준편차 배수 (기본값: 2.0)
        rsi_length: RSI 기간 (기본값: 14)
        sma200_length: SMA200 기간 (기본값: 200)
    
    Returns:
        BB, RSI, SMA200, 터치 플래그가 추가된 DataFrame
    """
    df = df.copy()
    close = df["close"]
    mid = close.rolling(window=bb_length, min_periods=bb_length).mean()
    std = close.rolling(window=bb_length, min_periods=bb_length).std()
    upper = mid + bb_std_mult * std
    lower = mid - bb_std_mult * std
    set_bollinger_columns(df, mid, upper, lower)
    # Use Wilder RSI to stay consistent with backtest/trend engines.
    df["RSI"] = compute_rsi_wilder(close, length=rsi_length)
    df["SMA200"] = close.rolling(window=sma200_length, min_periods=sma200_length).mean()
    
    # Touch flags
    low, high = df["low"], df["high"]
    df["touch_lower"] = low <= df["BB_lower"]
    df["touch_mid"] = (low <= df["BB_mid"]) & (high >= df["BB_mid"])
    df["touch_upper"] = high >= df["BB_upper"]
    return df


def add_combo_indicators(df: pd.DataFrame, sma_short: int, sma_long: int) -> pd.DataFrame:
    """
    Combo Filter를 위한 인디케이터들을 계산하여 DataFrame에 추가
    (SMA, BB, RSI, 캔들 패턴 특성)
    
    Args:
        df: OHLCV DataFrame
        sma_short: 단기 SMA 기간
        sma_long: 장기 SMA 기간
    
    Returns:
        SMA, BB, RSI, 캔들 패턴 특성이 추가된 DataFrame
    """
    df = df.copy()
    close = df["close"]
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    
    # SMA
    df[f"SMA{sma_short}"] = close.rolling(window=sma_short, min_periods=sma_short).mean()
    df[f"SMA{sma_long}"] = close.rolling(window=sma_long, min_periods=sma_long).mean()
    
    # BB
    mid = close.rolling(window=20, min_periods=20).mean()
    std = close.rolling(window=20, min_periods=20).std()
    upper = mid + 2.0 * std
    lower = mid - 2.0 * std
    set_bollinger_columns(df, mid, upper, lower)
    # Use Wilder RSI to stay consistent with backtest/trend engines.
    df["RSI"] = compute_rsi_wilder(close, length=14)
    
    # Full candle features (matching candle_patterns.add_candle_features)
    df["is_bull"] = c > o
    df["is_bear"] = c < o
    df["body"] = (c - o).abs()
    df["range"] = h - l
    
    # Replace zeros to avoid division errors
    df["body"] = df["body"].replace(0, 1e-8)
    df["range"] = df["range"].replace(0, 1e-8)
    
    # Body top/bottom for wick calculations
    df["body_top"] = np.where(df["is_bull"], c, o)
    df["body_bottom"] = np.where(df["is_bull"], o, c)
    
    # Wicks
    df["upper_wick"] = h - df["body_top"]
    df["lower_wick"] = df["body_bottom"] - l
    
    # Body relative to range (important for patterns)
    df["body_rel_range"] = df["body"] / df["range"]

    return df


def compute_live_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    실시간 지표 계산 (고정밀 지표 계산)
    
    하이브리드 전략 및 다른 전략에서 공통으로 사용할 수 있는 지표 계산 함수.
    Wilder's Smoothing을 적용한 고정밀 지표 계산 (SMA, MACD, RSI, ADX 등).
    
    일반 분석, 백테스팅, 라이브 모드 모두에서 사용 가능합니다.
    
    Args:
        df: OHLCV DataFrame
    
    Returns:
        지표가 추가된 DataFrame
    """
    d = df.copy()
    
    # 이평선
    d['sma20'] = d['close'].rolling(20).mean()
    d['sma50'] = d['close'].rolling(50).mean()
    d['sma100'] = d['close'].rolling(100).mean()
    d['sma200'] = d['close'].rolling(200).mean()
    
    # MACD
    ema12 = d['close'].ewm(span=12, adjust=False).mean()
    ema26 = d['close'].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    d['macd_hist'] = macd_line - macd_line.ewm(span=9, adjust=False).mean()
    
    # RSI/ADX/ATR (Wilder) - 전략 엔진과 동일 공식 사용
    d['rsi'] = compute_rsi_wilder(d['close'], length=14)
    d['adx'] = compute_adx_wilder(d, length=14)
    d['atr'] = compute_atr_wilder(d, length=14)
    d['atr_pct'] = (d['atr'] / d['close'].replace(0, np.nan)) * 100.0

    return d


def compute_stoch_rsi(series: pd.Series, rsi_period: int = 14, stoch_k: int = 3, stoch_d: int = 3) -> tuple[pd.Series, pd.Series]:
    """
    Stochastic RSI 계산 (RSI에 Stochastic 적용)
    Returns: (stoch_k, stoch_d)
    """
    rsi = compute_rsi(series, length=rsi_period)
    # Stoch RSI standard:
    # 1) RSI range window uses rsi_period
    # 2) %K/%D smoothing use stoch_k/stoch_d respectively
    rsi_min = rsi.rolling(window=rsi_period, min_periods=rsi_period).min()
    rsi_max = rsi.rolling(window=rsi_period, min_periods=rsi_period).max()
    stoch = 100 * (rsi - rsi_min) / (rsi_max - rsi_min + 1e-10)
    stoch_k_series = stoch.rolling(window=stoch_k, min_periods=stoch_k).mean()
    stoch_d_series = stoch_k_series.rolling(window=stoch_d, min_periods=stoch_d).mean()
    return stoch_k_series, stoch_d_series


def compute_slow_stochastic(
    df: pd.DataFrame,
    length: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """
    가격 기반 Slow Stochastic 계산 (TradingView ta.highest/lowest + sma 스무딩과 동일 계열)
    Returns: (slow_k, slow_d)
    """
    highest_high = df["high"].rolling(window=length, min_periods=length).max()
    lowest_low = df["low"].rolling(window=length, min_periods=length).min()
    denominator = (highest_high - lowest_low).replace(0, np.nan)

    fast_k = 100.0 * (df["close"] - lowest_low) / denominator
    slow_k = fast_k.rolling(window=smooth_k, min_periods=smooth_k).mean()
    slow_d = slow_k.rolling(window=smooth_d, min_periods=smooth_d).mean()
    return slow_k, slow_d


def compute_vwap_rolling(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """롤링 윈도우 VWAP: (H+L+C)/3 * volume의 이동 평균"""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    if "volume" not in df.columns:
        return typical.rolling(window).mean()  # volume 없으면 typical price MA
    tp_vol = typical * df["volume"]
    return tp_vol.rolling(window).sum() / (df["volume"].rolling(window).sum() + 1e-10)


def compute_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> tuple[pd.Series, pd.Series]:
    """
    Supertrend (Wilder ATR 기반) - 표준 알고리즘
    Returns: (supertrend_line, direction: 1=uptrend, -1=downtrend)
    """
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    atr = pd.Series(tr, index=df.index).ewm(alpha=1 / period, adjust=False).mean().values
    hl2 = (h + l) / 2
    basic_ub = hl2 + multiplier * atr
    basic_lb = hl2 - multiplier * atr
    final_ub = np.full(n, np.nan)
    final_lb = np.full(n, np.nan)
    st = np.full(n, np.nan)
    final_ub[period - 1] = basic_ub[period - 1]
    final_lb[period - 1] = basic_lb[period - 1]
    st[period - 1] = final_ub[period - 1]
    for i in range(period, n):
        if basic_ub[i] < final_ub[i - 1] or c[i - 1] > final_ub[i - 1]:
            final_ub[i] = basic_ub[i]
        else:
            final_ub[i] = final_ub[i - 1]
        if basic_lb[i] > final_lb[i - 1] or c[i - 1] < final_lb[i - 1]:
            final_lb[i] = basic_lb[i]
        else:
            final_lb[i] = final_lb[i - 1]
        prev_was_ub = not np.isnan(st[i - 1]) and abs(st[i - 1] - final_ub[i - 1]) < 1e-9
        if prev_was_ub:
            if c[i] <= final_ub[i]:
                st[i] = final_ub[i]
            else:
                st[i] = final_lb[i]
        else:
            if c[i] >= final_lb[i]:
                st[i] = final_lb[i]
            else:
                st[i] = final_ub[i]
    direction = np.where(c > st, 1, -1)
    return pd.Series(st, index=df.index), pd.Series(direction, index=df.index)


def compute_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Quant Lab 등 공용 분석용 지표 계산 (레거시 함수명 유지)
    - 3 Stoch RSI (5-3-3, 10-6-6, 20-12-12)
    - RSI(14), MACD, ADX (compute_live_indicators)
    - VWAP(롤링 20)
    - Supertrend(10, 3)

    주의:
    - Trend Judgment API(/api/trend-indicators)는 이 함수를 사용하지 않는다.
    - Trend Judgment는 compute_trend_judgment_indicators()를 통해
      Slow Stochastic(가격 기반)로 계산한다.
    """
    d = compute_live_indicators(df.copy())
    close = d["close"]
    sk1, sd1 = compute_stoch_rsi(close, 5, 3, 3)
    sk2, sd2 = compute_stoch_rsi(close, 10, 6, 6)
    sk3, sd3 = compute_stoch_rsi(close, 20, 12, 12)
    d["stoch_rsi_5k"], d["stoch_rsi_5d"] = sk1, sd1
    d["stoch_rsi_10k"], d["stoch_rsi_10d"] = sk2, sd2
    d["stoch_rsi_20k"], d["stoch_rsi_20d"] = sk3, sd3
    d["vwap_20"] = compute_vwap_rolling(d, 20)
    st, dr = compute_supertrend(d, 10, 3.0)
    d["supertrend"] = st
    d["supertrend_dir"] = dr
    return d


def compute_quant_lab_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Quant Lab 호출부 명확화를 위한 명시적 별칭 함수.

    내부 계산은 compute_trend_indicators(Stoch RSI 기반)와 동일하다.
    """
    return compute_trend_indicators(df)


def compute_trend_judgment_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    추세판단 페이지 전용 지표 계산
    - 3 Slow Stochastic (20-12-12, 10-6-6, 5-3-3)  # Pine B2S2 sto 기준
    - RSI(14), MACD, ADX (compute_live_indicators)
    - VWAP(롤링 20)
    - Supertrend(10, 3)
    """
    d = compute_live_indicators(df.copy())

    k20, d20 = compute_slow_stochastic(d, length=20, smooth_k=12, smooth_d=12)
    k10, d10 = compute_slow_stochastic(d, length=10, smooth_k=6, smooth_d=6)
    k5, d5 = compute_slow_stochastic(d, length=5, smooth_k=3, smooth_d=3)

    # 정식 필드: Slow Stochastic (가격 기반)
    d["slow_stoch_20k"], d["slow_stoch_20d"] = k20, d20
    d["slow_stoch_10k"], d["slow_stoch_10d"] = k10, d10
    d["slow_stoch_5k"], d["slow_stoch_5d"] = k5, d5

    d["vwap_20"] = compute_vwap_rolling(d, 20)
    st, dr = compute_supertrend(d, 10, 3.0)
    d["supertrend"] = st
    d["supertrend_dir"] = dr
    return d


def build_indicator_adapter(
    df: pd.DataFrame,
    mode: Literal["backtest", "trend_judgment", "quant_lab"] = "backtest",
    prepare_kwargs: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    백테스트/추세판단/AI 분석에서 공통으로 사용하는 지표 어댑터.

    - backtest: 전략 시그널/백테스트용 prepare_strategy_data 결과
    - trend_judgment: prepare_strategy_data + 추세판단 전용 지표(slow_stoch_*)
    - quant_lab: prepare_strategy_data + Stoch RSI 계열 지표(stoch_rsi_*)
    """
    base = prepare_strategy_data(df.copy(), **(prepare_kwargs or {}))

    if mode == "backtest":
        return base
    if mode == "trend_judgment":
        return compute_trend_judgment_indicators(base)
    if mode == "quant_lab":
        return compute_trend_indicators(base)
    raise ValueError(f"Unsupported indicator adapter mode: {mode}")


def get_latest_indicator_values(df: pd.DataFrame, use_previous_candle: bool = True) -> dict:
    """
    완성된 봉의 지표 값만 추출 (라이브 모드용)
    
    다른 전략에서도 재사용 가능한 공통 함수입니다.
    
    Args:
        df: 지표가 포함된 DataFrame
        use_previous_candle: True면 전 봉(완성된 봉) 사용, False면 최신 봉 사용
    
    Returns:
        완성된 봉의 지표 값 딕셔너리
    """
    if len(df) == 0:
        return {}
    
    # 완성된 전 봉 사용 (기본값)
    if use_previous_candle and len(df) >= 2:
        candle_idx = -2
    else:
        candle_idx = -1
    
    latest = df.iloc[candle_idx]
    timestamp = df.index[candle_idx]
    
    return {
        'timestamp': timestamp,
        'close': float(latest['close']) if not pd.isna(latest['close']) else None,
        'sma20': float(latest['sma20']) if 'sma20' in latest and not pd.isna(latest['sma20']) else None,
        'sma50': float(latest['sma50']) if 'sma50' in latest and not pd.isna(latest['sma50']) else None,
        'sma100': float(latest['sma100']) if 'sma100' in latest and not pd.isna(latest['sma100']) else None,
        'sma200': float(latest['sma200']) if 'sma200' in latest and not pd.isna(latest['sma200']) else None,
        'macd_hist': float(latest['macd_hist']) if 'macd_hist' in latest and not pd.isna(latest['macd_hist']) else None,
        'rsi': float(latest['rsi']) if 'rsi' in latest and not pd.isna(latest['rsi']) else None,
        'adx': float(latest['adx']) if 'adx' in latest and not pd.isna(latest['adx']) else None,
    }
