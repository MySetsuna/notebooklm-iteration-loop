import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.agent_dispatch import (
    build_plan,
    finalize_result,
    stable_hash,
    validate_batch,
    validate_plan,
    validate_result,
)

REQUIREMENTS = """# Requirements

- 需求版本:`v1`

## 正式需求 (Active Requirements)

### REQ-009 · Dispatch

- 批准依据:`user approved`
- 状态:`ACTIVE`
- 版本:`v1.0.0`
- 行为:bounded dispatch
- 后端:`auto`
- 边界:no scope expansion
- 验收:deterministic gate
- 追踪:`scripts/agent_dispatch.py`

## 修订账本 (Revision Ledger)
"""
PENDING = """# Pending

## 待审批变更 (Pending Changes)

_无_
"""


def task(task_id: str, *, write: bool = False, path: str | None = None) -> dict:
    target = path or f"src/{task_id}.py"
    return {
        "id": task_id,
        "result_path": f".iteration/agents/result-{task_id}.json",
        "objective": f"complete {task_id}",
        "execution_kind": "write" if write else "read",
        "isolation": "worktree" if write else "shared",
        "requirements": ["REQ-009"],
        "symbols": [task_id],
        "codegraph": {
            "queries": [task_id],
            "facts": [{"fact": f"{task_id} fact", "evidence": f"codegraph:{task_id}"}],
        },
        "files": [target],
        "tests": [f"tests/test_{task_id}.py"],
        "write_paths": [target] if write else [],
        "exclusive_resources": [],
        "constraints": ["stay scoped"],
        "verification": [{"command": f"test {task_id}", "expected_exit": 0}],
        "depends_on": [],
    }


