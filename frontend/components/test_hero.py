"""Unit tests for the landing-page hero and video background."""
from unittest.mock import MagicMock, patch
import pytest


def test_home_hero_sets_up_landing_video_background():
    """Verify the landing page uses its static video behind readable page content."""
    from components.home_hero import render_home_hero

    mock_st = MagicMock()
    mock_components = MagicMock()

    with patch("components.home_hero.st", mock_st), \
         patch("components.home_hero.components", mock_components):
        render_home_hero()

        # Check st.html calls for styles
        st_html_args = [str(call[0][0]) for call in mock_st.html.call_args_list]
        combined_css = "".join(st_html_args)

        assert combined_css

        assert mock_components.html.called, "components.html was not called"
        hero_html = str(mock_components.html.call_args[0][0])

        assert "/assets/landing%20video.mp4" in hero_html
        assert "autoplay muted loop playsinline" in hero_html
        assert "object-fit: cover" in hero_html
        assert "rgba(248, 250, 252, 0.64)" in hero_html
        assert "setupLandingVideoBackground" in hero_html
        assert "ag-landing-fullpage-video" in hero_html
        assert "__agrimenyaLandingVideoCleanup" in hero_html


def test_landing_video_url_encodes_asset_name():
    from components.home_hero import _landing_video_url

    assert _landing_video_url() == "/assets/landing%20video.mp4"
