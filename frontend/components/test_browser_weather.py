from unittest.mock import patch

from components.browser_weather import render_browser_weather


def test_browser_weather_renders_district_scoped_open_meteo_fallback():
    with patch("components.browser_weather.components.html") as render_html:
        render_browser_weather("Bugesera", (-2.2167, 30.25))

    document = render_html.call_args.args[0]
    assert 'const district = "Bugesera"' in document
    assert "const latitude = -2.2167" in document
    assert "const longitude = 30.25" in document
    assert 'wind_speed_unit: "kmh"' in document
    assert "api.open-meteo.com/v1/forecast" in document
    assert render_html.call_args.kwargs["scrolling"] is False
