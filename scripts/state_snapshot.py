#!/usr/bin/env python3
"""Build and validate the runtime PROJECT-STATE source used for NotebookLM."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .requirements_store import pending_index
except ImportError:  # direct script execution
    from requirements_store import pending_index

RUNTIME_MARKER = "<!-- PROJECT_STATE_RUNTIME -->"
VERSION = re.compile(r"(?m)^-\s*需求版本:`([^`]+)`\s*$")
METADATA = re.compile(r"(?m)^-\s*([a-z_]+):`([^`]*)`\s*$")
REQUIRED_HEADINGS = (
    "## 当前迭代目标",
    "## 已验证代码事实",
    "## 相关模块与 symbol",
    "## 最近完成与当前 diff",
    "## 验证状态",
    "## 当前失败信号与风险",
    "## 架构边界",
    "## 下一项已批准工作",
)


def requirements_version(path: Path) -> str:
    match = VERSION.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("requirements version is missing")
    return match.group(1)


def requirements_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decision_hash(decision: dict[str, Any]) -> str:
    payload = json.dumps(
        decision, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"git {' '.join(args)} failed")
    return result.stdout.strip()


def repository_head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD")


def changed_paths(root: Path, ignored_paths: set[str] | None = None) -> list[str]:
    tracked = _git(root, "diff", "HEAD", "--name-only", "--diff-filter=ACMRD").splitlines()
    untracked = _git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    ignored = {path.replace("\\", "/") for path in (ignored_paths or set())}
    return sorted({path.replace("\\", "/") for path in [*tracked, *untracked] if path and path.replace("\\", "/") not in ignored})


def _load_decision(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("decision package must contain an object")
    return value


def build_snapshot(
    root: Path,
    state_path: Path,
    requirements_path: Path,
    pending_path: Path,
    generated_at: str | None = None,
    decision: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> str:
    base = state_path.read_text(encoding="utf-8").split(RUNTIME_MARKER, 1)[0].rstrip()
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in base]
    if missing:
        raise ValueError(f"PROJECT-STATE missing headings: {', '.join(missing)}")
    head = repository_head(root)
    version = requirements_version(requirements_path)
    digest = requirements_hash(requirements_path)
    pending_digest = requirements_hash(pending_path)
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    ignored = {output_path.resolve().relative_to(root.resolve()).as_posix()} if output_path else set()
    paths = changed_paths(root, ignored)
    pending = pending_index(pending_path)
    pending_lines = (
        [
            f"- `{item['id']}` · {item['topic']} · `{item['status']}`；冻结：{item['frozen_scope']}"
            for item in pending
        ]
        or ["- _无_"]
    )
    runtime = [
        RUNTIME_MARKER,
        "## 运行元数据",
        "",
        f"- repository_head:`{head}`",
        f"- requirements_version:`{version}`",
        f"- requirements_hash:`{digest}`",
        f"- pending_hash:`{pending_digest}`",
        *([f"- decision_hash:`{decision_hash(decision)}`"] if decision is not None else []),
        f"- generated_at:`{timestamp}`",
        f"- current_git_diff:`{','.join(paths) or 'clean'}`",
        "",
        "## 非权威 Pending 索引",
        "",
        *pending_lines,
    ]
    if decision is not None:
        runtime.extend(
            [
                "",
                "## 当前决策包",
                "",
                "```json",
                json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
            ]
        )
    return base + "\n\n" + "\n".join(runtime) + "\n"


def metadata(snapshot: str) -> dict[str, str]:
    if RUNTIME_MARKER not in snapshot:
        raise ValueError("runtime metadata marker is missing")
    return dict(METADATA.findall(snapshot.split(RUNTIME_MARKER, 1)[1]))


def validate_snapshot(
    root: Path,
    snapshot_path: Path,
    requirements_path: Path,
    pending_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    values = metadata(snapshot_path.read_text(encoding="utf-8"))
    expected = {
        "repository_head": repository_head(root),
        "requirements_version": requirements_version(requirements_path),
        "requirements_hash": requirements_hash(requirements_path),
        "pending_hash": requirements_hash(pending_path),
        "current_git_diff": ",".join(changed_paths(root, {output_path.resolve().relative_to(root.resolve()).as_posix()} if output_path else set())) or "clean",
    }
    missing = [field for field in (*expected, "generated_at", "current_git_diff") if not values.get(field)]
    mismatches = [field for field, value in expected.items() if values.get(field) != value]
    try:
        datetime.fromisoformat(values.get("generated_at", ""))
    except ValueError:
        mismatches.append("generated_at")
    return {
        "ok": not missing and not mismatches,
        "missing": missing,
        "mismatches": mismatches,
        "metadata": values,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--root", type=Path, required=True)
    build.add_argument("--state", type=Path, default=Path("docs/PROJECT-STATE.md"))
    build.add_argument("--requirements", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
    build.add_argument("--pending", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
    build.add_argument("--decision", type=Path)
    build.add_argument("--generated-at")
    build.add_argument("--output", type=Path, default=Path(".iteration/PROJECT-STATE.snapshot.md"))
    check = subparsers.add_parser("check")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--snapshot", type=Path, required=True)
    check.add_argument("--requirements", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
    check.add_argument("--pending", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
    args = parser.parse_args()
    try:
        if args.command == "build":
            output = args.output if args.output.is_absolute() else args.root / args.output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                build_snapshot(
                    args.root,
                    args.state,
                    args.requirements,
                    args.pending,
                    args.generated_at,
                    _load_decision(args.decision),
                    output,
                ),
                encoding="utf-8",
            )
            print(json.dumps({"path": output.as_posix()}, ensure_ascii=False))
        else:
            result = validate_snapshot(args.root, args.snapshot, args.requirements, args.pending, args.snapshot)
            print(json.dumps(result, ensure_ascii=False))
            if not result["ok"]:
                raise SystemExit(3)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
