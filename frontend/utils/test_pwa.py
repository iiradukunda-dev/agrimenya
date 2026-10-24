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
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    root_static = os.path.join(root_dir, "static")

    assert os.path.exists(os.path.join(root_static, "manifest.json"))
    assert os.path.exists(os.path.join(root_static, "sw.js"))
    assert os.path.exists(os.path.join(root_static, "offline.html"))
