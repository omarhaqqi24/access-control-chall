"""Behavioral checks for AppArmor rule matching."""
import unittest
from app.validation.semantic import check_semantics
from tests.common import REFERENCE_PROFILE, with_tmp_permissions

class SemanticValidationTests(unittest.TestCase):
    def test_reference_profile_passes(self) -> None:
        self.assertTrue(all(check_semantics(REFERENCE_PROFILE).values()))
    def test_rw_and_wr_have_same_exact_permissions(self) -> None:
        for permission in ("rw", "wr"):
            with self.subTest(permission=permission):
                self.assertTrue(check_semantics(with_tmp_permissions(permission))["tmp_rw"])
    def test_incorrect_temporary_permissions_fail(self) -> None:
        for permission in ("r", "w", "rwx", "ra", "rrw"):
            with self.subTest(permission=permission):
                self.assertFalse(check_semantics(with_tmp_permissions(permission))["tmp_rw"])
    def test_commented_rule_does_not_count(self) -> None:
        profile = REFERENCE_PROFILE.replace("/home/** r,", "# /home/** r,")
        self.assertFalse(check_semantics(profile)["home_read"])
    def test_rule_outside_target_profile_does_not_count(self) -> None:
        profile = REFERENCE_PROFILE.replace("/home/** r,", "}\n/home/** r,\n{")
        self.assertFalse(check_semantics(profile)["home_read"])
    def test_rule_in_another_profile_does_not_count(self) -> None:
        profile = REFERENCE_PROFILE.replace("/usr/local/bin/file-manager {", "/usr/bin/other {", 1)
        self.assertFalse(check_semantics(profile)["profile"])
        self.assertFalse(check_semantics(profile)["tmp_rw"])
    def test_complain_mode_fails(self) -> None:
        profile = REFERENCE_PROFILE.replace("/usr/local/bin/file-manager {", "/usr/local/bin/file-manager flags=(complain) {")
        self.assertFalse(check_semantics(profile)["profile"])

if __name__ == "__main__":
    unittest.main()
