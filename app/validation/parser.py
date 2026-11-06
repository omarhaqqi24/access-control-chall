"""Safe, non-loading syntax checks using the official AppArmor parser."""
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
from app.config import PARSER_TIMEOUT_SECONDS, TEMP_DIRECTORY

class ParserUnavailableError(RuntimeError):
    """The parser is missing or could not be started."""


def check_profile_syntax(source: str) -> tuple[bool, str | None]:
    """Run parser check mode with a private temporary file; never load policy."""
    parser = shutil.which("apparmor_parser")
    if parser is None:
        raise ParserUnavailableError("Parser AppArmor tidak tersedia.")
    try:
        with tempfile.TemporaryDirectory(prefix="uap-aa-", dir=TEMP_DIRECTORY) as directory:
            os.chmod(directory, 0o700)
            path = Path(directory) / f"{secrets.token_hex(12)}.profile"
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(source)
            result = subprocess.run(
                [parser, "-Q", "-K", "--abort-on-error", str(path)],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                timeout=PARSER_TIMEOUT_SECONDS, check=False, shell=False,
                env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
            )
    except subprocess.TimeoutExpired:
        return False, "Parser melewati batas waktu pemeriksaan."
    except OSError as error:
        raise ParserUnavailableError("Parser AppArmor tidak dapat dijalankan.") from error
    if result.returncode == 0:
        return True, None
    message = (result.stderr or result.stdout or "Parser AppArmor menolak konfigurasi.").strip()
    message = re.sub(r"/tmp/uap-aa-[^/:\s]+/[^:\s]+", "profil sementara", message)
    return False, message[:400]
