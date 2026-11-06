"""Integration tests against the AppArmor parser installed in the image."""
import unittest
from app.validation.parser import check_profile_syntax
from tests.common import REFERENCE_PROFILE, with_tmp_permissions

class AppArmorParserTests(unittest.TestCase):
    def test_reference_profile_parses(self) -> None:
        passed, diagnostic = check_profile_syntax(REFERENCE_PROFILE)
        self.assertTrue(passed, diagnostic)
    def test_rw_profile_parses(self) -> None:
        passed, diagnostic = check_profile_syntax(with_tmp_permissions("rw"))
        self.assertTrue(passed, diagnostic)
    def test_wr_profile_parses(self) -> None:
        passed, diagnostic = check_profile_syntax(with_tmp_permissions("wr"))
        self.assertTrue(passed, diagnostic)
    def test_invalid_syntax_is_rejected(self) -> None:
        malformed = REFERENCE_PROFILE.replace("deny /var/log/** w,", "deny /var/log/** w")
        passed, diagnostic = check_profile_syntax(malformed)
        self.assertFalse(passed)
        self.assertTrue(diagnostic)

if __name__ == "__main__":
    unittest.main()
