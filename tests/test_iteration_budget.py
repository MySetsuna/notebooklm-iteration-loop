import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.iteration_budget import DEFAULT_BUDGET, check_budget, validate_budget


class IterationBudgetTests(unittest.TestCase):
    def test_default_budget_valid_and_missing_usage_is_zero(self):
        validate_budget(DEFAULT_BUDGET)
        result = check_budget(DEFAULT_BUDGET, {})
        self.assertTrue(result["ok"])
        self.assertEqual(result["usage"]["token"], 0)

    def test_reports_each_exceeded_metric(self):
        result = check_budget(
            DEFAULT_BUDGET,
            {"exploration_calls": 6, "codegraph_queries": 11, "files_read": 31, "retries": 4, "token": 80001},
        )
        self.assertFalse(result["ok"])
        self.assertEqual({item["metric"] for item in result["exceeded"]}, {"exploration_calls", "codegraph_queries", "files_read", "retries", "token"})

    def test_rejects_negative_or_missing_limit(self):
        with self.assertRaises(ValueError):
            validate_budget({"schema_version": 1, "max": {"token": -1}})

    def test_cli_returns_two_when_budget_is_exceeded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            budget = root / "budget.json"
            usage = root / "usage.json"
            budget.write_text(json.dumps(DEFAULT_BUDGET), encoding="utf-8")
            usage.write_text(json.dumps({"token": 80001}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parents[1] / "scripts" / "iteration_budget.py"),
                 "check", "--budget", str(budget), "--usage", str(usage)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)["ok"])
