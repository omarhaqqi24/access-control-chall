"""HTTP API behavior tests using the participant-facing validation service."""
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from app.config import Settings
from app.http_server import create_server
from app.rate_limiter import RateLimiter
from tests.common import REFERENCE_PROFILE, with_tmp_permissions

class ValidationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["CTF_FLAG"] = "UAP26{test_only}"
        cls.server = create_server(Settings("127.0.0.1", 0, os.environ["CTF_FLAG"]))
        cls.server.RequestHandlerClass.RATE_LIMITER = RateLimiter(limit=100, window_seconds=60)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/api/challenges/secure-file-manager/validate"
    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        os.environ.pop("CTF_FLAG", None)
    def submit(self, profile: str) -> tuple[int, dict]:
        request = urllib.request.Request(self.url, data=json.dumps({"profile": profile}).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())
    def test_rw_profile_scores_100_and_returns_flag(self) -> None:
        status, result = self.submit(with_tmp_permissions("rw"))
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["flag"], "UAP26{test_only}")
    def test_wr_profile_scores_100_and_returns_flag(self) -> None:
        status, result = self.submit(with_tmp_permissions("wr"))
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["flag"], "UAP26{test_only}")
    def test_bad_temporary_permissions_fail_without_flag(self) -> None:
        for permission in ("r", "w", "rwx", "ra", "rrw"):
            with self.subTest(permission=permission):
                status, result = self.submit(with_tmp_permissions(permission))
                self.assertEqual(status, 200)
                self.assertFalse(result["ok"])
                self.assertLess(result["score"], 100)
                self.assertNotIn("flag", result)
    def test_empty_input_is_rejected(self) -> None:
        self.assertEqual(self.submit("")[0], 400)
    def test_oversized_input_is_rejected(self) -> None:
        self.assertEqual(self.submit("x" * 21_000)[0], 413)
    def test_missing_rule_does_not_return_flag(self) -> None:
        status, result = self.submit(REFERENCE_PROFILE.replace("/home/** r,", ""))
        self.assertEqual(status, 200)
        self.assertFalse(result["ok"])
        self.assertNotIn("flag", result)

if __name__ == "__main__":
    unittest.main()
