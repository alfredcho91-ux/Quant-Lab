# Stop-Loss Lab

Research only: observed distributions and counterfactual simulations, not live
orders, causal findings, guaranteed returns or an automated trading system.

## Architecture audit and integration

- `/volatility-statistics` now opens Stop-Loss Lab; `/stop-loss-lab` is an alias.
  The existing six-column-statistics table is preserved under **Candle statistics**.
  Existing chart indicator registrations and wick calculations are unchanged.
- Public data: existing `fetch_binance_klines`, bounded backwards pagination,
  explicit historical `end_time`, existing 30-second raw-data cache. Binance
  USDT-M Futures BTC/ETH/SOL only. No credentials, journal records or SQLite reads.
  Unlike the recent-data compatibility wrapper, this path does not cap weekly
  history at 300 bars. There is no CSV fallback or fabricated market data.
- `statistics.py`: pure validation, completed-candle filtering, distribution and
  causal snapshots. Reuses `core.indicator_primitives` TR/Wilder ATR and existing
  **confirmation-time** swing levels (`detect_swings`, three bars each side).
- `simulation.py`: strategy-specific reference-level touch simulation. Existing
  `core/backtest.py` requires strategy signal columns and next-open entries and
  cannot represent these touch orders. It is deliberately unchanged. Existing
  journal `performance` is reused; account ledger/MDD and dollar-based PF are
  computed explicitly for actual sizing, including negative gap equity.
- `service.py` fetches/prepares each timeframe once; entry conditions and historical
  calibration are shared across stop/target combinations. `router.py` offloads
  calculation to FastAPI's threadpool. `POST /api/stop-loss-lab/analyze` uses the
  existing application authentication/local-request and offline sample boundary.
- UI uses existing React Query mutations, public API client, language store,
  number formatting, card/table styles and EChart. Only BarChart is added to the
  existing renderer registry. Heatmap is an accessible clickable table.
- One submitted request owns each result: editing the draft cannot relabel a late
  response or change its submitted settings. Calculations are never auto-run.

## API and reproducibility

Request schema: `backend/modules/stop_loss_lab/schemas.py::LabRequest`.
Extra fields, nonfinite numbers, invalid dates/grids and excessive work are rejected.
Inclusive UTC date range ≤366 days; execution bars ≤30,000; combinations ≤125;
bars × combinations × maximum entries ≤3,000,000. Up to ten explicit numeric
values per axis, entered comma-separated. No new dependency or persistent cache.

Response contains submitted `config`, source, effective `as_of`, counts, execution
coverage and SHA-256 of canonical OHLC inputs, daily/weekly distributions and
breakouts, candidate metrics/trades, chronological split, training-selected cell,
neighborhoods, year/regime groups and expanding walk-forward folds. To reproduce
later, the same canonical input data is necessary; a fingerprint is not a stored
market-data snapshot. Historical exchange corrections can change results.

Incomplete execution candles are excluded. Weeks start Monday 00:00 UTC.
Reference history gaps fail explicitly, preventing Wilder ATR from bridging a
missing candle. Missing execution intervals skip affected periods/horizons with
counts. No filling or compressed time. First/last partial reference periods are
excluded. Dates ending today therefore exclude unfinished reference periods.

## Statistics and information boundary

Upper wick = H − max(O,C); lower wick = min(O,C) − L. Zero wicks remain samples.
Percent distributions first divide **each candle's** length by its **open** ×100.
Price and percent statistics are calculated independently. Mean, median,
population standard deviation, linear-interpolated P50/P75/P90/P95/P99 and
mean/median are reported. Ratio is undefined when median is zero. Histograms
have sparse 0.1-percentage-point bins; ECDF includes every distinct observation.

TR = max(H−L, |H−previous C|, |L−previous C|); first observed TR is H−L.
ATR uses the existing engine's `ewm(alpha=1/N, adjust=False, min_periods=N)`;
MTR uses the same TR with a complete N-bar rolling median. ATR's initial seed is
the first fetched warmup candle, not a newly introduced SMA seed. Warmup is N+8
reference bars, reported through the data fingerprint. The old table retains its
arithmetic TR mean and **close** normalization and labels that difference.

Explorer summaries describe completed reference candles in the selected dates;
N controls ATR/MTR and pre-entry rolling calibration, not the date-range count.
ATR/MTR expansion ≥1.25, contraction ≤0.8; otherwise normal. Prior N-close change
>2% = bull, <−2% = bear, else sideways. These are explicit research buckets,
not an inferred or forward-looking regime model.

