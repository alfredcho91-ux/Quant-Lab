# Wick Statistics

## Integration boundary

The Trend Analysis Chart (`/trend-chart`) already retrieves OHLC through `useTrendPriceChart`, removes the final forming candle via `getCompletedCandles`, and retains up to 200 completed bars. Wick Statistics consumes that same array in the frontend. It adds no request, backend endpoint, dependency or second calculation engine. The backend ATR/indicator pipelines and backtest charts are unchanged.

There is no generic chart-indicator registry in the current application. Four definitions share one settings group; the existing Lightweight Charts instance owns the price pane and Wick pane, sharing time scale, horizontal zoom/pan and crosshair. The existing chart legend/crosshair callback and common two-decimal display formatter are reused. VPVR height tracks the actual price pane so its profile remains price-aligned.

Settings (default period 14, absolute-price unit, four independently visible series) persist in the existing `quant-lab-storage` Zustand record. Old or malformed records receive validated defaults. Positive safe integer periods are accepted without a UI cap; if N exceeds the available 200-bar chart history, all values are unavailable. No extra historical request is made. Invalid or unfinished input leaves the last valid period active.

## Formulas and validity

For each completed bar:

- Upper = High − max(Open, Close)
- Lower = min(Open, Close) − Low
- AUW / ALW = arithmetic mean of the trailing N upper / lower lengths
- MUW / MLW = median of the same N lengths (mean of the central pair for even N)
- Percent mode: divide **each bar's** upper and lower length by **that bar's close**, multiply by 100, then apply the same rolling operations.

Zero lengths are valid observations. Windows are trailing, never centered; calculations are not rounded. Every input row keeps one output position. A window with fewer than N observations, missing/non-numeric/non-finite/nonpositive OHLC, High below the body, Low above the body, or non-finite normalization yields null for all four values. Invalid rows are not replaced, clamped, silently skipped, or treated as zero; a valid result resumes only after they leave the window. The existing HTTP OHLC validator still rejects structurally malformed responses before chart rendering; its policy is not changed.

Null values render as whitespace/—. The native line adapter suppresses the outgoing segment across an invalid window so the chart does not interpolate a misleading bridge. Timestamps use the identical millisecond-to-second conversion as the price candles. Display toggles do not change calculated values.

## Per-candle distribution

Below the chart, a paired bar/table view groups raw upper and lower wick percentages into fixed **0.1 percentage-point** intervals: `[0.0%, 0.1%)`, `[0.1%, 0.2%)`, etc. Each wick is divided by its own candle's close before binning. This is a distribution of individual wick lengths, not of the rolling means or medians.

The population is the same loaded completed-candle array (up to 200), independent of rolling period, unit or visibility settings. Changing the coin/timeframe replaces the population through the existing query. Zero-length wicks count in the first bin. The view reports total, valid and excluded candles; each side's count/share uses the valid-candle count as its denominator. Invalid OHLC, non-finite normalization and unrepresentable bin indices are excluded from both sides, never coerced to zero. No valid samples produces an explicit empty state without percentages.

Bins are lower-inclusive and upper-exclusive, not rounded-to-nearest. A narrowly scaled floating-point correction handles subtraction error at decimal boundaries such as `100.1 - 100`. Empty bins on both sides are omitted; sparse storage preserves extreme outliers without allocating all intervening bins. Count/share labels reuse the two-decimal formatter; bin boundaries display one decimal. This adds no request, persisted state or dependency.

## Regression coverage

Pure calculation tests cover bullish/bearish/doji bars, flat/zero wicks, odd/even medians, outliers, overflow-safe finite means, warm-up/empty/insufficient data, malformed OHLC and recovery, per-bar percent normalization, invalid periods, immutability, prefix invariance and the existing forming-candle exclusion policy.

Chart/settings tests cover the four native pane series, aligned timestamps, null hover values, period/unit changes, independent/all-hidden toggles, coin/timeframe changes, persisted-state restoration and backward-compatible defaults. Other consumers can omit Wick settings and retain the original price-only chart. No real account, credential or journal data is needed for these tests.

Distribution tests cover exact and near-boundary values, zero wicks, per-candle normalization, invalid/excluded observations and denominators, empty states, sparse outliers, input immutability, bilingual counts/shares/bars, population replacement and independence from rolling settings.

## Acceptance results

- Frontend: 540 tests passed (including 49 new Wick tests); 53 focused Wick/OHLC tests passed. TypeScript, ESLint and production build passed. Build reports only the existing stale Browserslist database warning.
- Backend compatibility: 32 core-indicator/ATR, projection and market/data-loader tests passed; the optional TA-Lib comparison was skipped because TA-Lib is not installed locally. The full backend suite was not rerun for this frontend-only change.
- Browser: a disposable synthetic HTTP fixture verified native price/Wick panes with VPVR alignment, Korean/English settings, unit/period changes, all-hidden and restored series, timeframe changes, reload persistence and absence of browser errors/horizontal overflow. No application database or credentials were used. Mouse drag/wheel gestures were not automated; pane time synchronization uses the single native chart instance.
- Distribution browser follow-up: the same synthetic fixture displayed 200 valid completed candles, paired counts/share bars and decimal bins in Korean and English. The distribution remained present after switching from 4h to 1h. Desktop layout was visually checked; no live exchange or mobile distribution check was performed.
- These feature-stage checks did not include live exchange integration, a Windows package build or remote CI. Publication is tracked separately by the v1.1.0 release.

## Changed files

- `frontend/src/utils/wickStatistics.ts`: pure rolling/distribution calculations and validated settings defaults.
- `frontend/src/utils/wickStatisticsPresentation.ts`: four presentation definitions, bin labels and native line-data adapter.
- `frontend/src/types/indicators.ts`: Wick settings/series types.
- `frontend/src/components/WickStatisticsSettings.tsx`: the single settings group.
- `frontend/src/components/WickDistribution.tsx`: paired distribution table/bars and population disclosure.
- `frontend/src/components/TrendPriceChart.tsx`: shared native pane, legend and VPVR geometry.
- `frontend/src/pages/TrendChartPage.tsx`: chart-page integration.
- `frontend/src/store/useStore.ts`: existing-store persistence.
- `frontend/src/utils/wickStatistics.test.ts`: calculation regressions.
- `frontend/src/utils/wickDistribution.test.ts`: distribution calculation/boundary regressions.
- `frontend/src/components/WickDistribution.test.tsx`: distribution display regressions.
- `frontend/src/pages/TrendChartPage.wick.test.tsx`: settings/chart/persistence regressions.
- `docs/WICK_STATISTICS.md`: this implementation/acceptance record.

The pre-existing untracked `scripts/run_quant_lab_windows.cmd` is unchanged and is not part of this feature.
