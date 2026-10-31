"""Bounded public-market acquisition and pure research orchestration."""
from datetime import datetime, timedelta, timezone
import hashlib

from backend.utils.data_service import fetch_binance_klines
from .statistics import INTERVAL_MS, prepare, distributions, weekend_distribution
from .simulation import breakout_distribution, optimize


def candle_statistics(request, *, now=None, fetch=fetch_binance_klines):
    """Return observed daily-candle distributions without running a simulation."""
    now = now or datetime.now(timezone.utc)
    duration = INTERVAL_MS["1d"]
    end = int(now.timestamp()*1000)//duration*duration
    warmup = request.lookback+8
    raw = fetch(f"{request.coin}USDT", "1d", total_candles=request.candles+warmup, end_time=end-1)
    daily = prepare(raw, "1d", end, request.lookback)
    window = daily.tail(request.candles)
    start = int(window.iloc[0].open_time)
    fingerprint = hashlib.sha256(
        daily[["open_time", "open", "high", "low", "close"]].to_csv(index=False).encode()
    ).hexdigest()
    return {
        "config": request.model_dump(mode="json"),
        "data": {
            "source": "Binance USDT-M Futures public klines",
            "as_of": end,
            "fingerprint_sha256": fingerprint,
            "candle_count": len(window),
            "first": int(window.iloc[0].open_time),
            "last": int(window.iloc[-1].end_time),
        },
        "distributions": {
            "all": distributions({"1d": daily}, start, end)["1d"],
            "weekend": weekend_distribution(daily, start, end),
        },
    }


def analyze(request, *, now=None, fetch=fetch_binance_klines):
    now = now or datetime.now(timezone.utc)
    start = int(datetime.combine(request.start, datetime.min.time(), timezone.utc).timestamp()*1000)
    requested_end = int(datetime.combine(request.end+timedelta(days=1), datetime.min.time(), timezone.utc).timestamp()*1000)
    as_of = min(requested_end, int(now.timestamp()*1000))
    execution_step = INTERVAL_MS[request.execution_interval]
    end = as_of//execution_step*execution_step
    frames = {}
    fingerprint = hashlib.sha256()
    for interval in ("1d", "1w", request.execution_interval):
        duration = INTERVAL_MS[interval]
        warmup = request.lookback+8 if interval in ("1d", "1w") else 0
        # Anchor the seed to START, not the requested end-date's remainder.
        # Extending a date range must not shift earlier Wilder initialization.
        anchor = 4*INTERVAL_MS["1d"] if interval == "1w" else 0
        earliest = ((start-anchor)//duration-warmup)*duration+anchor
        last_open = ((requested_end-1-anchor)//duration)*duration+anchor
        count = (last_open-earliest)//duration+1
        raw = fetch(f"{request.coin}USDT", interval, total_candles=count, end_time=requested_end-1)
        frame = prepare(raw, interval, as_of, request.lookback)
        if interval == request.execution_interval:
            frame = frame.loc[(frame.open_time >= start) & (frame.end_time <= end)].copy()
            if frame.empty:
                raise ValueError("No completed execution candles in the requested date range")
        frames[interval] = frame
        fingerprint.update(frame[["open_time", "open", "high", "low", "close"]].to_csv(index=False).encode())
    execution = frames[request.execution_interval]
    result = optimize(request, frames[request.reference_interval], execution, start, end)
    return {"config": request.model_dump(mode="json"), "data": {
                "source": "Binance USDT-M Futures public klines", "as_of": end,
                "fingerprint_sha256": fingerprint.hexdigest(),
                "counts": {key: len(frame) for key, frame in frames.items()},
                "execution_first": int(execution.iloc[0].open_time), "execution_last": int(execution.iloc[-1].end_time)},
            "distributions": distributions({key: frames[key] for key in ("1d", "1w")}, start, end),
            "weekend_distribution": weekend_distribution(frames["1d"], start, end),
            "breakouts": {key: breakout_distribution(frames[key], execution, key, start, end) for key in ("1d", "1w")},
            **result}
