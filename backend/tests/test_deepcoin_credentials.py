from __future__ import annotations

import base64
import os

from backend.modules.deepcoin import credentials, secure_credentials, service


def test_local_credentials_are_written_atomically_with_restricted_mode(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPCOIN_API_BASE_URL=https://example.test\nOTHER=value\n", encoding="utf-8")
    monkeypatch.setattr(credentials, "ENV_FILE", env_file)
    monkeypatch.delenv("DEEPCOIN_API_KEY", raising=False)
    monkeypatch.delenv("DEEPCOIN_SECRET_KEY", raising=False)
    monkeypatch.delenv("DEEPCOIN_PASSPHRASE", raising=False)
    monkeypatch.setenv("CREDENTIAL_STORAGE", "encrypted_db")
    monkeypatch.setenv("CREDENTIAL_MASTER_KEY", base64.urlsafe_b64encode(b"x" * 32).decode("ascii"))
    monkeypatch.setattr(secure_credentials, "JOURNAL_DB_PATH", tmp_path / "journal.db")

    credentials.save_local_deepcoin_credentials("api key", "secret-key", "pass phrase")

    saved = env_file.read_text(encoding="utf-8")
    assert "DEEPCOIN_API_KEY" not in saved
    assert "DEEPCOIN_SECRET_KEY" not in saved
    assert "DEEPCOIN_PASSPHRASE" not in saved
    assert "OTHER=value" in saved
    assert credentials.has_local_deepcoin_credentials() is True
    assert credentials.credential_storage_source() == "encrypted_db"
    assert os.stat(env_file).st_mode & 0o777 == 0o600


def test_configure_credentials_verifies_before_saving(monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, configured):
            calls.append(("client", configured.api_key, configured.secret_key, configured.passphrase))

        def get_fills(self, *, inst_type, lookback_days):
            calls.append(("verify", inst_type, lookback_days))
            return []

    saved = []
    monkeypatch.setattr(service, "DeepcoinClient", FakeClient)
    monkeypatch.setattr(service, "save_local_deepcoin_credentials", lambda *values: saved.append(values))
    monkeypatch.setattr(service, "get_deepcoin_status_service", lambda: {"success": True, "data": {"configured": True}})

    result = service.configure_deepcoin_credentials_service("api", "secret", "passphrase")

    assert calls == [("client", "api", "secret", "passphrase"), ("verify", "SWAP", 1)]
    assert saved == [("api", "secret", "passphrase")]
    assert result["data"]["configured"] is True
