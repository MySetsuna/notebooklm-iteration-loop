import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from scripts.iteration_budget import DEFAULT_BUDGET
from scripts.iteration_gate import _changed_paths, check_gate


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
    def test_changed_paths_include_untracked_files(self):
        with patch(
            "scripts.iteration_gate.subprocess.run",
            side_effect=[
                CompletedProcess(["git", "diff"], 0, "tracked.py\n", ""),
                CompletedProcess(["git", "ls-files"], 0, "new.py\n", ""),
            ],
        ):
            self.assertEqual(_changed_paths(Path(".")), {"tracked.py", "new.py"})

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

    def test_accepts_requirement_id_as_explicit_entry(self):
        value = context(
            symbols=[],
            files=[],
            tests=[],
            requirements={"ids": ["REQ-001"], "records": [{"id": "REQ-001"}]},
        )
        result = check_gate(Path("."), value, DEFAULT_BUDGET, {}, [])
        self.assertTrue(result["ok"])

    def test_rejects_planned_codegraph_queries_over_budget(self):
        value = context(
            codegraph={"mode": "targeted", "full_rebuild": False, "queries": ["A", "B"]},
            budget={"max": {"codegraph_queries": 1}},
        )
        result = check_gate(Path("."), value, DEFAULT_BUDGET, {}, [])
        self.assertFalse(result["ok"])
        self.assertIn("codegraph_scope_exceeded", result["violations"])

    def test_rejects_materialized_requirements_outside_explicit_ids(self):
        value = context(
            requirements={"ids": ["REQ-001"], "records": [{"id": "REQ-002"}]},
        )
        result = check_gate(Path("."), value, DEFAULT_BUDGET, {}, [])
        self.assertFalse(result["ok"])
        self.assertIn("requirement_scope_invalid", result["violations"])
