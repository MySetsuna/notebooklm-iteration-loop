import json
import tempfile
import unittest
from pathlib import Path

from scripts import context_compiler


class ContextCompilerTests(unittest.TestCase):
    def test_compiles_only_explicit_allowlist_and_stable_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            context = context_compiler.compile_context(
                root,
                "fix auth timeout",
                symbols=["AuthService.login", "AuthService.login"],
                files=["auth/service.py"],
                tests=["tests/test_auth_timeout.py"],
                modify=["auth/service.py"],
                constraints=["OAuth contract unchanged"],
                failed_knowledge=["cache replacement regressed auth"],
                baseline_files={"existing.txt": "abc"},
            )
            self.assertEqual(context["files"], ["auth/service.py"])
            self.assertEqual(context["read_policy"]["allowed_files"], ["auth/service.py", "tests/test_auth_timeout.py"])
            self.assertTrue(context["read_policy"]["deny_unlisted"])
            self.assertEqual(context["write_policy"]["allowed_paths"], ["auth/service.py"])
            self.assertTrue(context["response_policy"]["forbid_background_recap"])
            self.assertEqual(context["codegraph"]["queries"], ["AuthService.login"])
            self.assertNotIn("repo_map", context)
            self.assertEqual(context["baseline"]["files"], {"existing.txt": "abc"})

    def test_rejects_path_escape_and_file_budget_overrun(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaises(ValueError):
                context_compiler.compile_context(root, "task", files=["../secret.txt"], modify=["a.py"])
            with self.assertRaises(ValueError):
                context_compiler.compile_context(
                    root,
                    "task",
                    files=["a.py", "b.py"],
                    modify=["a.py"],
                    budget={"max": {"files_read": 1}},
                )
            with self.assertRaises(ValueError):
                context_compiler.compile_context(root, "task", files=["a.py"])
            with self.assertRaises(ValueError):
                context_compiler.compile_context(
                    root,
                    "task",
                    symbols=["A", "B"],
                    modify=["a.py"],
                    budget={"max": {"codegraph_queries": 1}},
                )

    def test_write_context_is_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / ".iteration" / "context.json"
            context_compiler.write_context(
                output,
                context_compiler.compile_context(Path(temp_dir), "task", files=["a.py"], modify=["a.py"]),
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["task"], "task")

    def test_materializes_only_explicit_requirement_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            requirements = root / "docs" / "REQUIREMENTS-SPEC.md"
            requirements.parent.mkdir()
            requirements.write_text(
                "# Requirements\n\n"
                "## 待审批变更 (Pending Changes)\n\n_无_\n\n"
                "## 正式需求 (Active Requirements)\n\n"
                "### REQ-001 · One\n\n- 行为:first\n\n"
                "### REQ-002 · Two\n\n- 行为:second\n\n"
                "## 修订账本 (Revision Ledger)\n",
                encoding="utf-8",
            )
            context = context_compiler.compile_context(
                root,
                "inspect requirement",
                modify=["notes.md"],
                requirements=["REQ-002"],
            )
        self.assertEqual(context["requirements"]["ids"], ["REQ-002"])
        self.assertEqual(context["requirements"]["records"][0]["id"], "REQ-002")
        self.assertNotIn("REQ-001", context["requirements"]["records"][0]["markdown"])
        self.assertEqual(context["read_policy"]["allowed_files"], [])
