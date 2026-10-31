"""Start Streamlit behind Nginx for same-origin OAuth routing."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_HEALTH_URL = "http://127.0.0.1:8502/_stcore/health"


def _api_origin() -> str:
    value = os.environ.get("API_BASE_URL", "").strip()
    if not value:
        api_host = os.environ.get("API_HOST", "").strip()
        value = f"https://{api_host}" if api_host else "http://localhost:8000"
    value = value.rstrip("/")
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError("API_BASE_URL must be an HTTP(S) origin without credentials or a path")
    return f"{parsed.scheme}://{parsed.netloc}"


def _nginx_configuration(port: int, api_origin: str) -> str:
    template = (ROOT / "deployment" / "nginx.conf.template").read_text(encoding="utf-8")
    return template.replace("@PORT@", str(port)).replace("@API_BASE_URL@", api_origin)


def _wait_for_frontend(process: subprocess.Popen, timeout: int = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(f"Streamlit exited during startup with status {exit_code}")
        try:
            with urlopen(FRONTEND_HEALTH_URL, timeout=2):
                return
        except (OSError, URLError):
            time.sleep(0.5)
    raise RuntimeError(f"Streamlit did not become healthy within {timeout} seconds")


def _stop_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + 10
    for process in processes:
        if process.poll() is None:
            remaining = max(0, deadline - time.monotonic())
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    try:
        port = int(os.environ.get("PORT", "8501"))
    except ValueError as exc:
        raise RuntimeError("PORT must be an integer") from exc
    if not 1024 <= port <= 65535:
        raise RuntimeError("PORT must be between 1024 and 65535")

    api_base_url = _api_origin()
    os.environ["API_BASE_URL"] = api_base_url
    config_path = Path("/tmp/nginx.conf")
    config_path.write_text(_nginx_configuration(port, api_base_url), encoding="utf-8")

    def handle_shutdown(signum, _frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    processes = []
    try:
        frontend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "Home.py",
                "--server.headless=true",
                "--server.port=8502",
                "--server.address=127.0.0.1",
            ],
            cwd=ROOT,
            env=os.environ.copy(),
        )
        processes.append(frontend)
        _wait_for_frontend(frontend)
        proxy = subprocess.Popen(
            ["nginx", "-c", str(config_path), "-g", "daemon off;"],
            cwd=ROOT,
        )
        processes.append(proxy)

        while True:
            for name, process in (("Streamlit", frontend), ("Nginx", proxy)):
                exit_code = process.poll()
                if exit_code is not None:
                    print(f"{name} exited with status {exit_code}", file=sys.stderr, flush=True)
                    return exit_code or 1
            time.sleep(1)
    finally:
        _stop_processes(processes)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Frontend startup failed: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1) from exc
