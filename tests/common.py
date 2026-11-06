"""Shared policy fixtures used only in backend tests."""
REFERENCE_PROFILE = """#include <tunables/global>

/usr/local/bin/file-manager {
    #include <abstractions/base>

    /etc/file-manager/** r,
    /tmp/file-manager/** rw,
    /home/** r,
    deny /var/log/** w,
}
"""

def with_tmp_permissions(permissions: str) -> str:
    """Return the test profile with one substituted temporary directory rule."""
    return REFERENCE_PROFILE.replace("/tmp/file-manager/** rw,", f"/tmp/file-manager/** {permissions},")
