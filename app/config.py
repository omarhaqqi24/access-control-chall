"""Runtime configuration and challenge constants."""
from dataclasses import dataclass
from pathlib import Path
import os

APP_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = APP_ROOT / "static"
VALIDATE_ENDPOINT = "/api/challenges/secure-file-manager/validate"
MAX_PROFILE_BYTES = 20 * 1024
PARSER_TIMEOUT_SECONDS = 5
TEMP_DIRECTORY = Path("/tmp")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

@dataclass(frozen=True)
class Check:
    """One scored validation check."""
    check_id: str
    label: str
    points: int

CHECKS = (
    Check("profile", "Struktur profil dan executable", 10),
    Check("includes", "Include wajib", 10),
    Check("config_read", "Baca konfigurasi", 20),
    Check("tmp_rw", "Baca dan tulis file sementara", 20),
    Check("home_read", "Baca direktori home", 20),
    Check("log_deny_write", "Blokir write direktori log", 10),
    Check("parser", "Pemeriksaan sintaks AppArmor", 10),
)

@dataclass(frozen=True)
class Settings:
    """Application settings loaded from the container environment."""
    host: str
    port: int
    flag: str

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(os.getenv("HOST", DEFAULT_HOST), int(os.getenv("PORT", DEFAULT_PORT)), os.getenv("CTF_FLAG", "").strip())
