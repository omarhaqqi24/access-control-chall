"""Docker entry point for the challenge application."""
import logging
import os
from app.config import Settings
from app.http_server import create_server


def main() -> None:
    """Start and serve the challenge as a non-root process."""
    if os.geteuid() == 0:
        raise SystemExit("Jalankan service sebagai user non-root.")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_environment()
    server = create_server(settings)
    logging.info("Challenge listening on %s:%s", settings.host, settings.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutdown requested")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
