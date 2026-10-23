"""Contracts where the current journal meets Quant Lab's existing features."""
from __future__ import annotations

import base64
import json
import sqlite3
from contextlib import closing

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient

from backend import main
from backend.modules.exchanges import encrypted_store, keyring_store


def test_backtest_templates_and_user_playbook_have_distinct_routes():
    with TestClient(main.app) as client:
        templates = client.get('/api/strategies')
        playbook = client.get('/api/playbook/strategies')
        assert templates.status_code == playbook.status_code == 200
        assert templates.json()['data']
        assert all(isinstance(item['id'], str) for item in templates.json()['data'])
        assert isinstance(playbook.json()['data'], list)
        routes = [(route.path, method) for route in main.app.routes for method in getattr(route, 'methods', [])]
        assert len(routes) == len(set(routes))


def seed_legacy(path, key):
    payload = json.dumps({'api_key': 'fixture-api', 'secret_key': 'fixture-secret', 'passphrase': 'fixture-pass'})
    nonce = b'n' * 12
    envelope = json.dumps({'v': 1, 'nonce': base64.urlsafe_b64encode(nonce).decode(),
                           'ciphertext': base64.urlsafe_b64encode(AESGCM(key).encrypt(nonce, payload.encode(), b'quant-master:deepcoin:v1')).decode()})
    with closing(sqlite3.connect(path)) as conn:
        conn.execute('CREATE TABLE secure_credentials(provider TEXT PRIMARY KEY, payload TEXT, updated_at TEXT)')
        conn.execute("INSERT INTO secure_credentials VALUES ('deepcoin', ?, 't')", (envelope,))
        conn.commit()
    return payload, envelope


def test_same_profile_legacy_ciphertext_is_read_without_destructive_migration(tmp_path, monkeypatch):
    path = tmp_path / 'legacy.db'
    key = b'x' * 32
    monkeypatch.setenv('CREDENTIAL_MASTER_KEY', base64.urlsafe_b64encode(key).decode())
    payload, envelope = seed_legacy(path, key)
    assert encrypted_store.load_encrypted_credentials('deepcoin', db_path=path) == payload
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute("SELECT payload FROM secure_credentials WHERE provider='deepcoin'").fetchone()[0] == envelope
    assert encrypted_store.load_encrypted_credentials('binance', db_path=path) is None


def test_new_ciphertext_wins_and_explicit_delete_cannot_revive_legacy(tmp_path, monkeypatch):
    path = tmp_path / 'legacy.db'
    key = b'x' * 32
    monkeypatch.setenv('CREDENTIAL_MASTER_KEY', base64.urlsafe_b64encode(key).decode())
    seed_legacy(path, key)
    newer = json.dumps({'api_key': 'new-api', 'secret_key': 'new-secret', 'passphrase': 'new-pass'})
    encrypted_store.save_encrypted_credentials('deepcoin', newer, db_path=path)
    assert encrypted_store.load_encrypted_credentials('deepcoin', db_path=path) == newer
    assert encrypted_store.delete_encrypted_credentials('deepcoin', db_path=path)
    assert encrypted_store.load_encrypted_credentials('deepcoin', db_path=path) is None


def test_credential_namespace_is_separate_from_trade_journal_and_unscoped_legacy(monkeypatch):
    monkeypatch.setattr(keyring_store, 'credential_profile_id', lambda: 'quant-test-profile')
    assert keyring_store.service_name() == 'Quant Lab:profile:quant-test-profile'
    assert keyring_store.service_name() not in {'Quant Master', 'Trade Journal Free'}


def test_sample_boundary_blocks_quant_research_and_private_presets(monkeypatch):
    monkeypatch.setattr(main, 'IS_SAMPLE', True)
    # No lifespan: this checks the request boundary independently of fixture startup.
    client = TestClient(main.app)
    for method, path in [('get', '/api/presets'), ('get', '/api/strategies'),
                         ('post', '/api/backtest'), ('post', '/api/ai/research'),
                           ('post', '/api/streak-analysis'), ('post', '/api/stop-loss-lab/analyze')]:
        response = getattr(client, method)(path)
        assert response.status_code == 403
        assert response.json()['error_code'] == 'SAMPLE_OFFLINE'
    assert client.get('/api/journal').status_code == 200
