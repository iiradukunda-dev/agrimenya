"""Keep a free-tier backend awake while a user has the app open."""
import json

import streamlit.components.v1 as components

from utils.config import API_BASE_URL

KEEPALIVE_INTERVAL_MS = 5 * 60 * 1000


def render_api_keepalive() -> None:
    """Ping the public liveness endpoint from the active browser tab."""
    health_url = json.dumps(f"{API_BASE_URL.rstrip('/')}/health/live")
    components.html(
        f"""
        <script>
        (() => {{
          const healthUrl = {health_url};
          const ping = () => {{
            fetch(healthUrl, {{ method: "GET", mode: "no-cors", cache: "no-store" }})
              .catch(() => {{}});
          }};
          ping();
          window.setInterval(ping, {KEEPALIVE_INTERVAL_MS});
        }})();
        </script>
        """,
        height=0,
        scrolling=False,
    )