Short reference extreme is previous completed high; long is previous low.
Previous open/close, nonzero confirmed wick extreme, or confirmed swing may be
selected. Levels freeze at the period's start from reference candles that ended
by that time. Short trigger = reference + offset; long = reference − offset.
Fixed-% entry offset is relative to reference; stops/targets are relative to the
slippage-adjusted fill. ATR/MTR and wick lengths are price distances multiplied
by a user factor. Wick/overshoot percentiles use only previous completed history.
Overshoot is relative to the previous high/low; only positive breakouts enter
that conditional distribution (not all periods).

Conditional MAE stop calibration uses the first qualifying touch **per side per
reference period**, with the same entry setting and configured maximum horizon,
independent of stop/target choices. These are entry-condition samples, not a
portfolio of historical executed stops. A sample is available only once its
entire horizon has finished by the new period's start. At least `min_trades`
prior samples are required; otherwise that period is explicitly skipped. No
full-date-range percentile is applied to earlier orders. MAE is an OHLC upper
bound and therefore conservative, not exact tick-level adverse excursion.

Unconditional wick P95 is **not** a 5% conditional post-entry stop probability.
Daily/weekly overshoot distributions and reference-return measurements are
separate from selected-entry MAE/MFE. Return rates are confirmed lower bounds;
same-bar unknown ordering/missing coverage is counted. Return times are candle
resolution upper bounds. MAE/MFE distributions describe the selected cell's
evaluated trades; table values show both lower and upper bounds.

## Fill, costs and position assumptions

- Market-on-touch, not passive limit fills. If the opening price already crosses
  the trigger, enter at open; otherwise at trigger, then apply adverse slippage.
  Both directions share one position. Tied opposite triggers in one candle have
  unknown order and are excluded, not resolved in the profitable direction.
- Stops/targets use execution OHLC, not reference candle future high/low/close.
  Subsequent open beyond a barrier fills at that open. Otherwise if both barriers
  touch in one candle, stop wins and the trade is marked ambiguous.
- Intrabar entry plus target-only touch may have target before entry. Unless a
  favorable close proves a later target crossing, the outcome is not evaluable.
  It is counted as filled-but-unknown and blocks re-entry until the horizon;
  it contributes no invented PnL. Subsequent periods are conditional on excluding
  that unknown outcome; do not interpret their ledger as a fully observed path.
- Exit occurs at stop, target, reference-period-end close or configured holding
  horizon close. Fixed hours must align with execution bars and may cross weeks;
  a wholly covered horizon is required. Entry/exit timestamps are candle bounds,
  not claimed tick times. Entry clock starts at the trigger candle's opening.
- Re-entry default one per period, at most five, only after the prior exit candle.
  No concurrent positions. For Both, first identifiable trigger wins.
- Every entry and exit pays the configured fee and adverse slippage. Risk sizing
  = equity × risk% / planned stop distance, capped at equity / filled entry
  (1× notional). Alternative sizing uses the configured notional allocation.
  Planned risk excludes costs; realized R = net unit PnL / planned price risk.
  Gap losses can exceed planned risk or account capital; no clipping, and an
  exhausted account takes no subsequent positions.
- MAE/MFE lower bounds use known subsequent opens and filled exits; upper bounds
  include entry/exit candle extrema that might be outside the holding interval.
  Post-stop target rate is a **lower bound**, requiring a later bar before the
  original horizon; same-bar post-stop target order is not invented.

## Evaluation and anti-overfit safeguards

Each slice replays sizing from the configured initial equity. Report signal
opportunities, fills, unknown/skipped counts, evaluated trades, fill rate, win
rate, mean account win/loss, mean winning R / |mean losing R|, planned RR,
expected net R, dollar PnL-based PF, net account return, closed-equity MDD,
loss streak, holding time, MAE/MFE bounds, post-stop target rate and paid fees.
Re-entry creates additional signal opportunities. PF with no losses is undefined,
not infinity. Closed-equity MDD is **not** marked-to-market intratrade drawdown.

Split is a chronological reference-period boundary. Trades crossing train/test
boundaries are purged, not apportioned. Test results never select parameters.
Training must meet minimum sample count and MDD limit and have no unknown
execution/order exclusions. Selection ranks training neighborhood median EV R,
then own EV R; neighbors are within one step on each axis including self.
Grid values are sorted numerically before defining adjacency. A single cell
cannot establish regional stability.

