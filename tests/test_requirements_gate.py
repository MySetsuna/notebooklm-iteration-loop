import tempfile
import unittest
from pathlib import Path

from scripts.requirements_gate import inspect_documents

ACTIVE = """# Requirements

## 正式需求 (Active Requirements)

### REQ-001 · One

- 状态:`ACTIVE`
- 版本:`v1`
- 行为:one
- 边界:none
- 验收:test
- 追踪:test

## 修订账本 (Revision Ledger)
"""
PENDING = """# Pending

## 待审批变更 (Pending Changes)

{pending}
"""


class RequirementsGateTests(unittest.TestCase):
    def _inspect(self, pending: str, active: str = ACTIVE) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active_path = root / "REQUIREMENTS-SPEC.md"
            pending_path = root / "PENDING-REQUIREMENTS.md"
            active_path.write_text(active, encoding="utf-8")
            pending_path.write_text(PENDING.format(pending=pending), encoding="utf-8")
            return inspect_documents(active_path, pending_path)

    def test_empty_pending_queue_is_executable(self):
        result = self._inspect("_无_")
        self.assertTrue(result["executable"])
        self.assertEqual(result["pending_ids"], [])

    def test_pending_requirement_blocks_execution(self):
        result = self._inspect("### PENDING-REQ-1 · Change\n\n- 类型:`FIX`")
        self.assertFalse(result["executable"])
        self.assertEqual(result["pending_ids"], ["PENDING-REQ-1"])
        self.assertIsNotNone(result["record_error"])

    def test_active_source_rejects_pending_content(self):
        active = ACTIVE.replace("## 正式需求", "## 待审批变更 (Pending Changes)\n\n_无_\n\n## 正式需求")
        result = self._inspect("_无_", active)
        self.assertFalse(result["executable"])
        self.assertTrue(result["active_contains_pending"])

    def test_unstructured_pending_content_blocks(self):
        result = self._inspect("Need to change behavior.")
        self.assertFalse(result["valid_structure"])
        self.assertEqual(result["pending_ids"], ["unstructured-pending-content"])


if __name__ == "__main__":
    unittest.main()
