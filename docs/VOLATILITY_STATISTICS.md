# Volatility & Wick Statistics

## User entry point

Quant Lab's sidebar contains **변동성·꼬리 통계 / Volatility & Wick Statistics**, after Trend Analysis Chart. Direct route: `/volatility-statistics`. Existing sample-workspace restrictions remain unchanged.

Korean timeframe labels in the shared selector and this page header are `4h → 4시간봉`, `1d → 날봉`, `1w → 주봉`, `1M → 달봉`. Option values, store/query keys and API requests retain their original codes; English labels and other timeframe choices are unchanged. This is a label change, not a multi-timeframe comparison or calculation change.

The page shows **six arithmetic-mean/median statistics**, not standard deviations or Wilder ATR:

- Candle volatility (gap-inclusive True Range): mean and median.
- Upper wick length: mean (AUW) and median (MUW).
- Lower wick length: mean (ALW) and median (MLW).

The **numeric table has no graphs**. Its eight columns are candle open time, close and the six statistics, grouped into volatility/upper/lower mean–median pairs. Rows are newest first with 50 per page. All six metrics use price units or %, explicitly labeled in the group headers. Warm-up and invalid values remain —, while valid zeros show 0.00. Six summary cards retain the latest values.

All statistics are calculated on the full loaded chronological history before selecting/reversing table rows. Pagination changes only the visible rows, never the calculation population or network request. Applying settings or switching coin/timeframe returns to the first page. The table has a sticky header and its own overflow area so larger datasets do not require rendering all 9,999 rows at once. This page no longer imports EChart or builds chart options; other chart pages are unchanged.

The user can independently set:

- Calculation period N: positive safe integer, default 14. N larger than available history yields unavailable values, never a shortened window.
- Completed-candle count: 1–9,999, default 500. The existing API permits 10,000 rows; request count + 1 and exclude the final forming candle using `getCompletedCandles`. No backend limit is raised.
- Price or percent units (default percent).

Apply settings commits validated form inputs. Editing an input does not trigger requests. N/unit changes recalculate locally; count, sidebar coin or timeframe changes select a new React Query key. Actual returned sample count/source are displayed, because upstream history can be shorter than requested. Page settings are local to the mounted page, not new persisted application state.

## Calculation contract

- TR = max(H−L, |H−previous close|, |L−previous close|). The first loaded TR uses H−L.
- The UI explicitly identifies TR as gap-inclusive, which can differ from a candle's own H−L range.
- Each mean = sum of the trailing N observations / N, using equal weights. This page no longer computes or labels Wilder-smoothed ATR; the existing backend ATR and other chart pages are unchanged.
- Each median = the central sorted observation in the same trailing N-bar window, averaging the central pair for even N. There are separate medians for TR, upper wicks and lower wicks.
- Upper wick = H−max(O,C); lower wick = min(O,C)−L. All four wick statistics directly reuse `computeWickStatistics`; their accepted formulas/validation are unchanged.
- Zero TRs/wicks are valid observations. Means scale nonnegative observations before summing to avoid overflow; calculations and medians are never rounded before display.
- Percent mode computes `(length / that candle's close) × 100` for **each candle's** TR/upper/lower length **before** the mean/median. It does not divide an already-aggregated statistic by the final close. All six metrics are percentages, not standard-deviation percentage points.
- Positive finite numeric OHLC and consistent high/body/low geometry are required. Invalid rows are not imputed or skipped. A wick window remains unavailable until the invalid row leaves it. Invalid current/previous OHLC makes TR unavailable, so its trailing windows also remain unavailable until all N TRs are valid. Non-finite normalization is unavailable, not infinity.
- Only chronological completed bars are consumed. No future values, centered windows, signal execution or trading strategy is added. Calculations retain precision; labels use the existing two-decimal formatter.

The close column shows the corresponding raw candle close independently of whether a statistic's window is valid. This descriptive page does not change backend ATR, backtesting, trade sizing, accepted security boundaries, or the existing Wick Statistics/distribution page.

## Verification

- Six-statistic follow-up: the full frontend, including calculation, table and timeframe-label tests, passed **574 tests**, 54 files.
- TypeScript noEmit, ESLint and production build passed. Only the existing stale Browserslist database warning was reported by the build.
- Tests distinguish arithmetic means from the previously used Wilder ATR and means from medians on outliers. They verify all four wick results match the existing Wick Statistics contract, per-candle normalization before aggregation, gaps, even medians, zero lengths, invalid-data recovery, overflow and prefix invariance. Table regressions verify all six values/headers, newest-first candle alignment, two-decimal values, warm-up nulls vs valid zeros, forming-candle exclusion, pagination without extra requests or page-subset calculation, reset on settings/coin changes and bilingual labels. No canvas is rendered on this page.
- Timeframe-label regression verifies all four Korean names in the expanded/collapsed sidebar and page header, unchanged API interval values and the original English labels.
- Browser verification used a disposable synthetic HTTP server without application databases, profiles or credentials. The Korean desktop screen showed all six mean/median cards and the eight-column table (time, close, three mean/median pairs) for 200 completed candles. The earlier table follow-up also verified moving from page 1 (1–50) to page 2 (51–100). English labels were covered by component tests; mobile was not checked (the product is desktop-first).
- The page-specific calculation now returns six means/medians; its unused RMA/standard-deviation paths were removed. The backend and shared Wick Statistics/distribution helpers are unchanged, so the backend suite was not rerun. No real exchange, Windows installer or remote CI was tested for this change. This follow-up is local and is not included in the previously published v1.1.0 release; no new commit, push or release was made.

## Files

- `frontend/src/pages/VolatilityStatisticsPage.tsx`
- `frontend/src/utils/volatilityStatistics.ts`
- Corresponding page/calculation test files
- `frontend/src/App.tsx`, `frontend/src/components/Sidebar.tsx`, `frontend/src/store/labels.ts`: bilingual route/navigation
- `frontend/src/utils/wickStatistics.ts`: expose the already-used candle-wick helper; no formula change
- This document

The existing Wick Statistics feature and the user's pre-existing untracked Windows launcher are unchanged by the table-only follow-up.
