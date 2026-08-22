"""Local-only storage for read-only Deepcoin credentials."""

from __future__ import annotations

import os
import re
import shlex
import tempfile
from pathlib import Path
from typing import Dict

from backend.config.settings import PROJECT_ROOT

ENV_FILE = PROJECT_ROOT / ".env"
DEEPCOIN_ENV_KEYS = (
    "DEEPCOIN_API_KEY",
    "DEEPCOIN_SECRET_KEY",
    "DEEPCOIN_PASSPHRASE",
)


def has_local_deepcoin_credentials() -> bool:
    """Return whether the local git-ignored env file contains all key names."""
    if not ENV_FILE.is_file():
        return False
    try:
        values = _read_env_values(ENV_FILE)
    except OSError:
        return False
    return all(values.get(key) for key in DEEPCOIN_ENV_KEYS)


def save_local_deepcoin_credentials(api_key: str, secret_key: str, passphrase: str) -> None:
    """Atomically write read-only credentials to the project-local `.env` file.

    `.env` is already ignored by git and loaded by the project start scripts. The
    credentials are also placed in the running process environment so a restart
    is not required after a successful connection check.
    """
    values = {
        "DEEPCOIN_API_KEY": _validate_value("api_key", api_key),
        "DEEPCOIN_SECRET_KEY": _validate_value("secret_key", secret_key),
        "DEEPCOIN_PASSPHRASE": _validate_value("passphrase", passphrase),
    }
    existing = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.is_file() else ""
    output_lines = []
    replaced = set()
    key_pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")
    for line in existing.splitlines():
        match = key_pattern.match(line.strip())
        key = match.group(1) if match else None
        if key in values:
            output_lines.append(f"{key}={shlex.quote(values[key])}")
            replaced.add(key)
        else:
            output_lines.append(line)
    for key, value in values.items():
        if key not in replaced:
            output_lines.append(f"{key}={shlex.quote(value)}")

    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_path = tempfile.mkstemp(prefix=".env.", dir=str(ENV_FILE.parent), text=True)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write("\n".join(output_lines).rstrip() + "\n")
        os.replace(temp_path, ENV_FILE)
        os.chmod(ENV_FILE, 0o600)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise

    os.environ.update(values)


def _validate_value(name: str, value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized or "\n" in normalized or "\r" in normalized:
        raise ValueError(f"Deepcoin {name} is invalid")
    return normalized


def _read_env_values(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if not separator or key not in DEEPCOIN_ENV_KEYS:
            continue
        values[key] = value.strip().strip("'\"")
    return values


__all__ = ["has_local_deepcoin_credentials", "save_local_deepcoin_credentials"]
