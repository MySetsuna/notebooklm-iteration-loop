import os
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / "skills" / "refresh-notebooklm-auth" / "scripts" / "nlm_auth_flow.py"
SPEC = importlib.util.spec_from_file_location("nlm_auth_flow", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DEFAULT_PROXY_URL = MODULE.DEFAULT_PROXY_URL
chrome_args = MODULE.chrome_args
network_env = MODULE.network_env
resolve_proxy = MODULE.resolve_proxy


class NlmAuthFlowTests(unittest.TestCase):
    def test_fixed_proxy_is_default_and_explicit_override_wins(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_proxy(), DEFAULT_PROXY_URL)
        self.assertEqual(resolve_proxy("http://127.0.0.1:9999"), "http://127.0.0.1:9999")

    def test_process_env_sets_both_proxy_cases_and_local_bypass(self):
        env = network_env(DEFAULT_PROXY_URL)
        self.assertEqual(env["HTTP_PROXY"], DEFAULT_PROXY_URL)
        self.assertEqual(env["HTTPS_PROXY"], DEFAULT_PROXY_URL)
        self.assertEqual(env["http_proxy"], DEFAULT_PROXY_URL)
        self.assertEqual(env["NO_PROXY"], "127.0.0.1,localhost")

    def test_chrome_receives_proxy_and_dedicated_profile(self):
        args = chrome_args(DEFAULT_PROXY_URL, Path("C:/Temp/nlm"), 19222)
        self.assertIn("--proxy-server=http://127.0.0.1:51081", args)
        self.assertIn("--remote-debugging-port=19222", args)
        self.assertIn("https://notebook.google.com/", args)

    def test_nlm_output_decoding_is_explicit_utf8(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('encoding="utf-8"', source)
        self.assertIn('errors="replace"', source)

    def test_verify_does_not_return_raw_auth_or_notebook_output(self):
        with patch.object(MODULE, "run_nlm", side_effect=[
            (0, "Authentication valid! Account: secret@example.com"),
            (0, json.dumps([{"id": "secret-id", "title": "private"}])),
        ]):
            result = MODULE.verify(DEFAULT_PROXY_URL, 1)
        self.assertEqual(result["notebook_count"], 1)
        self.assertNotIn("secret@example.com", json.dumps(result))
        self.assertNotIn("secret-id", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
