#!/usr/bin/env python3
"""Build bounded worker packets and validate multi-agent results."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

try:
    from .requirements_store import pending_index, select_records
except ImportError:  # direct script execution
    from requirements_store import pending_index, select_records

SCHEMA_VERSION = 1
BACKENDS = {"auto", "ridge", "native", "tmux", "serial"}
RESULT_STATUSES = {"completed", "blocked", "failed"}
TOKEN_FIELDS = ("input", "cache_read", "cache_write", "output", "total")
DEFAULTS = {
    "enabled": True,
    "backend": "auto",
    "max_workers": 3,
    "max_packet_bytes": 16384,
    "max_total_packet_bytes": 49152,
}


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError("git rev-parse HEAD failed")
    return result.stdout.strip()


def _worktree_digest(root: Path) -> str:
    diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if diff.returncode or untracked.returncode:
        raise ValueError("git worktree digest failed")
    digest = hashlib.sha256(diff.stdout)
    for raw_path in sorted(path for path in untracked.stdout.split(b"\0") if path):
        relative = raw_path.decode("utf-8", errors="surrogateescape")
        path = root / relative
        digest.update(raw_path)
        if path.is_file():
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _strings(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(f"{field} must be a list of non-empty strings")
    normalized = list(dict.fromkeys(item.strip() for item in value))
    if not allow_empty and not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _relative(root: Path, value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (root / candidate).resolve()
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"path escapes project root: {value}") from error
    text = relative.as_posix()
    if not text or text == ".":
        raise ValueError("project root is not an allowed path")
    return text


def _paths(root: Path, value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    return [
        _relative(root, item)
        for item in _strings(value, field, allow_empty=allow_empty)
    ]


def _paths_overlap(left: str, right: str) -> bool:
    left_path = Path(os.path.normcase(left)).parts
    right_path = Path(os.path.normcase(right)).parts
    shared = min(len(left_path), len(right_path))
    return left_path[:shared] == right_path[:shared]


def _waves(tasks: list[dict[str, Any]]) -> list[list[str]]:
    ids = {task["id"] for task in tasks}
    dependencies = {
        task["id"]: set(_strings(task.get("depends_on", []), f"{task['id']}.depends_on"))
        for task in tasks
    }
    for task_id, required in dependencies.items():
        unknown = required - ids
        if task_id in required or unknown:
            raise ValueError(f"{task_id} has invalid dependencies")
    remaining = set(ids)
    completed: set[str] = set()
    waves: list[list[str]] = []
    while remaining:
        ready = sorted(task_id for task_id in remaining if dependencies[task_id] <= completed)
        if not ready:
            raise ValueError("task dependency cycle detected")
        waves.append(ready)
        completed.update(ready)
        remaining.difference_update(ready)
    return waves


def _execution_waves(
    dependency_waves: list[list[str]],
    tasks: dict[str, dict[str, Any]],
    backend: str,
) -> tuple[list[list[str]], list[str]]:
    waves: list[list[str]] = []
    rejections: list[str] = []
    for dependency_wave in dependency_waves:
        if backend == "serial":
            waves.extend([[task_id] for task_id in dependency_wave])
            continue
        groups: list[list[str]] = []
        for task_id in dependency_wave:
            task = tasks[task_id]
            placed = False
            for group in groups:
                conflicts = []
                for peer_id in group:
                    peer = tasks[peer_id]
                    if any(
                        _paths_overlap(left, right)
                        for left in task["scope"]["allowed_write_paths"]
                        for right in peer["scope"]["allowed_write_paths"]
                    ):
                        conflicts.append("write_scope")
                    if set(task["exclusive_resources"]) & set(peer["exclusive_resources"]):
                        conflicts.append("exclusive_resource")
                    if set(task["scope"]["control_write_paths"]) & set(
                        peer["scope"]["control_write_paths"]
                    ):
                        conflicts.append("control_write")
                    if (
                        task["execution_kind"] == "write"
                        and task["isolation"] != "worktree"
                    ) or (
                        peer["execution_kind"] == "write"
                        and peer["isolation"] != "worktree"
                    ):
                        conflicts.append("write_isolation")
                if not conflicts:
                    group.append(task_id)
                    placed = True
                    break
                rejections.append(
                    f"{task_id}:{','.join(sorted(set(conflicts)))}"
                )
            if not placed:
                groups.append([task_id])
        waves.extend(groups)
    return waves, sorted(set(rejections))


def _validate_codegraph(task: dict[str, Any]) -> dict[str, Any]:
    value = task.get("codegraph")
    if not isinstance(value, dict):
        raise ValueError(f"{task['id']}.codegraph must be an object")
    queries = _strings(value.get("queries", []), f"{task['id']}.codegraph.queries")
    facts = value.get("facts", [])
    if not isinstance(facts, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("fact"), str)
        or not item["fact"].strip()
        or not isinstance(item.get("evidence"), str)
        or not item["evidence"].strip()
        for item in facts
    ):
        raise ValueError(f"{task['id']}.codegraph.facts must contain fact/evidence objects")
    reason = value.get("not_applicable_reason")
    if not facts and (not isinstance(reason, str) or not reason.strip()):
        raise ValueError(f"{task['id']}.codegraph needs facts or not_applicable_reason")
    return {
        "queries": queries,
        "facts": facts,
        **({"not_applicable_reason": reason.strip()} if isinstance(reason, str) and reason.strip() else {}),
    }


def _verification(task: dict[str, Any]) -> list[dict[str, Any]]:
    value = task.get("verification")
    if not isinstance(value, list) or not value:
        raise ValueError(f"{task['id']}.verification must not be empty")
    normalized = []
    for item in value:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("command"), str)
            or not item["command"].strip()
            or not isinstance(item.get("expected_exit"), int)
        ):
            raise ValueError(f"{task['id']}.verification item is invalid")
        normalized.append(
            {
                "command": item["command"].strip(),
                "expected_exit": item["expected_exit"],
            }
        )
    return normalized


def _config(manifest: dict[str, Any], mode: str | None, backend: str | None) -> dict[str, Any]:
    supplied = manifest.get("dispatch", {})
    if not isinstance(supplied, dict):
        raise ValueError("dispatch must be an object")
    value = {**DEFAULTS, **supplied}
    if mode is not None:
        value["enabled"] = mode == "on"
    if backend is not None:
        value["backend"] = backend
    if not isinstance(value["enabled"], bool):
        raise ValueError("dispatch.enabled must be boolean")
    if value["backend"] not in BACKENDS:
        raise ValueError("dispatch.backend is invalid")
    for field in ("max_workers", "max_packet_bytes", "max_total_packet_bytes"):
        if not isinstance(value[field], int) or value[field] <= 0:
            raise ValueError(f"dispatch.{field} must be a positive integer")
    return value


def _transport(backend: str) -> dict[str, Any]:
    return {
        "requested_backend": backend,
        "auto_order": ["ridge", "native", "tmux", "serial"],
        "payload": "shared packet file; Ridge may use ridge_stash_data and send only ridge://cache URI",
        "ridge": {
            "discover": "ridge_get_team_profile",
            "spawn_if_configured": "ridge_split_pane",
            "delegate": "ridge_delegate_task",
            "observe": ["ridge_delivery_status", "ridge_capture_pane", "ridge_inbox_read"],
            "acknowledge": "ridge_acknowledge_receipt",
            "completion_rule": "receipt is transport evidence only; validated result file proves completion",
        },
        "native": {"actions": ["spawn_agent", "send_message", "wait_agent"]},
        "tmux": {"actions": ["create pane/session", "send packet path", "collect result file"]},
        "serial": {"actions": ["run one bounded worker packet at a time"]},
    }


def build_plan(
    root: Path,
    manifest: dict[str, Any],
    requirements_path: Path,
    pending_path: Path,
    mode: str | None = None,
    backend: str | None = None,
    current_head: str | None = None,
    worktree_digest: str | None = None,
) -> dict[str, Any]:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    config = _config(manifest, mode, backend)
    head = current_head or _git_head(root)
    baseline_digest = worktree_digest or _worktree_digest(root)
    requested_head = manifest.get("base_head")
    if requested_head and requested_head != head:
        raise ValueError("manifest base_head is stale")
    if pending_index(pending_path):
        raise ValueError("pending requirements block dispatch")
    raw_tasks = manifest.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError("tasks must not be empty")
    if len(raw_tasks) > config["max_workers"]:
        raise ValueError("task count exceeds max_workers")
    ids = [task.get("id") for task in raw_tasks if isinstance(task, dict)]
    if len(ids) != len(raw_tasks) or any(
        not isinstance(task_id, str) or not task_id.strip() for task_id in ids
    ):
        raise ValueError("every task needs a non-empty id")
    if len(set(ids)) != len(ids):
        raise ValueError("task ids must be unique")
    dispatch_id = stable_hash(
        {"head": head, "worktree_digest": baseline_digest, "tasks": sorted(ids)}
    )[:24]
    waves = _waves(raw_tasks)
    by_id = {task["id"]: task for task in raw_tasks}
    normalized: dict[str, dict[str, Any]] = {}
    for task in raw_tasks:
        task_id = task["id"]
        objective = task.get("objective")
        if not isinstance(objective, str) or not objective.strip():
            raise ValueError(f"{task_id}.objective must not be empty")
        requirement_ids = _strings(
            task.get("requirements"), f"{task_id}.requirements", allow_empty=False
        )
        records = select_records(requirements_path, requirement_ids, config["max_packet_bytes"])
        files = _paths(root, task.get("files", []), f"{task_id}.files")
        tests = _paths(root, task.get("tests", []), f"{task_id}.tests")
        execution_kind = task.get("execution_kind", "write")
        if execution_kind not in {"read", "write"}:
            raise ValueError(f"{task_id}.execution_kind is invalid")
        writes = _paths(root, task.get("write_paths", []), f"{task_id}.write_paths")
        if execution_kind == "write" and not writes:
            raise ValueError(f"{task_id}.write_paths must not be empty")
        isolation = task.get("isolation", "shared")
        if isolation not in {"shared", "worktree"}:
            raise ValueError(f"{task_id}.isolation is invalid")
        result_path = _relative(
            root,
            task.get("result_path", f".iteration/agents/result-{task_id}.json"),
        )
        constraints = _strings(
            task.get("constraints"), f"{task_id}.constraints", allow_empty=False
        )
        normalized[task_id] = {
            "schema_version": SCHEMA_VERSION,
            "dispatch_id": dispatch_id,
            "task_id": task_id,
            "baseline": {
                "head": head,
                "worktree_digest": baseline_digest,
                "codegraph_revision": manifest.get("codegraph_revision", "current-index"),
            },
            "objective": objective.strip(),
            "requirements": {"ids": requirement_ids, "records": records},
            "symbols": _strings(task.get("symbols", []), f"{task_id}.symbols"),
            "codegraph": _validate_codegraph(task),
            "scope": {
                "allowed_files": list(dict.fromkeys([*files, *tests, *writes])),
                "allowed_write_paths": writes,
                "control_write_paths": [result_path],
                "deny_unlisted": True,
            },
            "constraints": constraints,
            "verification": _verification(task),
            "depends_on": _strings(task.get("depends_on", []), f"{task_id}.depends_on"),
            "execution_kind": execution_kind,
            "isolation": isolation,
            "exclusive_resources": _strings(
                task.get("exclusive_resources", []), f"{task_id}.exclusive_resources"
            ),
            "worker_policy": {
                "may_approve_requirements": False,
                "may_expand_scope": False,
                "may_call_notebooklm": False,
                "may_commit_or_push": False,
                "must_write_result_file": True,
            },
            "transport": {
                "requested_backend": config["backend"],
                "completion_rule": "transport receipt is not completion; finalized result file is required",
            },
            "result_path": result_path,
        }
    execution_waves, parallel_rejections = _execution_waves(
        waves, normalized, config["backend"]
    )
    packets = []
    total_bytes = 0
    for task_id in sorted(normalized):
        packet = normalized[task_id]
        packet["packet_hash"] = stable_hash(packet)
        packet["packet_bytes"] = 0
        while True:
            size = len(_canonical(packet))
            if packet["packet_bytes"] == size:
                break
            packet["packet_bytes"] = size
        if size > config["max_packet_bytes"]:
            raise ValueError(f"{task_id} packet uses {size} bytes; limit is {config['max_packet_bytes']}")
        total_bytes += size
        packets.append(packet)
    if total_bytes > config["max_total_packet_bytes"]:
        raise ValueError("total packet bytes exceed limit")
    execution_mode = "disabled"
    if config["enabled"]:
        execution_mode = (
            "parallel" if any(len(wave) > 1 for wave in execution_waves) else "bounded_single"
        )
    plan = {
        "schema_version": SCHEMA_VERSION,
        "dispatch_id": dispatch_id,
        "baseline": {"head": head, "worktree_digest": baseline_digest},
        "orchestration_enabled": config["enabled"],
        "execution_mode": execution_mode,
        "waves": execution_waves if config["enabled"] else [],
        "parallel_rejections": parallel_rejections,
        "config": config,
        "transport": _transport(config["backend"]),
        "packets": packets if config["enabled"] else [],
        "total_packet_bytes": total_bytes if config["enabled"] else 0,
    }
    plan["plan_hash"] = stable_hash(plan)
    return plan


def write_plan(output_dir: Path, plan: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    for packet in plan["packets"]:
        (output_dir / f"{packet['task_id']}.json").write_text(
            json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    path = output_dir / "dispatch-plan.json"
    path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def finalize_result(path: Path) -> str:
    value = _read(path)
    value.pop("result_hash", None)
    digest = stable_hash(value)
    value["result_hash"] = digest
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return digest


def validate_plan(plan: dict[str, Any]) -> list[str]:
    reasons = []
    if plan.get("schema_version") != SCHEMA_VERSION:
        reasons.append("plan_schema_invalid")
    expected_plan_hash = stable_hash(
        {key: value for key, value in plan.items() if key != "plan_hash"}
    )
    if plan.get("plan_hash") != expected_plan_hash:
        reasons.append("plan_hash_mismatch")
    max_packet_bytes = plan.get("config", {}).get("max_packet_bytes")
    packets = plan.get("packets")
    if not isinstance(packets, list):
        return sorted(set([*reasons, "plan_packets_invalid"]))
    for packet in packets:
        if not isinstance(packet, dict):
            reasons.append("plan_packet_invalid")
            continue
        payload = {
            key: value
            for key, value in packet.items()
            if key not in {"packet_hash", "packet_bytes"}
        }
        if packet.get("packet_hash") != stable_hash(payload):
            reasons.append("plan_packet_hash_mismatch")
        size = len(_canonical(packet))
        if packet.get("packet_bytes") != size:
            reasons.append("plan_packet_size_mismatch")
        if isinstance(max_packet_bytes, int) and size > max_packet_bytes:
            reasons.append("plan_packet_too_large")
    total = sum(
        packet.get("packet_bytes", 0)
        for packet in packets
        if isinstance(packet, dict) and isinstance(packet.get("packet_bytes"), int)
    )
    if plan.get("total_packet_bytes") != total:
        reasons.append("plan_total_packet_size_mismatch")
    max_total = plan.get("config", {}).get("max_total_packet_bytes")
    if isinstance(max_total, int) and total > max_total:
        reasons.append("plan_total_packet_too_large")
    return sorted(set(reasons))


def _packet(plan: dict[str, Any], task_id: str) -> dict[str, Any]:
    matches = [packet for packet in plan.get("packets", []) if packet.get("task_id") == task_id]
    if len(matches) != 1:
        raise ValueError(f"unknown task_id: {task_id}")
    return matches[0]


def validate_result(
    root: Path,
    plan: dict[str, Any],
    result: dict[str, Any],
    current_head: str | None = None,
    current_worktree_digest: str | None = None,
) -> dict[str, Any]:
    reasons = [f"result_{reason}" for reason in validate_plan(plan)]
    if result.get("schema_version") != SCHEMA_VERSION:
        reasons.append("result_schema_invalid")
    if result.get("dispatch_id") != plan.get("dispatch_id"):
        reasons.append("result_dispatch_id_mismatch")
    task_id = result.get("task_id")
    if not isinstance(task_id, str):
        return {"valid": False, "reasons": ["result_task_id_invalid"]}
    try:
        packet = _packet(plan, task_id)
    except ValueError:
        return {"valid": False, "reasons": ["result_task_unknown"]}
    head = current_head or _git_head(root)
    if current_worktree_digest is None:
        current_worktree_digest = _worktree_digest(root)
    baseline = result.get("baseline")
    if (
        head != plan.get("baseline", {}).get("head")
        or not isinstance(baseline, dict)
        or baseline != packet["baseline"]
    ):
        reasons.append("result_base_head_stale")
    if (
        current_worktree_digest is not None
        and (
            packet.get("execution_kind") == "read"
            or packet.get("isolation") == "worktree"
        )
        and current_worktree_digest != packet["baseline"]["worktree_digest"]
    ):
        reasons.append("result_worktree_stale")
    if result.get("packet_hash") != packet["packet_hash"]:
        reasons.append("result_packet_hash_mismatch")
    status = result.get("status")
    if status not in RESULT_STATUSES:
        reasons.append("result_status_invalid")
    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        reasons.append("result_summary_invalid")
    try:
        changed = _paths(root, result.get("changed_paths", []), "result.changed_paths")
    except ValueError:
        changed = []
        reasons.append("result_changed_paths_invalid")
    allowed = packet["scope"]["allowed_write_paths"]
    outside = [
        path
        for path in changed
        if path not in allowed
    ]
    if outside:
        reasons.append("result_write_scope_exceeded")
    verification = result.get("verification")
    planned = {
        (item["command"], item["expected_exit"]) for item in packet["verification"]
    }
    observed: set[tuple[str, int]] = set()
    evidence_invalid = not isinstance(verification, list)
    for item in verification if isinstance(verification, list) else []:
        evidence = item.get("evidence") if isinstance(item, dict) else None
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("command"), str)
            or not isinstance(item.get("exit_code"), int)
            or not isinstance(evidence, dict)
            or not isinstance(evidence.get("path"), str)
            or not isinstance(evidence.get("sha256"), str)
        ):
            evidence_invalid = True
            continue
        try:
            evidence_path = root / _relative(root, evidence["path"])
            if hashlib.sha256(evidence_path.read_bytes()).hexdigest() != evidence["sha256"]:
                evidence_invalid = True
        except (OSError, ValueError):
            evidence_invalid = True
    if evidence_invalid:
        reasons.append("result_verification_invalid")
    else:
        observed = {(item["command"], item["exit_code"]) for item in verification}
    if status == "completed" and not planned <= observed:
        reasons.append("result_completion_unverified")
    usage = result.get("token_usage")
    if not isinstance(usage, dict) or any(
        not isinstance(usage.get(field), int) or usage[field] < 0 for field in TOKEN_FIELDS
    ):
        reasons.append("result_token_usage_invalid")
    receipt = result.get("transport_receipt")
    if receipt is not None and not isinstance(receipt, dict):
        reasons.append("result_transport_receipt_invalid")
    result_hash = result.get("result_hash")
    hash_input = {key: value for key, value in result.items() if key != "result_hash"}
    if not isinstance(result_hash, str) or result_hash != stable_hash(hash_input):
        reasons.append("result_hash_mismatch")
    return {
        "valid": not reasons,
        "task_id": task_id,
        "status": status,
        "reasons": sorted(set(reasons)),
        "outside_write_scope": outside,
    }


def validate_batch(
    root: Path,
    plan: dict[str, Any],
    results: Iterable[dict[str, Any]],
    current_head: str | None = None,
    current_worktree_digest: str | None = None,
) -> dict[str, Any]:
    values = list(results)
    by_task = {value.get("task_id"): value for value in values if isinstance(value, dict)}
    expected = {packet["task_id"] for packet in plan.get("packets", [])}
    missing = sorted(expected - set(by_task))
    unexpected = sorted(str(task_id) for task_id in set(by_task) - expected)
    duplicate_ids = sorted(
        task_id
        for task_id in expected
        if sum(value.get("task_id") == task_id for value in values if isinstance(value, dict)) > 1
    )
    validations = [
        validate_result(
            root,
            plan,
            by_task[task_id],
            current_head,
            current_worktree_digest,
        )
        for task_id in sorted(expected & set(by_task))
    ]
    aggregate = {field: 0 for field in TOKEN_FIELDS}
    for task_id in expected & set(by_task):
        usage = by_task[task_id].get("token_usage", {})
        if isinstance(usage, dict):
            for field in TOKEN_FIELDS:
                value = usage.get(field)
                if isinstance(value, int) and value >= 0:
                    aggregate[field] += value
    ready = (
        not missing
        and not unexpected
        and not duplicate_ids
        and all(item["valid"] and item["status"] == "completed" for item in validations)
    )
    return {
        "valid": (
            not missing
            and not unexpected
            and not duplicate_ids
            and all(item["valid"] for item in validations)
        ),
        "ready_for_lead_validation": ready,
        "missing": missing,
        "unexpected": unexpected,
        "duplicates": duplicate_ids,
        "results": validations,
        "aggregate_token_usage": aggregate,
        "note": "aggregate is measurement only; compare against same-task single-agent baseline",
    }


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--root", type=Path, required=True)
    build.add_argument("--manifest", type=Path, required=True)
    build.add_argument("--requirements", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
    build.add_argument("--pending", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
    build.add_argument("--output-dir", type=Path, default=Path(".iteration/agents"))
    build.add_argument("--mode", choices=("on", "off"))
    build.add_argument("--backend", choices=sorted(BACKENDS))
    result = subparsers.add_parser("validate-result")
    result.add_argument("--root", type=Path, required=True)
    result.add_argument("--plan", type=Path, required=True)
    result.add_argument("--result", type=Path, required=True)
    finalize = subparsers.add_parser("finalize-result")
    finalize.add_argument("--result", type=Path, required=True)
    batch = subparsers.add_parser("validate-batch")
    batch.add_argument("--root", type=Path, required=True)
    batch.add_argument("--plan", type=Path, required=True)
    batch.add_argument("--result", type=Path, action="append", required=True)
    args = parser.parse_args()
    try:
        if args.command == "build":
            plan = build_plan(
                args.root,
                _read(args.manifest),
                args.requirements,
                args.pending,
                args.mode,
                args.backend,
            )
            path = write_plan(args.output_dir, plan)
            output = {
                "path": path.as_posix(),
                "plan_hash": plan["plan_hash"],
                "execution_mode": plan["execution_mode"],
                "waves": plan["waves"],
            }
        elif args.command == "finalize-result":
            output = {"result": args.result.as_posix(), "result_hash": finalize_result(args.result)}
        elif args.command == "validate-result":
            output = validate_result(args.root, _read(args.plan), _read(args.result))
        else:
            output = validate_batch(
                args.root, _read(args.plan), [_read(path) for path in args.result]
            )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(output, ensure_ascii=False))
    if args.command in {"validate-result", "validate-batch"} and not output["valid"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
