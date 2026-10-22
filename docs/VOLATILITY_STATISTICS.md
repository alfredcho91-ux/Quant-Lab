# Volatility & Wick Statistics

## User entry point

Quant Lab's sidebar contains **변동성·꼬리 통계 / Volatility & Wick Statistics**, after Trend Analysis Chart. Direct route: `/volatility-statistics`. Existing sample-workspace restrictions remain unchanged.

The page shows latest completed-candle ATR, MTR, upper-wick standard deviation and lower-wick standard deviation, plus a price/indicator chart. Both panels share category times, crosshair links and inside/slider zoom using the existing EChart component. The native legend toggles each statistic.

The user can independently set:

- Calculation period N: positive safe integer, default 14. N larger than available history yields unavailable values, never a shortened window.
- Completed-candle count: 1–9,999, default 500. The existing API permits 10,000 rows; request count + 1 and exclude the final forming candle using `getCompletedCandles`. No backend limit is raised.
- Price or percent units (default percent).

Apply settings commits validated form inputs. Editing an input does not trigger requests. N/unit changes recalculate locally; count, sidebar coin or timeframe changes select a new React Query key. Actual returned sample count/source are displayed, because upstream history can be shorter than requested. Page settings are local to the mounted page, not new persisted application state.

## Calculation contract

- TR = max(H−L, |H−previous close|, |L−previous close|). The first loaded TR uses H−L.
- ATR matches `core/indicator_primitives.py::compute_atr_wilder` on valid input: first TR seed, recursive `(1−1/N) × previous ATR + TR/N`, hidden until N TR observations. This preserves the existing core's RMA initialization, rather than substituting a simple rolling mean or an SMA seed. ATR initialization depends on loaded history.
- MTR means **Median True Range**: median of trailing N TRs, averaging the central pair for even N.
- Upper wick = H−max(O,C); lower wick = min(O,C)−L. Both reuse the existing Wick Statistics validation/calculation helper.
- Wick standard deviation is population deviation: `sqrt(sum((x−mean)^2)/N)`, ddof=0. Zero wicks remain valid samples. Scale before calculating variance to avoid overflow.
- Percent ATR/MTR = price-unit statistic/current candle close ×100, matching the core ATR percent convention. Percent wick deviation normalizes each individual wick by its own close ×100 **before** computing deviation; its unit is percentage points (%p).
- Positive finite numeric OHLC and consistent high/body/low geometry are required. Invalid rows are not imputed or skipped. A wick window remains unavailable until the invalid row leaves it. Invalid current/previous OHLC makes TR unavailable; ATR resets and requires N consecutive valid TRs to become visible again. Non-finite normalization is unavailable, not infinity.
- Only chronological completed bars are consumed. No future values, centered windows, signal execution or trading strategy is added. Calculations retain precision; labels use the existing two-decimal formatter.

Price candles display the original validated HTTP response, independently of whether a statistic's window is valid. This descriptive page does not change backend ATR, backtesting, trade sizing, accepted security boundaries, or the existing Wick Statistics/distribution page.

## Verification

- 73 focused calculation/page/previous Wick tests passed; full frontend: **567 passed**, 54 files.
- TypeScript noEmit, ESLint and production build passed. Only the existing stale Browserslist database warning was reported by the build.
- Tests cover gaps, explicit core ATR reference values, odd/even median, zero wicks, population deviation, both unit conventions, invalid-data recovery, overflow, warm-up, arbitrary N, immutability/prefix invariance, forming-candle exclusion, API count bounds, explicit apply, one-request/no-refetch recalculation, empty/error states, late previous-selection responses, bilingual route/navigation and synchronized chart option contracts.
- Browser verification uses a disposable synthetic HTTP server without application databases, profiles or credentials. Korean desktop cards/chart and applying N=20/count=50/price units were visually checked; the shared zoom/crosshair and bottom slider rendered correctly. English labels and switching from 4h to 1h preserved the applied N/count and replaced the candle timestamps. Mobile was not checked (the product is desktop-first).
- These frontend feature-stage checks did not rerun the full backend suite or include a real exchange, Windows installer or remote CI. Publication is tracked separately by the v1.1.0 release.

## Files

- `frontend/src/pages/VolatilityStatisticsPage.tsx`
- `frontend/src/utils/volatilityStatistics.ts`
- Corresponding page/calculation test files
- `frontend/src/App.tsx`, `frontend/src/components/Sidebar.tsx`, `frontend/src/store/labels.ts`: bilingual route/navigation
- `frontend/src/utils/wickStatistics.ts`: expose the already-used candle-wick helper; no formula change
- This document

Earlier uncommitted Wick Statistics work and the user's pre-existing untracked Windows launcher are preserved.
