#!/usr/bin/env python3
"""Compile a bounded, task-scoped context package without scanning the repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1


def _items(values: Iterable[str]) -> list[str]:
    return sorted({value.strip() for value in values if value and value.strip()})


def _relative(root: Path, value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path must stay under project root: {value}")
    return path.as_posix()


def _load_budget(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    budget = json.loads(path.read_text(encoding="utf-8"))
    limits = budget.get("max") if isinstance(budget, dict) else None
    if not isinstance(limits, dict):
        raise ValueError("budget must contain max object")
    return budget


def compile_context(
    root: Path,
    task: str,
    symbols: Iterable[str] = (),
    files: Iterable[str] = (),
    tests: Iterable[str] = (),
    constraints: Iterable[str] = (),
    failed_knowledge: Iterable[str] = (),
    modify: Iterable[str] = (),
    budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not task.strip():
        raise ValueError("task must not be empty")
    if not any((symbols, files, tests)):
        raise ValueError("at least one explicit symbol, file, or test is required")
    if not any(modify):
        raise ValueError("at least one explicit modify path is required")
    normalized_files = [_relative(root, value) for value in files]
    normalized_tests = [_relative(root, value) for value in tests]
    normalized_modify = [_relative(root, value) for value in modify]
    normalized_files = _items(normalized_files)
    normalized_tests = _items(normalized_tests)
    allowed_files = _items([*normalized_files, *normalized_tests])
    max_files = len(allowed_files)
    if budget:
        configured = budget.get("max", {}).get("files_read")
        if isinstance(configured, int):
            max_files = configured
        if len(allowed_files) > max_files:
            raise ValueError(f"context has {len(allowed_files)} files; budget allows {max_files}")
    normalized_symbols = _items(symbols)
    queries = _items([*normalized_symbols, *(f"file:{path}" for path in normalized_files)])
    return {
        "schema_version": SCHEMA_VERSION,
        "task": task.strip(),
        "symbols": normalized_symbols,
        "files": normalized_files,
        "tests": normalized_tests,
        "constraints": _items(constraints),
        "failed_knowledge": _items(failed_knowledge),
        "codegraph": {
            "mode": "targeted",
            "queries": queries,
            "full_rebuild": False,
        },
        "read_policy": {
            "allowed_files": allowed_files,
            "deny_unlisted": True,
            "max_files": max_files,
        },
        "write_policy": {
            "allowed_paths": _items(normalized_modify),
            "deny_unlisted": True,
        },
        "response_policy": {
            "format": "delta_evidence_next",
            "forbid_background_recap": True,
        },
        "budget": budget,
    }


def write_context(output: Path, context: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--test", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--failed", action="append", default=[])
    parser.add_argument("--modify", action="append", default=[])
    parser.add_argument("--budget", type=Path)
    parser.add_argument("--output", type=Path, default=Path(".iteration/context.json"))
    args = parser.parse_args()
    try:
        budget = _load_budget(args.budget)
        context = compile_context(
            args.root,
            args.task,
            args.symbol,
            args.file,
            args.test,
            args.constraint,
            args.failed,
            args.modify,
            budget,
        )
        output = args.output if args.output.is_absolute() else args.root / args.output
        write_context(output, context)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps({"path": output.as_posix(), "allowed_files": len(context["read_policy"]["allowed_files"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
