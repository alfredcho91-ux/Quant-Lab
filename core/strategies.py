# core/strategies.py

STRATS = [
    {
        "id": "Connors",
        "name_ko": "A1. Connors (RSI2 역추세)",
        "name_en": "A1. Connors (RSI2 Reversion)",
        "prefix": "Sig_Connors",
        "logic": "Connors",
    },
    {
        "id": "Sqz",
        "name_ko": "A2. Squeeze (변동성 폭발)",
        "name_en": "A2. Squeeze (Volatility Burst)",
        "prefix": "Sig_Sqz",
        "logic": "Squeeze",
    },
    {
        "id": "Turtle",
        "name_ko": "A3. Turtle (Donchian 추세)",
        "name_en": "A3. Turtle (Donchian Trend)",
        "prefix": "Sig_Turtle",
        "logic": "Fixed",
    },
    {
        "id": "MR",
        "name_ko": "A4. Mean Reversion (BB+RSI)",
        "name_en": "A4. Mean Reversion (BB+RSI)",
        "prefix": "Sig_MR",
        "logic": "Fixed",
    },
    {
        "id": "RSI",
        "name_ko": "B1. RSI Reversal (표준)",
        "name_en": "B1. RSI Reversal (Standard)",
        "prefix": "Sig_RSI",
        "logic": "Fixed",
    },
    {
        "id": "MA",
        "name_ko": "B2. MA Cross (MA1↔MA2↔MA3)",
        "name_en": "B2. MA Cross (MA1↔MA2↔MA3)",
        "prefix": "Sig_MA",
        "logic": "Fixed",
    },
    {
        "id": "BB",
        "name_ko": "B3. BB Breakout (돌파)",
        "name_en": "B3. BB Breakout",
        "prefix": "Sig_BB",
        "logic": "Fixed",
    },
    {
        "id": "Engulf",
        "name_ko": "B4. Engulfing (장악형)",
        "name_en": "B4. Engulfing",
        "prefix": "Sig_Engulf",
        "logic": "Fixed",
    },
]