Expanding walk-forward chooses on earlier training only and tests in each next
calendar block. Small date ranges may provide fewer than three distinct folds.
Folds reset equity and are not summed into a continuous portfolio. Year/trend/
volatility breakdowns are descriptive, not independent evidence of causality.
Wilson win-rate intervals and normal-approximate EV-R intervals are 95%, with
no serial-dependence or multiple-testing correction. Small samples are flagged.
Choosing again after viewing holdout data contaminates that holdout.

## Validation / limits

Automated tests use synthetic OHLC, covering zero/even-median/quantile/std,
core ATR agreement, weekly confirmation, missing OHLC, prefix invariance,
same-bar barriers, unknown entry order, gaps, costs, risk sizing and insolvency,
timeout coverage, Both/re-entry limits, past-only conditional calibration,
train/test isolation, deterministic optimization, public-source boundaries and
router validation. UI tests cover submitted snapshot authority while pending,
explicit execution, malformed/over-budget grids, heatmap selection, ECDF data,
errors, bilingual labels and the preserved legacy view.

Not modeled: bid/ask spread, depth/partial fills/queue position, funding,
liquidation/leverage, exchange precision/minimum order rules, taxes, market impact,
tick ordering, portfolio correlations. Synthetic tests cannot prove real exchange
fill accuracy. This tool is an OHLC counterfactual research aid, not a live order
execution or investment recommendation service.

### Local acceptance (2026-10-23)

- Backend full suite: **1,276 passed, 1 skipped** (including 39 new lab tests and
  two added direct-route cases); no failures. Existing framework deprecation
  warnings remain.
- Frontend full suite: **580 passed / 55 files**, repeated with two workers after
  a long system execution interruption caused timeout-only failures in an earlier
  run. No test timeout was increased and no unrelated tests were weakened.
- TypeScript noEmit, ESLint (zero warnings), production build, core/route/version/
  Plan Lab isolation guards and `git diff --check` passed. Build reports the
  Browserslist freshness notice and 613 kB ECharts chunk warning; no dependency
  update or unrelated bundling refactor was performed.
- Real public BTC USDT-M data: 60 completed days, 1,440 hourly execution candles,
  eight entry/stop/target combinations calculated with source fingerprint.
  Daily and weekly source acquisition succeeded. This checks data integration,
  not actual order execution; real exchange fills, other symbols and exhaustive
  parameter/date ranges have not been independently reconciled.
- Synthetic OHLC used for deterministic numerical, ambiguity, cost, lookahead,
  holdout and UI coverage. No private trades or credentials used in fixtures.
- Restarted the existing local backend after user approval. Both direct routes
  return HTTP 200 and the new API is present in the running OpenAPI schema.
  Actual browser execution with public BTC data also completed a nine-cell grid
  (5,856 fifteen-minute candles); clicking a cell updated the detailed results.
  At the inspected 862px viewport, document width equaled viewport width, both
  chart canvases rendered and there were no browser console errors or UI alerts.
  This is desktop browser verification, not an exhaustive mobile-device matrix.

### Changed-file map

- New backend: `backend/modules/stop_loss_lab/{__init__,schemas,statistics,simulation,service,router}.py`.
- Backend integration: `backend/main.py`, `backend/utils/frontend_static.py`.
- Backend tests: `backend/tests/test_stop_loss_lab_{statistics,simulation}.py`,
  `test_framework_static_security.py`, `test_quant_journal_integration.py`.
- New frontend: `frontend/src/api/stopLossLab.ts`,
  `frontend/src/pages/StopLossLabPage.tsx`, its test,
  `frontend/src/components/StopLossLabResults.tsx`.
- Frontend integration: `frontend/src/App.tsx`, `store/labels.ts`,
  `components/EChart.tsx`, `pages/VolatilityStatisticsPage.test.tsx`.
- Documentation: this file, `README.md`, `API_SPEC.md`,
  `docs/PAGE_BACKEND_MAPPING.md`. Previously requested legacy table/timeframe
  changes in `VolatilityStatisticsPage`, `utils/volatilityStatistics`, their
  tests, `Sidebar.tsx`, `constants/market.ts` and `VOLATILITY_STATISTICS.md`
  are preserved. The pre-existing untracked Windows launcher was not modified.
- The implementation acceptance above made no dependency changes or publication.
  The subsequent user-authorized publication uses v1.2.0; see
  [release notes](releases/v1.2.0.md). The local-only launcher remains excluded.
