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
            )
            self.assertEqual(context["files"], ["auth/service.py"])
            self.assertEqual(context["read_policy"]["allowed_files"], ["auth/service.py", "tests/test_auth_timeout.py"])
            self.assertTrue(context["read_policy"]["deny_unlisted"])
            self.assertEqual(context["write_policy"]["allowed_paths"], ["auth/service.py"])
            self.assertTrue(context["response_policy"]["forbid_background_recap"])
            self.assertEqual(context["codegraph"]["queries"], ["AuthService.login", "file:auth/service.py"])
            self.assertNotIn("repo_map", context)

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

    def test_write_context_is_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / ".iteration" / "context.json"
            context_compiler.write_context(
                output,
                context_compiler.compile_context(Path(temp_dir), "task", files=["a.py"], modify=["a.py"]),
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["task"], "task")
