"""Automated unit tests for agrimenya Progressive Web App (PWA) configuration and assets."""
import json
import os
from utils.pwa import ensure_pwa_assets


def test_pwa_manifest_validity():
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(frontend_dir, "static", "manifest.json")

    assert os.path.exists(manifest_path), "manifest.json must exist in frontend/static"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "agrimenya" in data.get("name", "")
    assert data.get("display") == "standalone"
    assert data.get("start_url") in ("/", "/?source=pwa")
    assert data.get("theme_color") == "#05303f"
    assert data.get("background_color") == "#021824"

    icons = data.get("icons", [])
    assert len(icons) >= 2, "Must contain at least 2 icon specifications"

    sizes = [icon.get("sizes") for icon in icons]
    assert "192x192" in sizes
    assert "512x512" in sizes


def test_service_worker_structure():
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sw_path = os.path.join(frontend_dir, "static", "sw.js")

    assert os.path.exists(sw_path), "sw.js must exist in frontend/static"

    with open(sw_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "addEventListener('install'" in content
    assert "addEventListener('activate'" in content
    assert "addEventListener('fetch'" in content
    assert "offline.html" in content
    assert "skipWaiting()" in content


def test_offline_hub_page():
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    offline_path = os.path.join(frontend_dir, "static", "offline.html")

    assert os.path.exists(offline_path), "offline.html must exist in frontend/static"

    with open(offline_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert "agrimenya" in html
    assert "Offline" in html
    assert "Maize" in html or "Ibigori" in html
    assert "Bugesera" in html or "Musanze" in html
    assert "localStorage" in html


def test_ensure_pwa_assets_execution():
    ensure_pwa_assets()
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(frontend_dir)
    is_sys_root = (
        not root_dir
        or root_dir in ("/", "\\")
        or os.path.splitdrive(root_dir)[1] in ("", "/", "\\")
        or os.path.abspath(root_dir) == os.path.abspath(os.sep)
    )
    target_static = os.path.join(frontend_dir if is_sys_root else root_dir, "static")

    assert os.path.exists(os.path.join(target_static, "manifest.json"))
    assert os.path.exists(os.path.join(target_static, "sw.js"))
    assert os.path.exists(os.path.join(target_static, "offline.html"))


def test_ensure_pwa_assets_container_root_safety():
    from unittest.mock import patch

    # Simulate container where frontend_dir is /app and root_dir is /
    with patch("os.path.abspath", return_value="/app/utils/pwa.py"), \
         patch("os.makedirs") as mock_makedirs:
        ensure_pwa_assets()
        # Verify /static was NEVER created at OS root
        for call in mock_makedirs.call_args_list:
            arg = call[0][0]
            assert arg != "/static" and arg != "\\static", "Must never attempt to create /static at OS root"


def test_ensure_pwa_assets_permission_error_graceful_handling():
    from unittest.mock import patch

    # Simulate environment where os.makedirs raises PermissionError
    with patch("os.makedirs", side_effect=PermissionError(13, "Permission denied: '/static'")):
        # Must execute cleanly without unhandled exception
        ensure_pwa_assets()


def test_same_tab_enforcement_in_pwa_script():
    from unittest.mock import patch
    from utils.pwa import render_pwa_support

    rendered_html = []
    with patch("streamlit.components.v1.html", side_effect=lambda html, **kwargs: rendered_html.append(html)):
        render_pwa_support()

    assert len(rendered_html) == 1, "render_pwa_support must invoke components.html once"
    script = rendered_html[0]

    # Verify no <a ... target="_blank"> remains in injected HTML/templates
    import re
    assert not re.search(r'<a\s+[^>]*target=["\']_blank["\']', script), "pwa_script must not have any <a target='_blank'> links"
    assert 'target="_self"' in script, "pwa_script must specify target='_self'"

    # Verify strict same-tab enforcer functions exist
    assert "enforceStrictSameTabNavigation" in script
    assert "sameTabOpen" in script
    assert "target = '_self'" in script


def test_ai_widget_rendering_and_positioning():
    from unittest.mock import patch
    from components.ai_widget import render_floating_ai_widget

    rendered_markdown = []
    with patch("streamlit.markdown", side_effect=lambda md, **kwargs: rendered_markdown.append(md)):
        render_floating_ai_widget()

    assert len(rendered_markdown) == 1, "render_floating_ai_widget must output markdown"
    md = rendered_markdown[0]

    # Verify bottom right corner placement
    assert "bottom: 24px !important;" in md
    assert "right: 24px !important;" in md

    # Verify target=_self and AI Assistant link
    assert "fab.target = '_self'" in md
    assert "/AI_Assistant" in md
    assert "wireFabClick" in md


