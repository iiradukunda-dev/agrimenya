"""Unit tests for the landing-page hero."""
from unittest.mock import MagicMock, patch
import pytest


def test_home_hero_does_not_inject_a_video_background():
    """Verify the hero renders without a page-wide video or background override."""
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

        assert "<video" not in hero_html
        assert "landing video.mp4" not in hero_html
        assert "setupLandingVideoBackground" not in hero_html
        assert "ag-landing-video-layer" not in hero_html
        assert "background: transparent !important;" not in hero_html
        assert "ag-hero-title" in hero_html
