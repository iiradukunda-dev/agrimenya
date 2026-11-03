from unittest.mock import patch

from components import browser_keepalive


def test_browser_keepalive_pings_public_liveness_endpoint_periodically():
    with patch.object(browser_keepalive.components, "html") as render_html:
        browser_keepalive.render_api_keepalive()

    html = render_html.call_args.args[0]
    assert "https://api.example.test/health/live" not in html
    assert "/health/live" in html
    assert f"window.setInterval(ping, {browser_keepalive.KEEPALIVE_INTERVAL_MS})" in html
    assert 'mode: "no-cors"' in html
    assert render_html.call_args.kwargs == {"height": 0, "scrolling": False}


def test_browser_keepalive_uses_configured_api_origin():
    with patch.object(browser_keepalive, "API_BASE_URL", "https://api.example.test/"), patch.object(
        browser_keepalive.components, "html"
    ) as render_html:
        browser_keepalive.render_api_keepalive()

    assert "https://api.example.test/health/live" in render_html.call_args.args[0]
