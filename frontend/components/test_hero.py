"""Unit tests verifying removal of background video and hero styling integrity."""
from unittest.mock import MagicMock, patch
import pytest


def test_home_hero_has_no_video_background():
    """Verify that render_home_hero does not inject video elements or make stAppViewContainer transparent."""
    from components.home_hero import render_home_hero

    mock_st = MagicMock()
    mock_components = MagicMock()

    with patch("components.home_hero.st", mock_st), \
         patch("components.home_hero.components", mock_components):
        render_home_hero()

        # Check st.html calls for styles
        st_html_args = [str(call[0][0]) for call in mock_st.html.call_args_list]
        combined_css = "".join(st_html_args)

        # Confirm transparent body/container override is NOT present
        assert "html, body, [data-testid=\"stAppViewContainer\"], [data-testid=\"stApp\"] {\n        background: transparent !important;" not in combined_css
        assert "[data-testid=\"stAppViewContainer\"], [data-testid=\"stApp\"] {\n        background: transparent" not in combined_css

        # Check components.html call
        assert mock_components.html.called, "components.html was not called"
        hero_html = str(mock_components.html.call_args[0][0])

        # Confirm NO video tag or video source is in hero_html
        assert "<video" not in hero_html
        assert "landing_video.mp4" not in hero_html
        assert "landing video.mp4" not in hero_html

        # Confirm cleanup script for old video is present
        assert "cleanupVideoBackground" in hero_html
        assert "ag-landing-fullpage-video" in hero_html
        assert "existingVideo" in hero_html or "video.remove()" in hero_html
