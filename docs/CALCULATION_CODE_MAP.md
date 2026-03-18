# Streak Probability Calculation Code Map

## Main Module Cluster

The primary implementation lives under `backend/strategy/streak/`:

- `__init__.py` for orchestration and mode selection
- `simple_strategy.py`
- `complex_strategy.py`
- `common.py`
- `statistics.py`

## Where The Probability Logic Lives

### 1. Primary continuation rate

- Location: `strategy/streak/simple_strategy.py`
- Responsibility: continuation vs reversal after an `N`-candle streak, plus `C1` and `C2` outcome handling
- Main edit point: continuation and reversal counting inside `run_simple_analysis()`

### 2. Confidence intervals and statistical testing

- Call sites: `simple_strategy.py`, `complex_strategy.py`
- Definitions:
  - `wilson_confidence_interval()` in `statistics.py`
  - `calculate_binomial_pvalue()` in `common.py`

### 3. Second-candle (`C2`) prediction

- Locations: `simple_strategy.py`, `complex_strategy.py`
- Responsibility: conditional `C2` probabilities given the observed `C1` outcome

### 4. Interval statistics (`RSI`, `Disparity`)

- Location: `strategy/streak/common.py`
- Function: `analyze_interval_statistics()`
- Used by both simple and complex streak analyses

### 5. Short-signal simulation

- Location: `strategy/streak/complex_strategy.py`
- Responsibility: short-entry simulation and win-rate measurement for complex mode

### 6. Comparative report (`nG + 1R`)

- Locations: `simple_strategy.py`, `complex_strategy.py`
- Responsibility: compare the base pattern against alternative sequence structures

## Editing Guidance

### Before you change anything

1. Entry point: `analyze_streak_pattern()` in `strategy/streak/__init__.py`
2. Actual calculations are split across `simple_strategy.py`, `complex_strategy.py`, `common.py`, and `statistics.py`
3. Execution branches into `run_simple_analysis()` or `run_complex_analysis()`

### If you want to split more functions

```python
def calculate_continuation_rate(target_cases: pd.DataFrame) -> dict:
    """Primary continuation probability calculation."""
    pass


def calculate_c2_predictions(df: pd.DataFrame, target_cases: pd.DataFrame) -> dict:
    """Conditional C2 probability calculation."""
    pass


def calculate_interval_statistics(...):
    """Bucketed interval statistics."""
    pass
```

### If you want to edit directly

- `simple_strategy.py`: primary probability calculation and `C2` prediction
- `complex_strategy.py`: short-signal logic, interval statistics, comparative reporting
- `streak/common.py`, `streak/statistics.py`: Wilson score, binomial p-value, interval statistics

## Related Files

### Backend

- `backend/strategy/streak/__init__.py`: main orchestration entry point
- `backend/strategy/streak/simple_strategy.py`, `complex_strategy.py`: strategy logic
- `backend/strategy/streak/common.py`, `statistics.py`: shared and statistical logic
- `backend/modules/streak/router.py`: API endpoint
- `backend/models/request.py`: request model

### Frontend

- `frontend/src/pages/StreakAnalysisPage.tsx`: UI entry page
- `frontend/src/types/index.ts`: type definitions
- `frontend/src/api/client.ts`: API client wiring

## Key Functions

| Function | Location | Responsibility |
|---|---|---|
| `analyze_streak_pattern()` | `strategy/streak/__init__.py` | Main orchestration |
| `run_simple_analysis()` | `strategy/streak/simple_strategy.py` | Simple-mode analysis |
| `run_complex_analysis()` | `strategy/streak/complex_strategy.py` | Complex-mode analysis |
| `wilson_confidence_interval()` | `strategy/streak/statistics.py` | Confidence interval estimation |
| `calculate_binomial_pvalue()` | `strategy/streak/common.py` | Statistical testing |
| `analyze_interval_statistics()` | `strategy/streak/common.py` | Bucketed interval analysis |
| `calculate_signal_score()` | `strategy/streak/common.py` | Signal scoring |

## Current Structure

`analyze_streak_pattern()` is orchestration-only. The implementation is already split by responsibility:

```text
strategy/streak/
├── __init__.py         -> analyze_streak_pattern() for entry, cache, and mode branching
├── simple_strategy.py  -> run_simple_analysis()
├── complex_strategy.py -> run_complex_analysis()
├── common.py           -> data prep, cache helpers, interval stats, signal scoring
└── statistics.py       -> Wilson score and shared statistical helpers
```
