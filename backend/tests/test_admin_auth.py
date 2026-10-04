from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_routes_require_key():
    r = client.get('/admin/plans')
    assert r.status_code == 401


def test_admin_routes_allow_configured_key(monkeypatch):
    import app.core.config as config
    monkeypatch.setattr(config.settings, 'ADMIN_API_KEY', 'secret-key', raising=False)

    r = client.get('/admin/plans', headers={'X-Admin-Key': 'secret-key'})
    assert r.status_code in (200, 503)
