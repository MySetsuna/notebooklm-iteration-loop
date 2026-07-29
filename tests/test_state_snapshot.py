import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.state_snapshot import build_snapshot, decision_hash, validate_snapshot

STATE = """# State

## 当前迭代目标
x
## 已验证代码事实
x
## 相关模块与 symbol
x
## 最近完成与当前 diff
x
## 验证状态
x
## 当前失败信号与风险
x
## 架构边界
x
## 下一项已批准工作
x
"""
REQUIREMENTS = """# Requirements

- 需求版本:`v2`

## 正式需求 (Active Requirements)
## 修订账本 (Revision Ledger)
"""
PENDING = """# Pending

## 待审批变更 (Pending Changes)

_无_
"""


class StateSnapshotTests(unittest.TestCase):
    def _files(self, directory: str) -> tuple[Path, Path, Path]:
        root = Path(directory)
        state = root / "PROJECT-STATE.md"
        requirements = root / "REQUIREMENTS-SPEC.md"
        pending = root / "PENDING-REQUIREMENTS.md"
        state.write_text(STATE, encoding="utf-8")
        requirements.write_text(REQUIREMENTS, encoding="utf-8")
        pending.write_text(PENDING, encoding="utf-8")
        return state, requirements, pending

    @patch("scripts.state_snapshot.changed_paths", return_value=["a.py"])
    @patch("scripts.state_snapshot.repository_head", return_value="abc123")
    def test_builds_dynamic_metadata_only_at_tail(self, _head, _paths):
        with tempfile.TemporaryDirectory() as directory:
            state, requirements, pending = self._files(directory)
            snapshot = build_snapshot(
                Path(directory), state, requirements, pending, "2026-07-29T00:00:00+00:00"
            )
        self.assertTrue(snapshot.startswith(STATE.rstrip()))
        self.assertIn("repository_head:`abc123`", snapshot)
        self.assertIn("requirements_version:`v2`", snapshot)
        self.assertIn("pending_hash:`", snapshot)
        self.assertIn("current_git_diff:`a.py`", snapshot)
        self.assertTrue(snapshot.index("<!-- PROJECT_STATE_RUNTIME -->") > snapshot.index("## 架构边界"))

    @patch("scripts.state_snapshot.repository_head", return_value="abc123")
    def test_rejects_stale_head_or_requirements_hash(self, _head):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state, requirements, pending = self._files(directory)
            snapshot = root / "snapshot.md"
            with patch("scripts.state_snapshot.changed_paths", return_value=[]):
                snapshot.write_text(build_snapshot(root, state, requirements, pending), encoding="utf-8")
            with patch("scripts.state_snapshot.changed_paths", return_value=[]):
                self.assertTrue(validate_snapshot(root, snapshot, requirements, pending)["ok"])
            requirements.write_text(REQUIREMENTS + "\nchanged", encoding="utf-8")
            with patch("scripts.state_snapshot.changed_paths", return_value=[]):
                result = validate_snapshot(root, snapshot, requirements, pending)
        self.assertFalse(result["ok"])
        self.assertIn("requirements_hash", result["mismatches"])

    @patch("scripts.state_snapshot.repository_head", return_value="abc123")
    def test_rejects_stale_diff_or_pending_hash(self, _head):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state, requirements, pending = self._files(directory)
            snapshot = root / "snapshot.md"
            with patch("scripts.state_snapshot.changed_paths", return_value=["a.py"]):
                snapshot.write_text(build_snapshot(root, state, requirements, pending), encoding="utf-8")
            with patch("scripts.state_snapshot.changed_paths", return_value=["b.py"]):
                result = validate_snapshot(root, snapshot, requirements, pending)
            self.assertIn("current_git_diff", result["mismatches"])
            pending.write_text(PENDING + "\nchanged", encoding="utf-8")
            with patch("scripts.state_snapshot.changed_paths", return_value=["a.py"]):
                result = validate_snapshot(root, snapshot, requirements, pending)
            self.assertIn("pending_hash", result["mismatches"])

    def test_decision_hash_is_order_stable(self):
        self.assertEqual(decision_hash({"a": 1, "b": 2}), decision_hash({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
