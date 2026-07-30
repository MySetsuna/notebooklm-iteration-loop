import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scripts.requirements_gate import main as gate_main
from scripts.requirements_intake import build_manifest, inspect_manifest

ACTIVE = """# Requirements

## 正式需求 (Active Requirements)

### REQ-001 · Existing

- 状态:`ACTIVE`
- 版本:`v1`
- 行为:existing behavior
- 边界:none
- 验收:test
- 追踪:test

## 修订账本 (Revision Ledger)
"""
PENDING_RECORD = """### PENDING-REQ-2 · New behavior

- 类型:`NEW`
- 原始意图:add behavior
- 关联 Active 条款:`无`
- 目标行为:new behavior
- 范围:workflow
- 非目标:product code
- 不可动边界:no implementation before approval
- 假设/待确认:scope
- 确定性验收:test
- 预期追踪:REQ → script → test"""
EMPTY_PENDING = """# Pending

## 待审批变更 (Pending Changes)

_无_
"""


def decision(classification: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "intake_id": "INTAKE-TEST-1",
        "classification": classification,
        "summary": "test request",
        "requirement_ids": [],
        "pending_ids": [],
        "approval_reasons": [],
        "open_questions": [],
        "approval_evidence": "",
    }


class RequirementsIntakeTests(unittest.TestCase):
    def _files(self, directory: str, pending: str = "_无_"):
        root = Path(directory)
        active = root / "REQUIREMENTS-SPEC.md"
        pending_path = root / "PENDING-REQUIREMENTS.md"
        request = root / "request.txt"
        active.write_text(ACTIVE, encoding="utf-8")
        pending_path.write_text(
            EMPTY_PENDING if pending == "_无_" else EMPTY_PENDING.replace("_无_", pending),
            encoding="utf-8",
        )
        request.write_text("user request", encoding="utf-8")
        return active, pending_path, request

    def test_active_intake_binds_request_and_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            active, pending, request = self._files(directory)
            current = decision("active")
            current["requirement_ids"] = ["REQ-001"]
            manifest = build_manifest(active, pending, request, current)
            intake = Path(directory) / "intake.json"
            intake.write_text(json.dumps(manifest), encoding="utf-8")

            self.assertTrue(inspect_manifest(active, pending, request, intake)["executable"])
            with redirect_stdout(io.StringIO()):
                exit_code = gate_main(
                    [
                        "assert-task-executable",
                        "--file",
                        str(active),
                        "--pending-file",
                        str(pending),
                        "--request-file",
                        str(request),
                        "--intake-file",
                        str(intake),
                    ]
                )
            self.assertEqual(exit_code, 0)
            request.write_text("different request", encoding="utf-8")
            self.assertIn(
                "request_sha256_mismatch",
                inspect_manifest(active, pending, request, intake)["reasons"],
            )

    def test_pending_draft_is_bound_and_never_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            active, pending, request = self._files(directory, PENDING_RECORD)
            current = decision("pending")
            current["pending_ids"] = ["PENDING-REQ-2"]
            current["approval_reasons"] = ["new_requirement", "ambiguous_scope"]
            current["open_questions"] = ["confirm scope"]
            manifest = build_manifest(active, pending, request, current)

            self.assertFalse(manifest["executable"])
            self.assertIn("approval_required", manifest["reasons"])
            self.assertEqual(len(manifest["draft_sha256"]), 64)

    def test_approved_change_requires_previous_bound_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            active, pending, request = self._files(directory, PENDING_RECORD)
            draft_decision = decision("pending")
            draft_decision["pending_ids"] = ["PENDING-REQ-2"]
            draft_decision["approval_reasons"] = ["new_requirement"]
            draft = build_manifest(active, pending, request, draft_decision)
            previous = Path(directory) / "pending-intake.json"
            previous.write_text(json.dumps(draft), encoding="utf-8")

            active.write_text(
                ACTIVE.replace(
                    "## 修订账本",
                    """### REQ-002 · New

- 批准依据:`user approved displayed PENDING-REQ-2`
- 状态:`ACTIVE`
- 版本:`v1`
- 行为:new behavior
- 边界:none
- 验收:test
- 追踪:test

## 修订账本""",
                ),
                encoding="utf-8",
            )
            pending.write_text(EMPTY_PENDING, encoding="utf-8")
            request.write_text("批准 PENDING-REQ-2，开始修复", encoding="utf-8")
            approved = decision("approved")
            approved["requirement_ids"] = ["REQ-002"]
            approved["pending_ids"] = ["PENDING-REQ-2"]
            approved["approval_evidence"] = "批准 PENDING-REQ-2，开始修复"

            manifest = build_manifest(active, pending, request, approved, previous)
            self.assertTrue(manifest["executable"])
            self.assertEqual(manifest["draft_sha256"], draft["draft_sha256"])
            self.assertEqual(len(manifest["previous_intake_sha256"]), 64)

            approved["approval_evidence"] = ""
            rejected = build_manifest(active, pending, request, approved, previous)
            self.assertIn("approval_evidence_required", rejected["reasons"])

    def test_task_gate_requires_intake_files(self):
        with tempfile.TemporaryDirectory() as directory:
            active, pending, _ = self._files(directory)
            with redirect_stderr(io.StringIO()):
                exit_code = gate_main(
                    [
                        "assert-task-executable",
                        "--file",
                        str(active),
                        "--pending-file",
                        str(pending),
                    ]
                )
            self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
