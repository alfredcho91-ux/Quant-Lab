# Changelog

## [2026-01-31] Documentation Refresh

### Changes

- `ARCHITECTURE.md`: removed `MaCrossParams`, added hybrid-related params, renamed `MaCrossPage` references to `HybridAnalysisPage`, and cleaned up the stats API list
- `PROJECT_STRUCTURE.md`: removed the `ma_cross/` strategy, added `hybrid/`, replaced `MaCrossPage` references with `HybridAnalysisPage`, added `hybrid.ts`, and removed obsolete `stats.py` / `OPTIMIZATION_SUMMARY` references
- `PAGE_BACKEND_MAPPING.md`: removed the MA cross section, added the hybrid strategy analysis section, corrected the `data_service` path to `utils/`, and refreshed the summary table
- `API.md`: removed `/api/ma-cross`, added `/api/hybrid-analysis`, `/api/hybrid-backtest`, `/api/hybrid-live`, and added journal API coverage
- `main.py`: updated the `stats_router` comment from `ma-cross` to `hybrid-*`

---

## [2026-01-21] Project Structure Improvements

### Major Changes

#### 1. Dependency management cleanup

- Added `backend/__init__.py`
  - centralizes project-root path handling
  - removes scattered `sys.path.insert` usage
- Removed per-file `sys.path.insert` calls from 19 files
  - `routes/`: 5 files
  - `strategy/`: 8 files
  - `services/`: 1 file
  - `tests/`: 2 files kept due to test-environment specifics
- Result:
  - better readability
  - more consistent path handling
  - more stable test setup

#### 2. Data service restructuring

- Moved `backend/data_service.py` to `backend/utils/data_service.py`
- Updated import paths in 7 files:
  - `utils/data_loader.py`
  - `routes/market.py`
  - `routes/support_resistance.py`
  - `strategy/streak/common.py`
  - `strategy/weekly_pattern/logic.py`
  - `strategy/streak/statistics.py`
- Updated `BASE_DIR` from `parent.parent` to `parent.parent.parent`
- Result:
  - fixed dependency-direction issues
  - concentrated data utilities under `utils/`
  - improved structural clarity

#### 3. Duplicate code removal

- Deleted `backend/services/squeeze_service.py` (`195` lines)
- Reason: duplicated logic already covered by `backend/strategy/squeeze/logic.py`
- Result:
  - lower maintenance cost
  - more consistent bug-fix path
  - approximately `195` lines removed

#### 4. Naming cleanup

- Renamed `backend/services/backtest_logic.py` to `backend/services/statistics.py`
- Reason: the file was performing statistical calculations rather than backtest execution
- Result:
  - clearer file responsibility
  - improved readability

### Stats

- Approximate net code reduction: `388` lines (`398` removed, `10` added)
- Files moved: `1` (`data_service.py`)
- Files deleted: `1` (`squeeze_service.py`)
- Files renamed: `1` (`backtest_logic.py` -> `statistics.py`)
- Import paths updated: `7` files
- `sys.path` removals: `19` files

### Documentation Updates

- `PROJECT_STRUCTURE.md`: updated file structure and recent changes
- `ARCHITECTURE.md`: updated module descriptions and dependency relationships
- `README.md`: refreshed the file-structure diagram
- `CHANGELOG.md`: created the changelog

### Test Results

- Backend server starts successfully
- Frontend server starts successfully
- All API endpoints respond correctly
- Import paths resolve correctly
- `BASE_DIR` resolves correctly

---

## Earlier Changes

### 2025 Highlights

- Weekly pattern analysis refactor
- Combo filter test updates
- Type and API-client modularization
- Caching and context-management improvements
