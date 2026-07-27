import tempfile
import unittest
from pathlib import Path

from scripts.requirements_gate import inspect_document


BASE = """# Requirements

## 待审批变更 (Pending Changes)
{pending}

## 正式需求 (Active Requirements)

### REQ-001

## 修订账本 (Revision Ledger)
"""


class RequirementsGateTests(unittest.TestCase):
    def _inspect(self, pending: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "REQUIREMENTS-SPEC.md"
            path.write_text(BASE.format(pending=pending), encoding="utf-8")
            return inspect_document(path)

    def test_empty_pending_queue_is_executable(self) -> None:
        result = self._inspect("_无_")
        self.assertTrue(result["executable"])
        self.assertEqual(result["pending_ids"], [])

    def test_pending_requirement_blocks_execution(self) -> None:
        result = self._inspect("### PENDING-REQ-20260727-01\n\n- Goal: change behavior")
        self.assertFalse(result["executable"])
        self.assertEqual(result["pending_ids"], ["PENDING-REQ-20260727-01"])

    def test_unstructured_pending_content_also_blocks(self) -> None:
        result = self._inspect("Need to change payment behavior.")
        self.assertFalse(result["executable"])
        self.assertEqual(result["pending_ids"], ["unstructured-pending-content"])


if __name__ == "__main__":
    unittest.main()
