from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_requires_role_header_and_key(monkeypatch):
    import app.core.config as config
    config.settings.ADMIN_API_KEY = 'admin-secret'
    config.settings.USER_API_KEY = 'user-secret'

    bad = client.get('/admin/plans', headers={'X-API-Key': 'user-secret', 'X-Role': 'user'})
    assert bad.status_code == 401

    good = client.get('/admin/plans', headers={'X-API-Key': 'admin-secret', 'X-Role': 'admin'})
    assert good.status_code in (200, 503)
