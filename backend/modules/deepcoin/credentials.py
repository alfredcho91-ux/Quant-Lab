"""Compatibility functions backed by the profile-scoped exchange authority."""
from backend.modules.exchanges.credentials import (
    CredentialStorageError, credential_source, credential_storage_mode,
    delete_exchange_credentials, load_exchange_credentials, save_local_exchange_credentials,
)


def has_local_deepcoin_credentials() -> bool:
    return credential_source("deepcoin") in {"keyring", "encrypted_db"} and load_exchange_credentials("deepcoin") is not None


def credential_storage_source() -> str:
    source = credential_source("deepcoin")
    return "not_configured" if source == "none" else source


def save_local_deepcoin_credentials(api_key: str, secret_key: str, passphrase: str) -> str:
    save_local_exchange_credentials("deepcoin", api_key, secret_key, passphrase)
    return credential_storage_mode()


def delete_local_deepcoin_credentials() -> bool:
    return delete_exchange_credentials("deepcoin").deleted
