"""Challenge-specific checks for a submitted AppArmor profile."""
import re
from typing import NamedTuple

EXECUTABLE = "/usr/local/bin/file-manager"

class ProfileBlock(NamedTuple):
    body: str | None
    closed: bool
    flags: str


def strip_comments(source: str) -> str:
    """Remove ordinary comments but preserve AppArmor include directives."""
    lines = []
    for line in source.splitlines():
        if re.match(r"^\s*#\s*include\b", line):
            lines.append(line)
        else:
            lines.append(re.sub(r"#.*$", "", line))
    return "\n".join(lines)


def find_target_profile(source: str) -> ProfileBlock:
    """Extract the requested profile body, flags, and closing-brace status."""
    clean_source = strip_comments(source)
    declaration = re.search(
        rf"(?m)^\s*{re.escape(EXECUTABLE)}\s*"
        r"(?:flags\s*=\s*\(([^)]*)\)\s*)?\{",
        clean_source,
    )
    if declaration is None:
        return ProfileBlock(None, False, "")

    opening = clean_source.find("{", declaration.start(), declaration.end())
    depth = 0
    for position in range(opening, len(clean_source)):
        if clean_source[position] == "{":
            depth += 1
        elif clean_source[position] == "}":
            depth -= 1
            if depth == 0:
                return ProfileBlock(clean_source[opening + 1:position], True, declaration.group(1) or "")
    return ProfileBlock(clean_source[opening + 1:], False, declaration.group(1) or "")


def has_rule(body: str, path: str, expected: set[str], *, deny: bool = False) -> bool:
    """Match an exact path with precisely the requested permission characters."""
    deny_prefix = r"deny\s+" if deny else ""
    expression = rf"(?m)^\s*{deny_prefix}{re.escape(path)}\s+([a-z]+)\s*,\s*$"
    for match in re.finditer(expression, body):
        actual = match.group(1)
        if len(actual) == len(expected) and set(actual) == expected:
            return True
    return False


def has_conflicting_rule(body: str, path: str, expected: set[str]) -> bool:
    """Reject an exact-path allow/deny rule that conflicts with the required rule."""
    expression = rf"(?m)^\s*(deny\s+)?{re.escape(path)}\s+([a-z]+)\s*,\s*$"
    for match in re.finditer(expression, body):
        permissions = match.group(2)
        if match.group(1) or len(permissions) != len(expected) or set(permissions) != expected:
            return True
    return False


def check_semantics(source: str) -> dict[str, bool]:
    """Evaluate profile structure, includes, and the six required semantic rules."""
    clean_source = strip_comments(source)
    profile = find_target_profile(source)
    flags = {item.strip().lower() for item in profile.flags.split(",") if item.strip()}
    body = profile.body or ""
    checks = {
        "profile": profile.body is not None and profile.closed and not flags.intersection(
            {"complain", "unconfined", "default_allow"}
        ),
        "includes": (
            re.search(r"(?m)^\s*#include\s*<tunables/global>\s*$", clean_source) is not None
            and re.search(r"(?m)^\s*#include\s*<abstractions/base>\s*$", body) is not None
        ),
        "config_read": has_rule(body, "/etc/file-manager/**", {"r"}),
        "tmp_rw": has_rule(body, "/tmp/file-manager/**", {"r", "w"}),
        "home_read": has_rule(body, "/home/**", {"r"}),
        "log_deny_write": has_rule(body, "/var/log/**", {"w"}, deny=True),
    }
    required = (
        ("/etc/file-manager/**", {"r"}, "config_read"),
        ("/tmp/file-manager/**", {"r", "w"}, "tmp_rw"),
        ("/home/**", {"r"}, "home_read"),
    )
    for path, permissions, check_id in required:
        if has_conflicting_rule(body, path, permissions):
            checks[check_id] = False
    if re.search(r"(?m)^\s*/var/log/\*\*\s+(?:w|rw),\s*$", body):
        checks["log_deny_write"] = False
    return checks
