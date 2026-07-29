import unittest
from pathlib import Path

from scripts.iteration_budget import DEFAULT_BUDGET
from scripts.iteration_gate import check_gate


def context(**overrides):
    value = {
        "schema_version": 1,
        "task": "fix auth timeout",
        "symbols": ["AuthService.login"],
        "files": ["auth/service.py"],
        "tests": ["tests/test_auth_timeout.py"],
        "read_policy": {"allowed_files": ["auth/service.py", "tests/test_auth_timeout.py"], "deny_unlisted": True},
        "write_policy": {"allowed_paths": ["auth/service.py"], "deny_unlisted": True},
        "codegraph": {"mode": "targeted", "full_rebuild": False},
        "response_policy": {"format": "delta_evidence_next", "forbid_background_recap": True},
    }
    value.update(overrides)
    return value


class IterationGateTests(unittest.TestCase):
    def test_allows_only_scoped_changes(self):
        result = check_gate(Path("."), context(), DEFAULT_BUDGET, {}, ["auth/service.py"])
        self.assertTrue(result["ok"])

    def test_rejects_full_scan_unscoped_write_and_budget(self):
        value = context(codegraph={"mode": "full", "full_rebuild": True})
        result = check_gate(Path("."), value, DEFAULT_BUDGET, {"token": 80001}, ["auth/service.py", "other.py"])
        self.assertFalse(result["ok"])
        self.assertEqual(
            set(result["violations"]),
            {"full_scan_forbidden", "iteration_budget_exceeded", "write_scope_exceeded"},
        )

    def test_rejects_missing_explicit_entry_and_background_recap(self):
        value = context(symbols=[], files=[], tests=[], response_policy={})
        result = check_gate(Path("."), value, DEFAULT_BUDGET, {}, [])
        self.assertFalse(result["ok"])
        self.assertIn("explicit_entry_missing", result["violations"])
        self.assertIn("background_recap_forbidden", result["violations"])
