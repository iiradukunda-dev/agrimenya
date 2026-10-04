from fastapi.testclient import TestClient

from app.core.auth import create_token
from app.main import app

client = TestClient(app)


def test_admin_token_auth(monkeypatch):
    import app.core.config as config
    config.settings.ADMIN_API_KEY = 'admin-secret'
    config.settings.USER_API_KEY = 'user-secret'
    config.settings.JWT_SECRET = 'test-secret'

    token = create_token('admin', expires_in_seconds=3600)
    r = client.get('/admin/plans', headers={'Authorization': f'Bearer {token}', 'X-Role': 'admin'})
    assert r.status_code in (200, 503)

    bad = client.get('/admin/plans', headers={'Authorization': 'Bearer bad.token', 'X-Role': 'admin'})
    assert bad.status_code == 401
