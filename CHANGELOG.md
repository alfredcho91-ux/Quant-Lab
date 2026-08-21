# Changelog

## [2026-08-21] Navigation And Product Scope Cleanup

- Removed the unused Combo Filter Test end to end: sidebar item, page, frontend client/types, `/api/combo-filter` endpoint, schemas, strategy module, and indicator helper.
- Moved Trading Journal and Trade Analysis to the top of the sidebar, and moved AI Backtest Lab to the final sidebar item.
- Updated README, architecture, API, page mapping, calculation map, backend guide, and implementation notes to reflect the active product scope.

## [2026-08-08] Unified Trade Report

- Combined the journal indicator snapshot and position chart review into one trade-report modal.
- Added 5m/15m/30m/1h/2h/4h/1d RSI, MACD histogram/lines, Stoch RSI, and three Slow Stochastic chart panels.
- Added point-in-time VPVR, POC/Value Area, anchored VWAP, profile VWAP, and 200-bar VWAP as a numeric report below the uncluttered price chart.
- Added shared ENTRY and EXIT time markers to RSI, MACD, Stoch RSI, and all three Slow Stochastic graphs.
- Moved the selected ENTRY/EXIT indicator values into each momentum graph and removed their duplicate snapshot-table rows.
- Added order-grouped `ENTRY`/`ADD` markers and confirmed Deepcoin TPSL `TP1`/`TP2` markers and price lines to the trade-review chart.
- Limited `ADD` attribution to the selected closed position size so overlapping same-direction positions are not merged, and recalculated re-entry quantity from the entered USDT notional at the re-entry price.
- Added mouse-wheel vertical price-axis zoom to the trade-review candlestick chart.
- Added left-click vertical drag to pan the trade-review price axis.
- Added Shift-plus-wheel horizontal time-axis zoom to the trade-review candlestick chart.
- Added left/right drag horizontal zoom to the trade-review candlestick chart.
- Kept one Lightweight Charts instance alive during zoom and drag interactions instead of rebuilding it per frame.
- Normalized trade-report indicator timestamps to UTC and unified entry-time and entry-snapshot fill resolution, with estimated entries labeled in the UI.
- Removed manual journal entry creation and split the trade report and Deepcoin snapshot calculation into focused modules.
- Replaced journal net-PnL summary and row values with notional-weighted net return percentages after trading fees and funding.
- Hid raw fill rows from the journal, retained them for position matching, and added split-entry fill details, weighted average price, and ADD chart markers to the trade report.
- Corrected Deepcoin SWAP returns by inferring notional from reported PnL and price movement instead of treating contract count as coin quantity.
- Extended the Deepcoin sync client timeout so a 90-day backfill can finish instead of appearing to fail after the global 60-second limit.
- Added period and per-trade net profit beside net return, removed the journal price-move column, and added inclusive boundary tests for 7/30/90-day period selection.
- Grouped partial fills by order and excluded opposite-position fills from entry and scale-in reporting.
- Removed entry-order detail tables and ADD markers so trade reports show only the position entry and exit prices.
- Kept post-exit context candles out of entry/exit VPVR and VWAP calculations and retained the existing stored multi-timeframe snapshot table.

## [2026-08-04] Deepcoin Trade Journal Sync

- Added a read-only Deepcoin fills synchronization API and Journal UI controls for SWAP and SPOT histories.
- Added `billId`-based idempotent journal imports, bounded pagination, and server-only API credentials.
- Added 1h/2h/4h/1d completed-candle snapshots for RSI, MACD, Slow Stochastic, Stoch RSI, VPVR, and VPVR VWAP.
- Added snapshot inspection in the journal and tests for HMAC signing, pagination, idempotency, and completed-candle selection.

## [2026-08-03] Trend Judgment And Documentation Refresh

### Trend Judgment

- Added an ECharts candlestick chart with anchored VWAP lines, VPVR profile, and 1h/2h/4h/1d RSI 30/70 price-reference levels.
- Standardized Trend Judgment display values on the previous completed candle and chart data on the latest 200 completed candles.
- Added 2-hour price projection and current RSI display.
- Added MACD and Stoch RSI crossover markers based on actual recent crosses.
- Added vertical price-axis zoom controls.
- Changed trend-indicator data loading from 2,000 to 600 candles: enough warmup for 200-period indicators while avoiding a second Binance kline request.

### VWAP And VPVR

- Set VWAP anchors by timeframe: 1h/2h daily+weekly, 4h weekly+monthly, 1d monthly+quarterly+yearly.
- Added a 200-bar rolling VWAP for 1h, 2h, and 4h projections.
- Added Binance kline source inspection and VPVR output with POC, Value Area, period VWAP, and explicit `candle_range_proportional` allocation metadata.
- Set VPVR defaults to 240 bars for 1h/2h/4h, 180 bars for 1d, 300-bar fallback, 24 bins, and a maximum 10,000-USDT visible range.

### Performance And Reliability

- Moved Trend Judgment query ownership to the page and removed duplicate child queries.
- Set Trend Judgment React Query stale time to one hour, aligned auto-refresh to the next hour, and prevented unnecessary refetch on reconnect or short visibility changes.
- Added OHLCV validation and shared completed-candle filtering in the frontend.
- Moved presets to a project-root-based path and writes them through a temporary file followed by replace.

### Product Scope

- Removed scanner, pattern-scanner, strategy-scanner, advanced-backtest, and BB Mid navigation from the active sidebar.
- Limited shared market coin selection to BTC, ETH, and SOL.

### Documentation And CI

- Rewrote README, architecture, API, install, cache, calculation, page-mapping, and backend-operation documents from current code.
- Updated project and subdirectory knowledge-base files.
- Added the frontend Vitest step to GitHub Actions alongside lint and build.

## [2026-01-31] Documentation Refresh

- Consolidated previous hybrid-strategy documentation and route references.

## [2026-01-21] Project Structure Improvements

- Centralized backend project-root path handling.
- Consolidated market data access under `backend/utils/data_service.py`.
- Removed duplicated squeeze-service implementation and clarified shared statistics ownership.
