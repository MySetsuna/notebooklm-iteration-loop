#!/usr/bin/env python3
"""Hard gate for bounded context, write scope, and iteration budget."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

try:
    from .iteration_budget import check_budget
except ImportError:  # direct script execution
    from iteration_budget import check_budget


def _items(values: Iterable[str]) -> set[str]:
    return {value.replace("\\", "/").strip() for value in values if value and value.strip()}


def _changed_paths(root: Path) -> set[str]:
    tracked = subprocess.run(
        ["git", "diff", "HEAD", "--name-only", "--diff-filter=ACMRD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    changed = _items(tracked.stdout.splitlines()) if tracked.returncode == 0 else set()
    if untracked.returncode == 0:
        changed.update(_items(untracked.stdout.splitlines()))
    return changed


def check_context(context: dict[str, Any]) -> list[str]:
    violations = []
    if context.get("schema_version") != 1:
        violations.append("context_schema_invalid")
    if not context.get("task"):
        violations.append("task_missing")
    requirements = context.get("requirements", {})
    requirement_ids = requirements.get("ids", []) if isinstance(requirements, dict) else []
    requirement_records = requirements.get("records", []) if isinstance(requirements, dict) else []
    if not isinstance(requirement_ids, list) or not isinstance(requirement_records, list):
        violations.append("requirement_scope_invalid")
        requirement_ids = []
        requirement_records = []
    record_ids = [record.get("id") for record in requirement_records if isinstance(record, dict)]
    if requirement_records and record_ids != requirement_ids:
        violations.append("requirement_scope_invalid")
    if not any(context.get(key) for key in ("symbols", "files", "tests")) and not requirement_ids:
        violations.append("explicit_entry_missing")
    read_policy = context.get("read_policy", {})
    if read_policy.get("deny_unlisted") is not True or not isinstance(read_policy.get("allowed_files"), list):
        violations.append("read_scope_unbounded")
    write_policy = context.get("write_policy", {})
    if write_policy.get("deny_unlisted") is not True or not write_policy.get("allowed_paths"):
        violations.append("write_scope_unbounded")
    codegraph = context.get("codegraph", {})
    if codegraph.get("full_rebuild") is not False or codegraph.get("mode") != "targeted":
        violations.append("full_scan_forbidden")
    queries = codegraph.get("queries", [])
    max_queries = context.get("budget", {}).get("max", {}).get("codegraph_queries")
    if not isinstance(queries, list) or (
        isinstance(max_queries, int) and len(queries) > max_queries
    ):
        violations.append("codegraph_scope_exceeded")
    response_policy = context.get("response_policy", {})
    if response_policy.get("forbid_background_recap") is not True:
        violations.append("background_recap_forbidden")
    return violations


def check_gate(
    root: Path,
    context: dict[str, Any],
    budget: dict[str, Any],
    usage: dict[str, Any],
    changed_paths: Iterable[str] | None = None,
) -> dict[str, Any]:
    violations = check_context(context)
    allowed = _items(context.get("write_policy", {}).get("allowed_paths", []))
    changed = _items(changed_paths) if changed_paths is not None else _changed_paths(root)
    outside = sorted(changed - allowed)
    if outside:
        violations.append("write_scope_exceeded")
    budget_result = check_budget(budget, usage)
    if not budget_result["ok"]:
        violations.append("iteration_budget_exceeded")
    return {
        "ok": not violations,
        "violations": sorted(set(violations)),
        "changed_paths": sorted(changed),
        "outside_write_scope": outside,
        "budget": budget_result,
    }


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--budget", type=Path, required=True)
    parser.add_argument("--usage", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check_gate(args.root, _read(args.context), _read(args.budget), _read(args.usage))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))
    if not result["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
