from __future__ import annotations

import json
import re
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import uvicorn
import webview


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_DIST_INDEX = PROJECT_ROOT / "frontend" / "dist" / "index.html"


if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app  # noqa: E402


def wait_for_server(host: str, port: int, timeout_seconds: int = 20) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.2)
    return False


def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) != 0


def pick_port(host: str, preferred_port: int = 8000, max_attempts: int = 30) -> int:
    for candidate in range(preferred_port, preferred_port + max_attempts):
        if is_port_available(host, candidate):
            return candidate
    raise RuntimeError("Could not find an available local port.")


def get_download_filename(content_disposition: str | None) -> str:
    if not content_disposition:
        return "recibos.zip"
    match = re.search(r'filename="?([^";]+)"?', content_disposition)
    if not match:
        return "recibos.zip"
    return match.group(1)


def parse_error_detail(payload: bytes) -> str:
    if not payload:
        return "Unknown error"
    try:
        parsed = json.loads(payload.decode("utf-8"))
        if isinstance(parsed, dict):
            detail = parsed.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail.strip()
    except Exception:
        pass

    text = payload.decode("utf-8", errors="ignore").strip()
    return text or "Unknown error"


class DesktopApi:
    def __init__(self, backend_base_url: str) -> None:
        self.backend_base_url = backend_base_url.rstrip("/")
        self.window: webview.Window | None = None

    def set_window(self, window: webview.Window) -> None:
        self.window = window

    def download_zip(self, session_id: str) -> dict[str, Any]:
        if self.window is None:
            return {"saved": False, "error": "Desktop window is not ready."}

        endpoint = f"{self.backend_base_url}/api/v1/receipts/zip"
        query = urlencode({"session_id": session_id})
        request = Request(f"{endpoint}?{query}", method="GET")

        try:
            with urlopen(request, timeout=120) as response:
                zip_bytes = response.read()
                filename = get_download_filename(
                    response.headers.get("content-disposition")
                )
        except HTTPError as exception:
            error_payload = exception.read()
            return {
                "saved": False,
                "error": parse_error_detail(error_payload),
            }
        except URLError as exception:
            return {
                "saved": False,
                "error": f"Cannot connect to local server: {exception.reason}",
            }
        except Exception as exception:
            return {
                "saved": False,
                "error": f"Failed to download ZIP file: {exception}",
            }

        save_target = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=filename,
            file_types=("ZIP file (*.zip)",),
        )

        if not save_target:
            return {"saved": False, "error": "Save canceled."}

        selected_path: str
        if isinstance(save_target, (tuple, list)):
            selected_path = str(save_target[0])
        else:
            selected_path = str(save_target)

        try:
            output_path = Path(selected_path)
            output_path.write_bytes(zip_bytes)
        except Exception as exception:
            return {"saved": False, "error": f"Cannot save ZIP file: {exception}"}

        return {"saved": True, "path": selected_path}


def run() -> None:
    if not FRONTEND_DIST_INDEX.exists():
        raise FileNotFoundError(
            "Frontend build not found. Run 'npm install && npm run build' inside 'frontend' first."
        )

    host = "127.0.0.1"
    port = pick_port(host)
    app_url = f"http://{host}:{port}"

    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    if not wait_for_server(host, port):
        server.should_exit = True
        raise RuntimeError("Backend server did not start in time.")

    desktop_api = DesktopApi(app_url)
    window = webview.create_window(
        title="Payment Receipt Generator",
        url=app_url,
        js_api=desktop_api,
        min_size=(960, 720),
        width=1240,
        height=860,
    )
    desktop_api.set_window(window)

    def shutdown_server() -> None:
        server.should_exit = True

    window.events.closed += shutdown_server

    try:
        webview.start(debug=False)
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    run()
