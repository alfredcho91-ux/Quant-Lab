"""Legacy Deepcoin names delegate to the single profile-scoped credential store."""
from backend.modules.exchanges.credentials import (
    CredentialStorageError, StoredCredentials as StoredDeepcoinCredentials,
    credential_storage_mode, delete_exchange_credentials,
    resolve_exchange_credentials, save_local_exchange_credentials,
)


def storage_mode():
    return credential_storage_mode()


def load_stored_credentials():
    resolved = resolve_exchange_credentials("deepcoin")
    if resolved.storage_error:
        raise CredentialStorageError(resolved.storage_error)
    return resolved.credentials, ("not_configured" if resolved.source == "none" else resolved.source)


def save_stored_credentials(api_key: str, secret_key: str, passphrase: str):
    save_local_exchange_credentials("deepcoin", api_key, secret_key, passphrase)
    return credential_storage_mode()


def delete_stored_credentials() -> bool:
    return delete_exchange_credentials("deepcoin").deleted
