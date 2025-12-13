# core/candle_patterns.py

import numpy as np
import pandas as pd
from typing import Dict


def add_candle_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    캔들 패턴 탐지에 필요한 기본 특성 계산.
    - 양봉/음봉, 몸통 길이, 전체 길이, 꼬리 길이 등
    """
    df = df.copy()

    o = df["open"]
    h = df["high"]
    l = df["low"]
    c = df["close"]

    df["is_bull"] = c > o
    df["is_bear"] = c < o

    df["body"] = (c - o).abs()
    df["range"] = h - l

    df["body_top"] = np.where(df["is_bull"], c, o)
    df["body_bottom"] = np.where(df["is_bull"], o, c)

    df["upper_wick"] = h - df["body_top"]
    df["lower_wick"] = df["body_bottom"] - l

    df["body"] = df["body"].replace(0, 1e-8)
    df["range"] = df["range"].replace(0, 1e-8)

    df["body_rel_range"] = df["body"] / df["range"]

    return df


# =========================
# 개별 패턴들
# =========================

def bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    """상승 장악형"""
    prev = df.shift(1)

    prev_red = prev["is_bear"]
    curr_green = df["is_bull"]

    prev_top = prev[["open", "close"]].max(axis=1)
    prev_bot = prev[["open", "close"]].min(axis=1)
    curr_top = df[["open", "close"]].max(axis=1)
    curr_bot = df[["open", "close"]].min(axis=1)

    engulf = (curr_top >= prev_top) & (curr_bot <= prev_bot)
    return (prev_red & curr_green & engulf).fillna(False)


def bearish_engulfing(df: pd.DataFrame) -> pd.Series:
    """하락 장악형"""
    prev = df.shift(1)

    prev_green = prev["is_bull"]
    curr_red = df["is_bear"]

    prev_top = prev[["open", "close"]].max(axis=1)
    prev_bot = prev[["open", "close"]].min(axis=1)
    curr_top = df[["open", "close"]].max(axis=1)
    curr_bot = df[["open", "close"]].min(axis=1)

    engulf = (curr_top >= prev_top) & (curr_bot <= prev_bot)
    return (prev_green & curr_red & engulf).fillna(False)


def bullish_harami(df: pd.DataFrame) -> pd.Series:
    """상승 잉태형"""
    prev = df.shift(1)

    prev_red = prev["is_bear"]
    curr_green = df["is_bull"]

    prev_top = prev[["open", "close"]].max(axis=1)
    prev_bot = prev[["open", "close"]].min(axis=1)
    curr_top = df[["open", "close"]].max(axis=1)
    curr_bot = df[["open", "close"]].min(axis=1)

    inside = (curr_top <= prev_top) & (curr_bot >= prev_bot)
    return (prev_red & curr_green & inside).fillna(False)


def bearish_harami(df: pd.DataFrame) -> pd.Series:
    """하락 잉태형"""
    prev = df.shift(1)

    prev_green = prev["is_bull"]
    curr_red = df["is_bear"]

    prev_top = prev[["open", "close"]].max(axis=1)
    prev_bot = prev[["open", "close"]].min(axis=1)
    curr_top = df[["open", "close"]].max(axis=1)
    curr_bot = df[["open", "close"]].min(axis=1)

    inside = (curr_top <= prev_top) & (curr_bot >= prev_bot)
    return (prev_green & curr_red & inside).fillna(False)


def three_inside_up(df: pd.DataFrame) -> pd.Series:
    """
    상승 잉태 확인형 (Three Inside Up)
    - i-2: 음봉
    - i-1: 양봉, i-2 몸통 안에 포함
    - i: 양봉, i-1 종가 위로 마감
    """
    prev1 = df.shift(1)
    prev2 = df.shift(2)

    c1_red = prev2["is_bear"]
    c2_green = prev1["is_bull"]
    c3_green = df["is_bull"]

    c1_top = prev2[["open", "close"]].max(axis=1)
    c1_bot = prev2[["open", "close"]].min(axis=1)
    c2_top = prev1[["open", "close"]].max(axis=1)
    c2_bot = prev1[["open", "close"]].min(axis=1)

    inside = (c2_top <= c1_top) & (c2_bot >= c1_bot)
    confirm = c3_green & (df["close"] > prev1["close"])

    return (c1_red & c2_green & inside & confirm).fillna(False)


def hammer_bullish(df: pd.DataFrame) -> pd.Series:
    """
    양봉 망치형
    - 양봉
    - 아랫꼬리 >= 2 * 몸통
    - 윗꼬리 <= 0.5 * 몸통
    """
    cond = (
        df["is_bull"]
        & (df["lower_wick"] >= 2.0 * df["body"])
        & (df["upper_wick"] <= 0.5 * df["body"])
    )
    return cond.fillna(False)


def hanging_man(df: pd.DataFrame) -> pd.Series:
    """교수형"""
    small_body = df["body_rel_range"] <= 0.4
    long_lower = df["lower_wick"] >= 2.0 * df["body"]
    short_upper = df["upper_wick"] <= 0.5 * df["body"]
    cond = small_body & long_lower & short_upper
    return cond.fillna(False)


def doji_bullish(df: pd.DataFrame, max_body_ratio: float = 0.1) -> pd.Series:
    """십자형"""
    cond = df["body_rel_range"] <= max_body_ratio
    return cond.fillna(False)


def morning_star(df: pd.DataFrame) -> pd.Series:
    """모닝 스타 (단순 버전)"""
    prev1 = df.shift(1)
    prev2 = df.shift(2)

    c1_red = prev2["is_bear"]
    c3_green = df["is_bull"]
    small_body = prev1["body_rel_range"] <= 0.4

    c1_mid = (prev2["open"] + prev2["close"]) / 2.0
    c3_above_mid = df["close"] >= c1_mid

    cond = c1_red & small_body & c3_green & c3_above_mid
    return cond.fillna(False)


def evening_star(df: pd.DataFrame) -> pd.Series:
    """이브닝 스타 (단순 버전)"""
    prev1 = df.shift(1)
    prev2 = df.shift(2)

    c1_green = prev2["is_bull"]
    c3_red = df["is_bear"]
    small_body = prev1["body_rel_range"] <= 0.4

    c1_mid = (prev2["open"] + prev2["close"]) / 2.0
    c3_below_mid = df["close"] <= c1_mid

    cond = c1_green & small_body & c3_red & c3_below_mid
    return cond.fillna(False)


def three_white_soldiers(df: pd.DataFrame) -> pd.Series:
    """적삼병"""
    df1 = df.shift(1)
    df2 = df.shift(2)

    bull0 = df["is_bull"]
    bull1 = df1["is_bull"]
    bull2 = df2["is_bull"]

    cond_dir = bull0 & bull1 & bull2
    cond_close = (df["close"] > df1["close"]) & (df1["close"] > df2["close"])

    return (cond_dir & cond_close).fillna(False)


def three_black_crows(df: pd.DataFrame) -> pd.Series:
    """흑삼병"""
    df1 = df.shift(1)
    df2 = df.shift(2)

    red0 = df["is_bear"]
    red1 = df1["is_bear"]
    red2 = df2["is_bear"]

    cond_dir = red0 & red1 & red2
    cond_close = (df["close"] < df1["close"]) & (df1["close"] < df2["close"])

    return (cond_dir & cond_close).fillna(False)


def shooting_star(df: pd.DataFrame) -> pd.Series:
    """슈팅 스타"""
    small_body = df["body_rel_range"] <= 0.4
    long_upper = df["upper_wick"] >= 2.0 * df["body"]
    short_lower = df["lower_wick"] <= 0.5 * df["body"]
    cond = small_body & long_upper & short_lower
    return cond.fillna(False)


def get_pattern_signals(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    df를 받아서 모든 패턴에 대한 시그널을 묶어서 반환.
    반환 형식:
        {
            "Bullish Engulfing": {"direction": "bull", "signal": Series[bool]},
            ...
        }
    """
    df_feat = add_candle_features(df)

    patterns = {
        "Bullish Engulfing": {
            "direction": "bull",
            "signal": bullish_engulfing(df_feat),
        },
        "Bearish Engulfing": {
            "direction": "bear",
            "signal": bearish_engulfing(df_feat),
        },
        "Bullish Harami": {
            "direction": "bull",
            "signal": bullish_harami(df_feat),
        },
        "Bearish Harami": {
            "direction": "bear",
            "signal": bearish_harami(df_feat),
        },
        "Three Inside Up": {
            "direction": "bull",
            "signal": three_inside_up(df_feat),
        },
        "Hammer": {
            "direction": "bull",
            "signal": hammer_bullish(df_feat),
        },
        "Hanging Man": {
            "direction": "bear",
            "signal": hanging_man(df_feat),
        },
        "Doji (bullish)": {
            "direction": "bull",
            "signal": doji_bullish(df_feat),
        },
        "Morning Star": {
            "direction": "bull",
            "signal": morning_star(df_feat),
        },
        "Evening Star": {
            "direction": "bear",
            "signal": evening_star(df_feat),
        },
        "Three White Soldiers": {
            "direction": "bull",
            "signal": three_white_soldiers(df_feat),
        },
        "Three Black Crows": {
            "direction": "bear",
            "signal": three_black_crows(df_feat),
        },
        "Shooting Star": {
            "direction": "bear",
            "signal": shooting_star(df_feat),
        },
    }

    return patterns