class AgentDispatchTests(unittest.TestCase):
    def _files(self, directory: str) -> tuple[Path, Path, Path]:
        root = Path(directory)
        requirements = root / "requirements.md"
        pending = root / "pending.md"
        requirements.write_text(REQUIREMENTS, encoding="utf-8")
        pending.write_text(PENDING, encoding="utf-8")
        return root, requirements, pending

    def _plan(self, root, requirements, pending, tasks, **dispatch):
        return build_plan(
            root,
            {
                "schema_version": 1,
                "dispatch": {"max_workers": 4, **dispatch},
                "tasks": tasks,
            },
            requirements,
            pending,
            current_head="abc123",
            worktree_digest="dirty-hash",
        )

    def _result(self, root: Path, packet: dict, *, changed_paths=None) -> dict:
        evidence_path = root / ".iteration" / f"{packet['task_id']}.log"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("verified\n", encoding="utf-8")
        value = {
            "schema_version": 1,
            "dispatch_id": packet["dispatch_id"],
            "task_id": packet["task_id"],
            "baseline": packet["baseline"],
            "packet_hash": packet["packet_hash"],
            "status": "completed",
            "summary": "done",
            "changed_paths": changed_paths or [],
            "verification": [
                {
                    "command": item["command"],
                    "exit_code": item["expected_exit"],
                    "evidence": {
                        "path": evidence_path.relative_to(root).as_posix(),
                        "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                    },
                }
                for item in packet["verification"]
            ],
            "token_usage": {
                "input": 10,
                "cache_read": 2,
                "cache_write": 1,
                "output": 3,
                "total": 14,
            },
            "transport_receipt": {
                "backend": "ridge",
                "submit_dispatched": True,
                "terminal_accepted": True,
                "agent_acknowledged": True,
            },
        }
        value["result_hash"] = stable_hash(value)
        return value

    def test_read_only_tasks_fan_out_with_bounded_stable_packets(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            manifest_tasks = [task("a"), task("b")]
            first = self._plan(root, requirements, pending, manifest_tasks)
            second = self._plan(root, requirements, pending, manifest_tasks)
        self.assertEqual(first["execution_mode"], "parallel")
        self.assertEqual(first["plan_hash"], second["plan_hash"])
        self.assertEqual(first["waves"], [["a", "b"]])
        self.assertTrue(all(packet["packet_bytes"] <= 16384 for packet in first["packets"]))

    def test_shared_write_tasks_degrade_to_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            left, right = task("a", write=True), task("b", write=True)
            left["isolation"] = right["isolation"] = "shared"
            plan = self._plan(root, requirements, pending, [left, right])
        self.assertEqual(plan["execution_mode"], "bounded_single")
        self.assertEqual(plan["waves"], [["a"], ["b"]])
        self.assertTrue(any("write_isolation" in item for item in plan["parallel_rejections"]))

    def test_overlapping_worktree_writes_degrade_to_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(
                root,
                requirements,
                pending,
                [task("a", write=True, path="src/x.py"), task("b", write=True, path="src/x.py")],
            )
        self.assertEqual(plan["waves"], [["a"], ["b"]])
        self.assertTrue(any("write_scope" in item for item in plan["parallel_rejections"]))

    def test_dependency_and_serial_backend_never_fan_out(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            first, second = task("a"), task("b")
            second["depends_on"] = ["a"]
            plan = self._plan(root, requirements, pending, [first, second], backend="serial")
        self.assertEqual(plan["execution_mode"], "bounded_single")
        self.assertEqual(plan["waves"], [["a"], ["b"]])

    def test_orchestration_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a")], enabled=False)
        self.assertFalse(plan["orchestration_enabled"])
        self.assertEqual(plan["execution_mode"], "disabled")
        self.assertEqual(plan["packets"], [])

    def test_exclusive_resource_conflict_degrades_to_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            left, right = task("a"), task("b")
            left["exclusive_resources"] = right["exclusive_resources"] = ["port:8000"]
            plan = self._plan(root, requirements, pending, [left, right])
        self.assertEqual(plan["waves"], [["a"], ["b"]])
        self.assertTrue(
            any("exclusive_resource" in item for item in plan["parallel_rejections"])
        )

    def test_control_result_path_collision_degrades_to_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            left, right = task("a"), task("b")
            left["result_path"] = right["result_path"] = ".iteration/agents/shared.json"
            plan = self._plan(root, requirements, pending, [left, right])
        self.assertEqual(plan["waves"], [["a"], ["b"]])
        self.assertTrue(any("control_write" in item for item in plan["parallel_rejections"]))

    def test_rejects_pending_unknown_requirement_and_stale_head(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            pending.write_text(
                PENDING.replace(
                    "_无_",
                    "### PENDING-REQ-1 · wait\n\n- 状态:`PENDING`\n- 主题:wait\n- 冻结范围:src\n- 禁止行为:write\n",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "pending requirements"):
                self._plan(root, requirements, pending, [task("a")])
            pending.write_text(PENDING, encoding="utf-8")
            unknown = task("a")
            unknown["requirements"] = ["REQ-404"]
            with self.assertRaisesRegex(ValueError, "not found"):
                self._plan(root, requirements, pending, [unknown])
            with self.assertRaisesRegex(ValueError, "base_head is stale"):
                build_plan(
                    root,
                    {
                        "schema_version": 1,
                        "base_head": "old",
                        "tasks": [task("a")],
                    },
                    requirements,
                    pending,
                    current_head="new",
                    worktree_digest="digest",
                )

    def test_validates_completed_result_and_exact_write_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a", write=True)])
            packet = plan["packets"][0]
            result = self._result(root, packet, changed_paths=["src/a.py"])
            valid = validate_result(
                root,
                plan,
                result,
                current_head="abc123",
                current_worktree_digest="dirty-hash",
            )
            result["changed_paths"] = ["src"]
            result["result_hash"] = stable_hash(
                {key: value for key, value in result.items() if key != "result_hash"}
            )
            invalid = validate_result(
                root,
                plan,
                result,
                current_head="abc123",
                current_worktree_digest="dirty-hash",
            )
        self.assertTrue(valid["valid"])
        self.assertIn("result_write_scope_exceeded", invalid["reasons"])

    def test_transport_receipt_alone_cannot_prove_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a")])
            packet = plan["packets"][0]
            result = self._result(root, packet)
            result["verification"] = []
            result["result_hash"] = stable_hash(
                {key: value for key, value in result.items() if key != "result_hash"}
            )
            validation = validate_result(
                root,
                plan,
                result,
                current_head="abc123",
                current_worktree_digest="dirty-hash",
            )
        self.assertIn("result_completion_unverified", validation["reasons"])

    def test_fabricated_verification_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a")])
            result = self._result(root, plan["packets"][0])
            result["verification"][0]["evidence"] = {
                "path": ".iteration/missing.log",
                "sha256": "0" * 64,
            }
            result["result_hash"] = stable_hash(
                {key: value for key, value in result.items() if key != "result_hash"}
            )
            validation = validate_result(
                root,
                plan,
                result,
                current_head="abc123",
                current_worktree_digest="dirty-hash",
            )
        self.assertIn("result_verification_invalid", validation["reasons"])

    def test_rejects_packet_result_hash_or_baseline_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a")])
            result = self._result(root, plan["packets"][0])
            result["packet_hash"] = "wrong"
            validation = validate_result(
                root,
                plan,
                result,
                current_head="new-head",
                current_worktree_digest="dirty-hash",
            )
        self.assertIn("result_packet_hash_mismatch", validation["reasons"])
        self.assertIn("result_base_head_stale", validation["reasons"])
        self.assertIn("result_hash_mismatch", validation["reasons"])

    def test_read_result_rejects_changed_worktree_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a")])
            result = self._result(root, plan["packets"][0])
            validation = validate_result(
                root,
                plan,
                result,
                current_head="abc123",
                current_worktree_digest="new-dirty-hash",
            )
        self.assertIn("result_worktree_stale", validation["reasons"])

    def test_plan_hash_and_packet_size_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a")])
            self.assertEqual(validate_plan(plan), [])
            plan["packets"][0]["packet_bytes"] += 1
            reasons = validate_plan(plan)
        self.assertIn("plan_hash_mismatch", reasons)
        self.assertIn("plan_packet_size_mismatch", reasons)

    def test_plan_rechecks_total_packet_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a"), task("b")])
            plan["config"]["max_total_packet_bytes"] = 1
            plan["plan_hash"] = stable_hash(
                {key: value for key, value in plan.items() if key != "plan_hash"}
            )
            reasons = validate_plan(plan)
        self.assertIn("plan_total_packet_too_large", reasons)

    def test_batch_requires_every_unique_completed_result_and_aggregates_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            plan = self._plan(root, requirements, pending, [task("a"), task("b")])
            results = [self._result(root, packet) for packet in plan["packets"]]
            valid = validate_batch(
                root,
                plan,
                results,
                current_head="abc123",
                current_worktree_digest="dirty-hash",
            )
            duplicate = validate_batch(
                root,
                plan,
                [results[0], results[0]],
                current_head="abc123",
                current_worktree_digest="dirty-hash",
            )
        self.assertTrue(valid["ready_for_lead_validation"])
        self.assertEqual(valid["aggregate_token_usage"]["total"], 28)
        self.assertFalse(duplicate["valid"])
        self.assertEqual(duplicate["duplicates"], ["a"])
        self.assertEqual(duplicate["missing"], ["b"])

    def test_packet_size_limit_is_hard(self):
        with tempfile.TemporaryDirectory() as directory:
            root, requirements, pending = self._files(directory)
            oversized = task("a")
            oversized["objective"] = "x" * 2000
            with self.assertRaisesRegex(ValueError, "limit"):
                self._plan(
                    root,
                    requirements,
                    pending,
                    [oversized],
                    max_packet_bytes=1000,
                )

    def test_finalize_result_writes_canonical_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text('{"task_id":"a","result_hash":"wrong"}', encoding="utf-8")
            digest = finalize_result(path)
            value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["result_hash"], digest)
        self.assertEqual(digest, stable_hash({"task_id": "a"}))


if __name__ == "__main__":
    unittest.main()
