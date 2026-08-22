"""Local-only storage for read-only Deepcoin credentials."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from backend.config.settings import PROJECT_ROOT
from backend.modules.deepcoin.secure_credentials import (
    CredentialStorageError,
    delete_stored_credentials,
    load_stored_credentials,
    save_stored_credentials,
)

ENV_FILE = PROJECT_ROOT / ".env"
DEEPCOIN_ENV_KEYS = (
    "DEEPCOIN_API_KEY",
    "DEEPCOIN_SECRET_KEY",
    "DEEPCOIN_PASSPHRASE",
)


def has_local_deepcoin_credentials() -> bool:
    """Return whether a protected local credential store has valid values."""
    credentials, source = load_stored_credentials()
    return credentials is not None and source in {"keyring", "encrypted_db"}


def credential_storage_source() -> str:
    """Return storage metadata without exposing the stored credentials."""
    _credentials, source = load_stored_credentials()
    return source


def save_local_deepcoin_credentials(api_key: str, secret_key: str, passphrase: str) -> str:
    """Store credentials in the OS vault or encrypted SQLite, never in `.env`."""
    source = save_stored_credentials(api_key, secret_key, passphrase)
    _remove_legacy_env_values()
    for key in DEEPCOIN_ENV_KEYS:
        os.environ.pop(key, None)
    return source


def delete_local_deepcoin_credentials() -> bool:
    """Remove persisted credentials and the legacy local `.env` values."""
    deleted = delete_stored_credentials()
    _remove_legacy_env_values()
    return deleted


def _remove_legacy_env_values() -> None:
    """Delete only Deepcoin key lines, preserving unrelated local settings."""
    if not ENV_FILE.is_file():
        return
    existing = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.is_file() else ""
    output_lines = []
    key_pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")
    for line in existing.splitlines():
        match = key_pattern.match(line.strip())
        key = match.group(1) if match else None
        if key not in DEEPCOIN_ENV_KEYS:
            output_lines.append(line)

    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_path = tempfile.mkstemp(prefix=".env.", dir=str(ENV_FILE.parent), text=True)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write("\n".join(output_lines).rstrip() + ("\n" if output_lines else ""))
        os.replace(temp_path, ENV_FILE)
        os.chmod(ENV_FILE, 0o600)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise



__all__ = [
    "CredentialStorageError",
    "credential_storage_source",
    "delete_local_deepcoin_credentials",
    "has_local_deepcoin_credentials",
    "save_local_deepcoin_credentials",
]
