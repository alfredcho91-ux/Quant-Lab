# API Spec (Core Endpoints)

See `API.md` for detailed examples and full parameter references. This file is the concise contract summary for the public repository.

## Envelopes

- Success response: `{ "success": true, "data": ... }`
- Error response: `{ "success": false, "error": "..." }`

## Core Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/streak-analysis` | `POST` | Streak-pattern probability analysis |
| `/api/bb-mid` | `POST` | Bollinger Band mid-touch probability statistics |
| `/api/combo-filter` | `POST` | Combo filter backtest |
| `/api/trend-indicators` | `POST` | Trend-judgment indicator lookup |
| `/api/hybrid-analysis` | `POST` | Hybrid strategy statistics |
| `/api/hybrid-backtest` | `POST` | Hybrid strategy backtest |
| `/api/hybrid-live` | `POST` | Hybrid strategy live-state evaluation |
| `/api/qx/profiles` | `GET` | Quant-Lab profile list |
| `/api/qx/regime-snapshot` | `POST` | Quant-Lab regime snapshot |
| `/api/qx/conditional-prob` | `POST` | Quant-Lab conditional probability study |
| `/api/qx/event-study` | `POST` | Quant-Lab event study |
| `/api/qx/robustness` | `POST` | Quant-Lab robustness comparison |

## Quality Gates (Quant-Lab)

`/api/qx/*` analyses return a failure response when the incoming dataset does not satisfy the required data-quality gate.

- Included quality metadata: `quality_report`, `quality_gate`, `reproducibility`
