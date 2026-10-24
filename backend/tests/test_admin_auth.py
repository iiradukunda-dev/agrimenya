from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_routes_require_named_session():
    r = client.get('/admin/plans')
    assert r.status_code == 401


def test_admin_routes_reject_legacy_shared_key(monkeypatch):
    from tests.auth_helpers import admin_headers
    r = client.get('/admin/plans', headers={'X-Admin-Key': 'secret-key'})
    assert r.status_code == 401
    r = client.get('/admin/plans', headers=admin_headers(monkeypatch))
    assert r.status_code in (200, 503)
