"""HTTP routes for challenge assets and the profile validation API."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
from typing import Any
from app.config import MAX_PROFILE_BYTES, STATIC_DIR, VALIDATE_ENDPOINT, Settings
from app.rate_limiter import RateLimiter
from app.validation.parser import ParserUnavailableError
from app.validation.service import validate_profile

LOGGER = logging.getLogger("uap_ctf")
RATE_LIMITER = RateLimiter()
ASSETS = {
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "app.js": "application/javascript; charset=utf-8",
}

class ChallengeRequestHandler(BaseHTTPRequestHandler):
    """Serve the challenge frontend and validate participant submissions."""
    settings: Settings

    def do_GET(self) -> None:
        """Serve only allowlisted static assets."""
        name = self.path.split("?", maxsplit=1)[0].lstrip("/") or "index.html"
        content_type = ASSETS.get(name)
        if content_type is None:
            self.send_error(404)
            return
        path: Path = STATIC_DIR / name
        try:
            content = path.read_bytes()
        except OSError:
            LOGGER.exception("Could not read static asset %s", name)
            self.send_error(500)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        """Handle a single JSON validation submission."""
        if self.path != VALIDATE_ENDPOINT:
            self._send_json(404, {"error": "Endpoint tidak ditemukan."})
            return
        if not RATE_LIMITER.allow(self.client_address[0]):
            self._send_json(429, {"error": "Terlalu banyak permintaan. Coba lagi sebentar."})
            return
        profile, error = self._read_profile()
        if error is not None:
            status, payload = error
            self._send_json(status, payload)
            return
        assert profile is not None
        try:
            result = validate_profile(profile, self.settings)
        except ParserUnavailableError:
            LOGGER.exception("AppArmor parser is unavailable")
            self._send_json(503, {"error": "Layanan parser AppArmor tidak tersedia."})
            return
        except (OSError, ValueError):
            LOGGER.exception("Validation request failed")
            self._send_json(500, {"error": "Layanan validator mengalami kesalahan."})
            return
        self._send_json(200, result)

    def _read_profile(self) -> tuple[str | None, tuple[int, dict[str, str]] | None]:
        """Read JSON safely and enforce the profile byte limit."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None, (400, {"error": "Panjang permintaan tidak valid."})
        if length > MAX_PROFILE_BYTES + 1024:
            return None, (413, {"error": "Konfigurasi melebihi batas 20 KB."})
        if length <= 0:
            return None, (400, {"error": "Konfigurasi tidak boleh kosong."})
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, (400, {"error": "Format JSON tidak valid."})
        profile = payload.get("profile") if isinstance(payload, dict) else None
        if not isinstance(profile, str) or not profile.strip():
            return None, (400, {"error": "Konfigurasi tidak boleh kosong."})
        if len(profile.encode("utf-8")) > MAX_PROFILE_BYTES:
            return None, (413, {"error": "Konfigurasi melebihi batas 20 KB."})
        return profile, None

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        """Send a non-cacheable JSON response."""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


def create_server(settings: Settings) -> ThreadingHTTPServer:
    """Create a server with settings attached to its request handler."""
    handler = type("ConfiguredChallengeHandler", (ChallengeRequestHandler,), {"settings": settings})
    return ThreadingHTTPServer((settings.host, settings.port), handler)
