# core/indicators.py
import numpy as np
import pandas as pd


def calculate_adx(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    ADX 계산 함수.
    app.py에서 쓰던 calculate_adx를 그대로 옮겨온 것입니다.
    """
    df = df.copy()
    h, l, c = df["high"], df["low"], df["close"]

    df["tr0"] = (h - l).abs()
    df["tr1"] = (h - c.shift(1)).abs()
    df["tr2"] = (l - c.shift(1)).abs()
    df["tr"] = df[["tr0", "tr1", "tr2"]].max(axis=1)

    up = h - h.shift(1)
    dn = l.shift(1) - l
    df["pdm"] = np.where((up > dn) & (up > 0), up, 0.0)
    df["mdm"] = np.where((dn > up) & (dn > 0), dn, 0.0)

    df["tr_s"] = df["tr"].rolling(length).sum()
    df["pdm_s"] = df["pdm"].rolling(length).sum()
    df["mdm_s"] = df["mdm"].rolling(length).sum()

    df["pdi"] = 100 * (df["pdm_s"] / (df["tr_s"] + 1e-10))
    df["mdi"] = 100 * (df["mdm_s"] / (df["tr_s"] + 1e-10))
    df["dx"] = 100 * (df["pdi"] - df["mdi"]).abs() / (df["pdi"] + df["mdi"] + 1e-10)
    return df["dx"].rolling(length).mean()


def prepare_strategy_data(
    df: pd.DataFrame,
    rsi_ob_level: int = 70,      # RSI(14) overbought (20~80); oversold = 100 - this
    rsi2_ob_level: int = 80,     # RSI(2) overbought (20~80); oversold = 100 - this
    ema_len: int = 200,
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
    rsi2_os_level = 100 - rsi2_ob_level

    # ───────── 추세: EMA / MA ─────────
    df["EMA_main"] = df["close"].ewm(span=ema_len, adjust=False).mean()
    df["SMA_1"] = df["close"].rolling(sma1_len).mean()
    df["SMA_2"] = df["close"].rolling(sma2_len).mean()
    df["SMA_200"] = df["close"].rolling(200).mean()  # 참고용

    # ───────── 모멘텀: RSI(14), RSI(2) ─────────
    d = df["close"].diff()
    g = (d.where(d > 0, 0)).rolling(14).mean()
    s = (-d.where(d < 0, 0)).rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + g / (s + 1e-10)))

    g2 = (d.where(d > 0, 0)).rolling(2).mean()
    s2 = (-d.where(d < 0, 0)).rolling(2).mean()
    df["RSI_2"] = 100 - (100 / (1 + g2 / (s2 + 1e-10)))

    # ───────── MACD (12, 26, 9 기본) ─────────
    ema_fast = df["close"].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=macd_slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=macd_signal, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    # ───────── ADX & Regime ─────────
    df["ADX"] = calculate_adx(df)
    df["Regime"] = np.select(
        [
            (df["ADX"] < adx_threshold),
            (df["ADX"] >= adx_threshold) & (df["close"] > df["EMA_main"]),
            (df["ADX"] >= adx_threshold) & (df["close"] <= df["EMA_main"]),
        ],
        ["Sideways", "Bull", "Bear"],
        default="Sideways",
    )

    # ───────── 변동성: Bollinger, Keltner, Squeeze ─────────
    df["BB_Mid"] = df["close"].rolling(bb_length).mean()
    df["BB_Std"] = df["close"].rolling(bb_length).std()
    df["BB_Up"] = df["BB_Mid"] + bb_std_mult * df["BB_Std"]
    df["BB_Low"] = df["BB_Mid"] - bb_std_mult * df["BB_Std"]

    df["TR"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs(),
        ),
    )
    df["ATR"] = df["TR"].rolling(atr_length).mean()
    df["KC_Up"] = df["BB_Mid"] + kc_mult * df["ATR"]
    df["KC_Low"] = df["BB_Mid"] - kc_mult * df["ATR"]
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
    df["Sig_Connors_Long"] = (df["close"] > df["EMA_main"]) & (
        df["RSI_2"] < rsi2_os_level
    )
    df["Sig_Connors_Short"] = (df["close"] < df["EMA_main"]) & (
        df["RSI_2"] > rsi2_ob_level
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
        df["close"] > df["EMA_main"]
    )
    df["Sig_Turtle_Short"] = (df["close"] < df["Donch_Low"]) & (
        df["close"] < df["EMA_main"]
    )

    df["Sig_MR_Long"] = (
        (df["close"] > df["EMA_main"])
        & (df["close"] < df["BB_Low"])
        & (df["RSI"] < rsi_os_level)
    )
    df["Sig_MR_Short"] = (
        (df["close"] < df["EMA_main"])
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
    df.attrs["RSI2_OB"] = rsi2_ob_level
    df.attrs["RSI2_OS"] = 100 - rsi2_ob_level
    df.attrs["EMA_LEN"] = ema_len
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