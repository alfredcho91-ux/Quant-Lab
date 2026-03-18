# Backend Sharing Guide

> Summary reference for anyone taking over or extending the Quant-Lab backend.

## Project Overview

Quant-Lab backend is a FastAPI service for crypto market analysis, strategy execution, and quant research workflows.

- Framework: FastAPI 0.109
- Language: Python 3.9+
- Key libraries: Pandas, NumPy, SciPy, CCXT, Pydantic
- Default port: `8000`

## Critical Invariants

### 1. DatetimeIndex normalization

- Location: `backend/strategy/streak/common.py` via `normalize_indices()`
- Rule: every analysis DataFrame must carry a `DatetimeIndex`
- Do not remove index validation or allow mixed index types in analytical paths

### 2. C1 extraction logic

- Pattern completion time is not the analysis target
- The analysis target is the next candle after completion: `C1` (`T+1`)
- Key locations:
  - `backend/strategy/streak/simple_strategy.py`
  - `backend/strategy/streak/complex_strategy.py`
- Do not rewrite the logic to analyze the completion candle directly

### 3. Wilson score interval

- Location: `backend/strategy/streak/statistics.py` via `wilson_confidence_interval()`
- Baseline confidence setting: `z = 1.96` for 95% confidence
- Do not change the formula or remove the low-reliability treatment for small samples

### 4. Bonferroni correction

- Location: `backend/strategy/streak/statistics.py` via `analyze_interval_statistics()`
- Formula: `alpha_adjusted = alpha / n_comparisons`
- Default high-probability minimum sample: `DEFAULT_HIGH_PROB_MIN_SAMPLE = 10`
- Do not remove multiple-comparison correction

### 5. New York timezone conversion

- Location: `backend/strategy/streak/statistics.py` via `calculate_intraday_distribution()`
- Implementation: `pytz.timezone("America/New_York")` for automatic DST handling
- Do not replace this with manual EST/EDT offset arithmetic

## Backend Layout

```text
backend/
├── main.py
├── modules/
│   ├── ai_lab/
│   ├── backtest/
│   ├── journal/
│   ├── market/
│   ├── preset/
│   ├── scanner/
│   ├── stats/
│   ├── strategy_info/
│   ├── streak/
│   └── support_resistance/
├── services/
│   ├── ai_clients.py
│   ├── pattern_logic.py
│   └── statistics.py
├── strategy/
│   ├── bb_mid/
│   ├── combo_filter/
│   ├── hybrid/
│   └── streak/
├── utils/
│   ├── cache.py
│   ├── data_loader.py
│   ├── data_service.py
│   └── decorators.py
└── config/
    ├── settings.py
    └── strategies.yaml
```

Project-root shared logic:

```text
core/
├── backtest.py
├── indicators.py
└── strategies.py
```

## Major APIs

### Streak analysis

- `POST /api/streak-analysis`
- Parameters include `coin`, `interval`, `n_streak`, `direction`, `use_complex_pattern`, `complex_pattern`, and `rsi_threshold`
- Main logic lives under `backend/strategy/streak/`

### Hybrid strategy

- `POST /api/hybrid-analysis`
- `POST /api/hybrid-backtest`
- `POST /api/hybrid-live`
- Main logic lives under `backend/strategy/hybrid/logic.py`
- Shared indicator path: `core/indicators.py::compute_live_indicators()`

### BB mid

- `POST /api/bb-mid`
- Main logic lives under `backend/strategy/bb_mid/`

### Combo filter

- `POST /api/combo-filter`
- Main logic lives under `backend/strategy/combo_filter/`

### Backtest

- `POST /api/backtest`
- `POST /api/backtest-advanced`
- Engine: `core/backtest.py`

## Key Modules

### Data loading

- `backend/utils/data_loader.py`
- CSV-first with API fallback
- Includes DataFrame normalization for analysis

### Indicator calculation

- `core/indicators.py`
- Shared functions such as `compute_live_indicators()`
- Reused across hybrid and other strategy paths

### Strategy signal generation

- `backend/strategy/hybrid/logic.py`
- `generate_strategy_signals()` handles multiple strategy templates

### Shared statistics

- `backend/services/statistics.py`
- Quant helpers for profit factor, Sharpe ratio, drawdown, and related calculations

### Caching

- `backend/utils/cache.py`
- TTL-based caching for data and analysis reuse

## Dependencies

Core packages from `requirements.txt`:

```text
fastapi>=0.109.0
uvicorn[standard]
pydantic>=2.5.0
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.11.0
ccxt>=4.0.0
pytz>=2023.3
```

## Configuration

Primary environment settings from `config/settings.py`:

- `CORS_ORIGINS`
- `DEBUG_STREAK_ANALYSIS`
- `BINANCE_DATA_PATH`
- `CACHE_TTL`
- `TIMEZONE_OFFSET`

## Tests

Run the backend suite:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Important regression coverage:

- `tests/test_c1_extraction.py`
- `tests/test_statistics.py`

## Editing Rules

1. Normalize DataFrame indexes before running analytics.
2. Keep `C1` defined as the candle after pattern completion.
3. Preserve statistical formulas such as Wilson score and Bonferroni correction.
4. Preserve timezone conversion through New York timezone handling.
5. Keep shared indicator code reusable across strategies.

## Recent Changes (2026-01)

### Hybrid live mode

- Added `analyze_live_mode()`
- Uses the most recently completed candle instead of the still-forming candle
- Moved reusable indicator work into `core/indicators.py`

### Cleanup

- Removed unused imports
- Reduced duplicated code via `_prepare_indicators_and_signals()`
- Consolidated `compute_refined_indicators` into `compute_live_indicators`

## Related Docs

- `README.md`
- `ARCHITECTURE.md`
- `API.md`
- `PROJECT_STRUCTURE.md`

## Run The Backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Docs endpoint: `http://localhost:8000/docs`
