# Cache Strategy

## Objective

Define where caching is used and which TTLs apply so runtime behavior stays predictable across development and operations.

## Shared Interface

All caches should use `backend/utils/cache.py::DataCache`.

- TTL inputs: `ttl_seconds` or `ttl_minutes`
- Backing store:
  - persistent disk cache when `diskcache` is available
  - in-memory fallback otherwise

## Current Cache Map

| Area | Location | TTL | Purpose |
|---|---|---:|---|
| Market metadata | `backend/utils/data_service.py::discover_timeframes` | 5 seconds | CSV timeframe discovery |
| Fear & Greed index | `backend/utils/data_service.py::get_fear_and_greed_index` | 300 seconds | External API reuse |
| Market tickers | `backend/utils/data_service.py::get_market_prices` | 30 seconds | Dashboard price lookups |
| Streak data | `backend/strategy/streak/cache_ops.py::data_cache` | 5 minutes | DataFrame cache |
| Streak analysis | `backend/strategy/streak/cache_ops.py::analysis_cache` | 10 minutes | Analysis-result cache |
| Streak indicators | `backend/strategy/streak/cache_ops.py::indicators_cache` | 30 minutes | Indicator-calculation cache |

## Operating Rules

1. New caches should not introduce a parallel cache implementation outside `DataCache`.
2. Cache keys must be deterministic and derived from request parameters or normalized inputs.
3. Cache usage must be made explicit in the service or orchestration layer.
4. If a TTL changes, update both the code comments and this document in the same change.
