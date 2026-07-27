import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_reports_machine_global_quality_commands(self) -> None:
        available = {"sonar-scanner", "coverage", "playwright"}
        with tempfile.TemporaryDirectory() as directory:
            global_bin = Path(directory).parent / "global-bin"
            with patch(
                "scripts.preflight.shutil.which",
                side_effect=lambda command, path=None: str(global_bin / command)
                if command in available
                else None,
            ):
                result = detect(Path(directory), search_path="")

        self.assertEqual(result["quality"]["global_commands"]["sonar"], ["sonar-scanner"])
        self.assertEqual(result["quality"]["global_commands"]["coverage"], ["coverage"])
        self.assertEqual(result["quality"]["global_commands"]["e2e"], ["playwright"])

    def test_ignores_project_local_quality_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "scripts.preflight.shutil.which",
            side_effect=lambda command, path=None: str(Path(directory) / ".venv" / command),
        ):
            result = detect(Path(directory), search_path="")

        self.assertEqual(result["quality"]["global_commands"]["sonar"], [])
        self.assertEqual(result["quality"]["global_commands"]["coverage"], [])
        self.assertEqual(result["quality"]["global_commands"]["e2e"], [])


if __name__ == "__main__":
    unittest.main()
