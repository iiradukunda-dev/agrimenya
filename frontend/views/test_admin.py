import re
from pathlib import Path

from components.icons import get_base64_svg


def test_admin_view_references_existing_svg_assets():
    admin_source = Path(__file__).with_name("admin.py").read_text(encoding="utf-8")
    icon_paths = re.findall(r'render_icon_(?:title|subheader)\("(assets/[^"]+)"', admin_source)

    assert icon_paths
    for icon_path in icon_paths:
        assert get_base64_svg(icon_path)
