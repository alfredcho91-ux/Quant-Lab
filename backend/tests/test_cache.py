from __future__ import annotations

from backend.utils import cache as cache_module


def test_data_cache_is_lazy_at_construction(monkeypatch):
    called = False

    def fake_cache(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("disk cache should not initialize during construction")

    monkeypatch.setattr(cache_module, "DISKCACHE_AVAILABLE", True)
    monkeypatch.setattr(cache_module, "Cache", fake_cache)

    cache = cache_module.DataCache(cache_dir="/tmp/should-not-open-at-init")

    assert called is False
    assert cache._cache_ready is False


def test_data_cache_falls_back_to_memory_when_diskcache_fails(monkeypatch, tmp_path):
    def fake_cache(*args, **kwargs):
        raise RuntimeError("readonly database")

    monkeypatch.setattr(cache_module, "DISKCACHE_AVAILABLE", True)
    monkeypatch.setattr(cache_module, "Cache", fake_cache)

    cache = cache_module.DataCache(cache_dir=str(tmp_path / "cache"))

    assert cache.get("missing") is None
    cache.set("foo", "bar")

    assert cache.get("foo") == "bar"
    assert cache.stats()["persistent"] is False


def test_packaged_cache_uses_writable_profile_but_preserves_explicit_external_paths(tmp_path, monkeypatch):
    from backend.config import settings
    bundle = tmp_path / "read-only-install" / "_internal"
    profile = tmp_path / "user-profile"
    monkeypatch.setattr(settings, "IS_FROZEN", True)
    monkeypatch.setattr(settings, "SOURCE_ROOT", bundle)
    monkeypatch.setattr(settings, "PROJECT_ROOT", profile)
    assert cache_module.DataCache()._resolve_cache_dir() == str(profile / ".cache" / "data")
    raw = cache_module.DataCache(cache_dir=str(bundle / ".cache" / "data_service" / "klines"))
    assert raw._resolve_cache_dir() == str(profile / ".cache" / "data_service" / "klines")
    external = str(tmp_path / "custom-cache")
    assert cache_module.DataCache(cache_dir=external)._resolve_cache_dir() == external


def test_source_cache_keeps_existing_paths(tmp_path, monkeypatch):
    from backend.config import settings
    monkeypatch.setattr(settings, "IS_FROZEN", False)
    configured = str(tmp_path / ".cache" / "raw")
    assert cache_module.DataCache(cache_dir=configured)._resolve_cache_dir() == configured
