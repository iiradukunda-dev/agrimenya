import pytest

from deployment.render_start import _api_origin, _nginx_configuration


def test_api_origin_removes_trailing_slash(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://agri-menya-api.onrender.com/")

    assert _api_origin() == "https://agri-menya-api.onrender.com"


def test_api_origin_uses_render_service_host(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.setenv("API_HOST", "agrimenya-api-20261030.onrender.com")

    assert _api_origin() == "https://agrimenya-api-20261030.onrender.com"


@pytest.mark.parametrize(
    "api_base_url",
    [
        "ftp://api.example.com",
        "https://user:password@api.example.com",
        "https://api.example.com/v1",
        "https://api.example.com?key=value",
    ],
)
def test_api_origin_rejects_non_origin_urls(monkeypatch, api_base_url):
    monkeypatch.setenv("API_BASE_URL", api_base_url)

    with pytest.raises(RuntimeError, match="API_BASE_URL"):
        _api_origin()


def test_nginx_configuration_routes_oauth_to_api_on_the_public_port():
    config = _nginx_configuration(10000, "https://agri-menya-api.onrender.com")

    assert "listen 10000;" in config
    assert "location = /community/auth/google {" in config
    assert "location = /community/auth/google/callback {" in config
    assert "proxy_pass https://agri-menya-api.onrender.com;" in config
    assert "proxy_pass http://127.0.0.1:8502;" in config
    assert "@API_BASE_URL@" not in config
    assert "@PORT@" not in config
