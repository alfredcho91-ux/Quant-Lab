# Current Trade Journal integration

Source: `alfredcho91-ux/trade-journal-free` at `9718c0a828f7244859f360d03d9e14103d20e625` (v1.0.28).
Quant Lab baseline: `cb93c197e2279022e80c90bee543c31bff23d4e0`.

The integration includes Journal and daily records, read-only exchange connectors, Strategy Playbook/version assignments, rule evaluation, validated analytics, summary-first review/experiment handoff, Plan Lab history/save authority, isolated sample onboarding, and the current shared presentation. Existing Quant research tools, built-in strategy templates, store preferences and default Trend Judgment route remain available.

## Adaptation boundaries

- User Playbook routes use `/api/playbook/strategies`. `/api/strategies` still returns built-in backtest templates. Frontend `Strategy` describes the Playbook; `BacktestStrategy` describes the built-in templates.
- Profile settings retain Quant timezone, preset and AI configuration. Normal source-run journal paths remain project-local. Packaged profile and vault names use Quant Lab, not Trade Journal Free.
- Legacy Deepcoin HTTP/functions delegate to the common profile-scoped credential policy. Same-DB legacy encrypted rows remain readable and newer protected rows win. Explicit deletion removes both rows to prevent old ciphertext from reappearing. Reads never delete a legacy source.
- Unscoped old OS-vault entries do not prove profile ownership. They remain untouched; users can explicitly configure the new profile from exchange settings.
- Quant's sidebar remains, with Journal, analysis, risk, planning, trade exploration and Playbook routes. Market selection is hidden on journal-wide queries. Sample mode disables sidebar market polling and research/preset APIs; it permits journal features and pure calculators. Hold/re-entry stays last.
- Known Quant browser routes receive the SPA shell, while unknown API/assets remain 404. Research API routers and timing middleware are retained.
- Python 3.11 and Node 24 match the validated journal toolchain. FastAPI/Starlette, pandas, Pydantic, urllib3 and frontend build/test dependencies use the accepted compatibility lines. Axios 1.20 is the same-major fix for the subsequently published [fetch-adapter advisory](https://github.com/advisories/GHSA-vh66-26gq-q6x8).

## Verification scope

The imported deterministic/backend and async authority/frontend regressions run alongside Quant's research tests. Additional integration contracts cover route ownership, the legacy encrypted format and vault namespace separation. All backend tests redirect storage to temporary profiles and forbid OS credential access. No live private account or exchange sync is required for this acceptance.

Frontend DOM tests supply jsdom's missing `matchMedia` API for Quant's retained sidebar. Browser acceptance uses an isolated temporary profile and synthetic sample, then checks Journal, analysis/review/experiments, risk, planning, Playbook and trade exploration.

No Microsoft Store package, new release or live-exchange acceptance is produced by this source integration.

## Local acceptance results

- Backend: 1,235 passed, 1 skipped (optional TA-Lib); core, route, Plan Lab R:R isolation and release guards passed.
- Frontend: 491 passed; TypeScript, ESLint and production build passed. Runtime npm audit reported zero vulnerabilities.
- Browser: eight journal/calculator routes in Korean and English at desktop/tablet widths, direct routes, guided query results, summary-first review, review-to-experiment draft handoff and Playbook dialog keyboard focus passed using synthetic data only.
- Dependency resolution and `pip check` passed. Docker configuration was reviewed against the resolved toolchain, but no container build was run because Docker is unavailable locally. CI retains a mandatory TA-Lib regression job.
- The pre-existing untracked `scripts/run_quant_lab_windows.cmd` is not part of this integration.
