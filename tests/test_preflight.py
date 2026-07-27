import json
import tempfile
import unittest
from pathlib import Path

from scripts.preflight import detect


class PreflightTests(unittest.TestCase):
    def test_detects_node_quality_stack_without_mutating_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = {
                "scripts": {"test": "vitest", "test:e2e": "playwright test"},
                "devDependencies": {
                    "vitest": "1",
                    "@vitest/coverage-v8": "1",
                    "@playwright/test": "1",
                },
            }
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            (root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
            (root / ".codegraph").mkdir()

            result = detect(root, search_path="")

            self.assertEqual(result["project"]["node"]["package_manager"], "pnpm")
            self.assertTrue(result["quality"]["coverage_detected"])
            self.assertIn("node", result["required"]["native_verifiers"])
            self.assertEqual(sorted(p.name for p in root.iterdir()), [".codegraph", "package.json", "pnpm-lock.yaml"])

    def test_reports_required_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = detect(Path(directory), search_path="")

            self.assertIn("codegraph_cli_missing", result["blockers"])
            self.assertIn("codegraph_index_missing", result["blockers"])
            self.assertIn("project_verifier_not_detected", result["blockers"])


if __name__ == "__main__":
    unittest.main()
