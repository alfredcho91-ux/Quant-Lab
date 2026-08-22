"""Protected local storage for read-only Deepcoin API credentials."""

from __future__ import annotations

import base64
import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Literal, Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.config.settings import JOURNAL_DB_PATH, get_app_environment

MASTER_KEY_ENV = "CREDENTIAL_MASTER_KEY"
SERVICE_NAME = "Quant Master"
StorageSource = Literal["environment", "keyring", "encrypted_db", "not_configured"]


class CredentialStorageError(RuntimeError):
    """Raised when protected local credential storage cannot be used."""


@dataclass(frozen=True)
class StoredDeepcoinCredentials:
    api_key: str
    secret_key: str
    passphrase: str


def storage_mode() -> Literal["keyring", "encrypted_db"]:
    configured = os.getenv("CREDENTIAL_STORAGE", "auto").strip().lower()
    if configured not in {"auto", "keyring", "encrypted_db"}:
        raise CredentialStorageError("CREDENTIAL_STORAGE must be auto, keyring, or encrypted_db")
    if configured == "keyring":
        return "keyring"
    if configured == "encrypted_db" or get_app_environment() == "production" or _master_key_is_configured():
        return "encrypted_db"
    return "keyring"


def load_stored_credentials() -> tuple[Optional[StoredDeepcoinCredentials], StorageSource]:
    """Load environment credentials first, then the protected local store."""
    environment = _environment_credentials()
    if environment is not None:
        return environment, "environment"
    mode = storage_mode()
    payload = _load_payload(mode)
    if not payload:
        return None, "not_configured"
    try:
        values = json.loads(payload)
        return StoredDeepcoinCredentials(
            _required(values.get("api_key")),
            _required(values.get("secret_key")),
            _required(values.get("passphrase")),
        ), mode
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CredentialStorageError("Stored Deepcoin credentials are invalid") from exc


def save_stored_credentials(api_key: str, secret_key: str, passphrase: str) -> StorageSource:
    credentials = StoredDeepcoinCredentials(_required(api_key), _required(secret_key), _required(passphrase))
    mode = storage_mode()
    payload = json.dumps(credentials.__dict__, separators=(",", ":"))
    _save_payload(mode, payload)
    return mode


def delete_stored_credentials() -> bool:
    deleted = _delete_payload(storage_mode())
    _clear_environment_values()
    return deleted


def _environment_credentials() -> Optional[StoredDeepcoinCredentials]:
    api_key = os.getenv("DEEPCOIN_API_KEY", "").strip()
    secret_key = os.getenv("DEEPCOIN_SECRET_KEY", "")
    passphrase = os.getenv("DEEPCOIN_PASSPHRASE", "")
    if not all((api_key, secret_key, passphrase)):
        return None
    return StoredDeepcoinCredentials(api_key, secret_key, passphrase)


def _save_payload(mode: str, payload: str) -> None:
    try:
        if mode == "keyring":
            _keyring().set_password(SERVICE_NAME, "deepcoin", payload)
            return
        envelope = _encrypt(payload)
        with _connect() as connection:
            connection.execute(
                """INSERT INTO secure_credentials (provider, payload, updated_at) VALUES ('deepcoin', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(provider) DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP""",
                (envelope,),
            )
    except (sqlite3.Error, ValueError, TypeError) as exc:
        raise CredentialStorageError("Protected credential storage is unavailable") from exc


def _load_payload(mode: str) -> Optional[str]:
    try:
        if mode == "keyring":
            return _keyring().get_password(SERVICE_NAME, "deepcoin")
        with _connect() as connection:
            row = connection.execute("SELECT payload FROM secure_credentials WHERE provider = 'deepcoin'").fetchone()
        return _decrypt(str(row[0])) if row else None
    except (sqlite3.Error, ValueError, TypeError, InvalidTag) as exc:
        raise CredentialStorageError("Stored Deepcoin credentials could not be loaded") from exc


def _delete_payload(mode: str) -> bool:
    try:
        if mode == "keyring":
            vault = _keyring()
            if not vault.get_password(SERVICE_NAME, "deepcoin"):
                return False
            vault.delete_password(SERVICE_NAME, "deepcoin")
            return True
        with _connect() as connection:
            return connection.execute("DELETE FROM secure_credentials WHERE provider = 'deepcoin'").rowcount > 0
    except (sqlite3.Error, ValueError, TypeError) as exc:
        raise CredentialStorageError("Protected Deepcoin credentials could not be deleted") from exc


def _connect() -> sqlite3.Connection:
    JOURNAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(JOURNAL_DB_PATH, timeout=30)
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS secure_credentials (
        provider TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    return connection


def _encrypt(payload: str) -> str:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_master_key()).encrypt(nonce, payload.encode("utf-8"), b"quant-master:deepcoin:v1")
    return json.dumps({"v": 1, "nonce": _encode(nonce), "ciphertext": _encode(ciphertext)}, separators=(",", ":"))


def _decrypt(envelope_text: str) -> str:
    envelope = json.loads(envelope_text)
    if envelope.get("v") != 1:
        raise CredentialStorageError("Unsupported credential encryption format")
    return AESGCM(_master_key()).decrypt(
        _decode(envelope["nonce"]), _decode(envelope["ciphertext"]), b"quant-master:deepcoin:v1"
    ).decode("utf-8")


def _master_key_is_configured() -> bool:
    return bool(os.getenv(MASTER_KEY_ENV, "").strip())


def _master_key() -> bytes:
    raw = os.getenv(MASTER_KEY_ENV, "").strip()
    if not raw:
        raise CredentialStorageError(f"{MASTER_KEY_ENV} is required for encrypted credential storage")
    try:
        key = _decode(raw)
    except (TypeError, ValueError) as exc:
        raise CredentialStorageError(f"{MASTER_KEY_ENV} must be URL-safe base64") from exc
    if len(key) != 32:
        raise CredentialStorageError(f"{MASTER_KEY_ENV} must decode to 32 bytes")
    return key


def _keyring():
    try:
        import keyring
    except ImportError as exc:
        raise CredentialStorageError("Install keyring or configure CREDENTIAL_MASTER_KEY") from exc
    return keyring


def _required(value: object) -> str:
    normalized = str(value or "").strip()
    if not normalized or "\n" in normalized or "\r" in normalized:
        raise ValueError("Invalid Deepcoin credential value")
    return normalized


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _clear_environment_values() -> None:
    for key in ("DEEPCOIN_API_KEY", "DEEPCOIN_SECRET_KEY", "DEEPCOIN_PASSPHRASE"):
        os.environ.pop(key, None)


__all__ = [
    "CredentialStorageError", "StoredDeepcoinCredentials", "delete_stored_credentials",
    "load_stored_credentials", "save_stored_credentials", "storage_mode",
]
