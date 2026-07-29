#!/usr/bin/env python3
"""Validate and enforce a small, explicit iteration budget."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
METRICS = ("exploration_calls", "codegraph_queries", "files_read", "retries", "token")
DEFAULT_BUDGET = {
    "schema_version": SCHEMA_VERSION,
    "max": {
        "exploration_calls": 5,
        "codegraph_queries": 10,
        "files_read": 30,
        "retries": 3,
        "token": 80000,
    },
}


def validate_budget(budget: dict[str, Any]) -> None:
    if budget.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    limits = budget.get("max")
    if not isinstance(limits, dict):
        raise ValueError("budget must contain max object")
    for metric in METRICS:
        value = limits.get(metric)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"max.{metric} must be a non-negative integer")


def check_budget(budget: dict[str, Any], usage: dict[str, Any]) -> dict[str, Any]:
    validate_budget(budget)
    over = []
    normalized = {}
    for metric in METRICS:
        value = usage.get(metric, 0)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"usage.{metric} must be a non-negative integer")
        normalized[metric] = value
        limit = budget["max"][metric]
        if value > limit:
            over.append({"metric": metric, "used": value, "max": limit})
    return {"ok": not over, "max": budget["max"], "usage": normalized, "exceeded": over}


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--force", action="store_true")
    validate = subparsers.add_parser("validate")
    validate.add_argument("--budget", type=Path, required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--budget", type=Path, required=True)
    check.add_argument("--usage", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            if args.output.exists() and not args.force:
                raise ValueError(f"refusing to overwrite {args.output}; use --force")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(DEFAULT_BUDGET, indent=2) + "\n", encoding="utf-8")
            result = {"path": args.output.as_posix()}
        elif args.command == "validate":
            budget = _read(args.budget)
            validate_budget(budget)
            result = {"valid": True}
        else:
            result = check_budget(_read(args.budget), _read(args.usage))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))
    if args.command == "check" and not result["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
