from fastapi.testclient import TestClient

from app.core.auth import create_token
from app.main import app

client = TestClient(app)


def test_admin_token_auth(monkeypatch):
    from tests.auth_helpers import admin_headers
    r = client.get('/admin/plans', headers=admin_headers(monkeypatch))
    assert r.status_code in (200, 503)

    bad = client.get('/admin/plans', headers={'Authorization': 'Bearer bad.token', 'X-Role': 'admin'})
    assert bad.status_code == 401
