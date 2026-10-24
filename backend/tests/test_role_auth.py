from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_requires_named_session(monkeypatch):
    from tests.auth_helpers import admin_headers

    bad = client.get('/admin/plans', headers={'X-API-Key': 'user-secret', 'X-Role': 'user'})
    assert bad.status_code == 401

    good = client.get('/admin/plans', headers=admin_headers(monkeypatch))
    assert good.status_code in (200, 503)
