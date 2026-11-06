"""Validation orchestration, public check results, and score calculation."""
from typing import Any
from app.config import CHECKS, Settings
from app.validation.parser import check_profile_syntax
from app.validation.semantic import check_semantics

FAILURE_HINTS = {
    "profile": "Periksa deklarasi profil, executable, dan mode profil.",
    "includes": "Periksa include global dan include dasar.",
    "config_read": "Aturan baca direktori konfigurasi belum sesuai.",
    "tmp_rw": "Aturan baca dan tulis direktori sementara belum sesuai.",
    "home_read": "Aturan baca direktori home belum sesuai.",
    "log_deny_write": "Aturan penolakan write direktori log belum sesuai.",
}


def validate_profile(source: str, settings: Settings) -> dict[str, Any]:
    """Return scored results and reveal the flag only after every check passes."""
    semantics = check_semantics(source)
    parser_passed, parser_error = check_profile_syntax(source)
    check_results = []
    score = 0
    for check in CHECKS:
        passed = parser_passed if check.check_id == "parser" else semantics[check.check_id]
        if passed:
            score += check.points
        result: dict[str, Any] = {"id": check.check_id, "label": check.label, "passed": passed}
        if not passed:
            if check.check_id == "parser" and parser_error:
                result["message"] = f"Kesalahan sintaks: {parser_error}"
            else:
                result["message"] = FAILURE_HINTS.get(check.check_id, "Pemeriksaan belum terpenuhi.")
        check_results.append(result)

    successful = score == 100 and parser_passed and all(semantics.values())
    response: dict[str, Any] = {
        "ok": successful,
        "score": score,
        "passed": sum(item["passed"] for item in check_results),
        "total": len(CHECKS),
        "checks": check_results,
    }
    if successful:
        if settings.flag:
            response["flag"] = settings.flag
        else:
            response["message"] = "Validasi berhasil, tetapi flag belum dikonfigurasi pada server."
    return response
