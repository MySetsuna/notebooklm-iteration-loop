import tempfile
import unittest
from pathlib import Path

from scripts.requirements_store import apply_operation, pending_index, select_records

ACTIVE = """# Requirements

## 正式需求 (Active Requirements)

### REQ-001 · One

- 状态:`ACTIVE`
- 版本:`v1`
- 行为:first
- 边界:none
- 验收:test
- 追踪:test

### REQ-002 · Two

- 状态:`ACTIVE`
- 版本:`v1`
- 行为:second
- 边界:none
- 验收:test
- 追踪:test

## 修订账本 (Revision Ledger)
"""
PENDING = """# Pending

## 待审批变更 (Pending Changes)

_无_
"""
PENDING_MARKDOWN = """### PENDING-REQ-1 · Change

- 类型:`MODIFY`
- 原始意图:change
- 关联 Active 条款:`REQ-001`
- 目标行为:changed
- 范围:requirements
- 非目标:code
- 不可动边界:auth contract
- 假设/待确认:none
- 确定性验收:test
- 预期追踪:req → script → test"""


class RequirementsStoreTests(unittest.TestCase):
    def _paths(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory)
        active = root / "REQUIREMENTS-SPEC.md"
        pending = root / "PENDING-REQUIREMENTS.md"
        active.write_text(ACTIVE, encoding="utf-8")
        pending.write_text(PENDING, encoding="utf-8")
        return active, pending

    def test_selects_only_explicit_active_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            active, _ = self._paths(directory)
            selected = select_records(active, ["REQ-002"])
        self.assertEqual([record["id"] for record in selected], ["REQ-002"])
        self.assertNotIn("REQ-001", selected[0]["markdown"])

    def test_selection_rejects_pending_id_and_byte_overrun(self):
        with tempfile.TemporaryDirectory() as directory:
            active, _ = self._paths(directory)
            with self.assertRaises(ValueError):
                select_records(active, ["PENDING-REQ-1"])
            with self.assertRaises(ValueError):
                select_records(active, ["REQ-001"], max_bytes=1)

    def test_pending_write_never_touches_approved_source(self):
        operation = {
            "schema_version": 1,
            "upsert": [{"id": "PENDING-REQ-1", "section": "pending", "markdown": PENDING_MARKDOWN}],
            "remove": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            active, pending = self._paths(directory)
            before = active.read_text(encoding="utf-8")
            apply_operation(active, pending, operation)
            self.assertEqual(active.read_text(encoding="utf-8"), before)
            self.assertIn("PENDING-REQ-1", pending.read_text(encoding="utf-8"))
            self.assertEqual(pending_index(pending)[0]["frozen_scope"], "auth contract")

    def test_commented_pending_example_is_not_a_record(self):
        with tempfile.TemporaryDirectory() as directory:
            _, pending = self._paths(directory)
            pending.write_text(
                PENDING + "\n<!--\n### PENDING-REQ-EXAMPLE · Example\n-->\n",
                encoding="utf-8",
            )
            self.assertEqual(pending_index(pending), [])

    def test_active_write_and_pending_removal_require_evidence(self):
        active_markdown = """### REQ-003 · Three

- 状态:`ACTIVE`
- 版本:`v1`
- 行为:third
- 边界:none
- 验收:test
- 追踪:test"""
        operation = {
            "schema_version": 1,
            "upsert": [{"id": "REQ-003", "section": "active", "markdown": active_markdown}],
            "remove": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            active, pending = self._paths(directory)
            with self.assertRaises(ValueError):
                apply_operation(active, pending, operation)
            apply_operation(active, pending, operation, "user approved")
            self.assertIn("Approval evidence:`user approved`", active.read_text(encoding="utf-8"))

    def test_rejects_missing_empty_and_placeholder_fields(self):
        cases = [
            "### PENDING-REQ-1 · Bad\n\n- 类型:`FIX`",
            PENDING_MARKDOWN.replace("- 原始意图:change", "- 原始意图:"),
            PENDING_MARKDOWN.replace("- 原始意图:change", "- 原始意图:`<待填写>`"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            active, pending = self._paths(directory)
            for markdown in cases:
                operation = {
                    "schema_version": 1,
                    "upsert": [{"id": "PENDING-REQ-1", "section": "pending", "markdown": markdown}],
                    "remove": [],
                }
                with self.assertRaises(ValueError):
                    apply_operation(active, pending, operation)
