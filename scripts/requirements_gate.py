#!/usr/bin/env python3
"""Deterministic gate for approved and pending requirement documents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from .requirements_intake import inspect_manifest
    from .requirements_store import read_records, validate_records
except ImportError:  # direct script execution
    from requirements_intake import inspect_manifest
    from requirements_store import read_records, validate_records

PENDING_HEADING = "## 待审批变更 (Pending Changes)"
ACTIVE_HEADING = "## 正式需求 (Active Requirements)"
LEDGER_HEADING = "## 修订账本 (Revision Ledger)"
PENDING_ID = re.compile(r"\bPENDING-REQ-[A-Za-z0-9._-]+\b")
PLACEHOLDER_ONLY = re.compile(r"^\s*(?:_?无_?|[-*]\s*无|<!--.*?-->)\s*$", re.S)


def inspect_documents(active_path: Path, pending_path: Path) -> dict[str, object]:
    active = active_path.read_text(encoding="utf-8")
    pending = pending_path.read_text(encoding="utf-8")
    active_missing = [heading for heading in (ACTIVE_HEADING, LEDGER_HEADING) if heading not in active]
    active_forbidden = PENDING_HEADING in active or bool(re.search(r"(?m)^###\s+PENDING-REQ-", active))
    pending_missing = PENDING_HEADING not in pending
    pending_ids: list[str] = []
    unstructured = False
    if not pending_missing:
        body = pending[pending.index(PENDING_HEADING) + len(PENDING_HEADING) :].strip()
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
        if body and not PLACEHOLDER_ONLY.fullmatch(body):
            pending_ids = sorted(set(PENDING_ID.findall(body)))
            unstructured = not pending_ids
    record_error = None
    try:
        records = [
            *read_records(active_path, "active").values(),
            *read_records(pending_path, "pending").values(),
        ]
        if records:
            validate_records(records)
    except ValueError as error:
        record_error = str(error)
    valid_structure = (
        not active_missing
        and not active_forbidden
        and not pending_missing
        and not unstructured
        and record_error is None
    )
    return {
        "active_file": str(active_path.resolve()),
        "pending_file": str(pending_path.resolve()),
        "valid_structure": valid_structure,
        "active_missing_headings": active_missing,
        "active_contains_pending": active_forbidden,
        "pending_structure_invalid": pending_missing or unstructured,
        "record_error": record_error,
        "pending_ids": pending_ids or (["unstructured-pending-content"] if unstructured else []),
        "executable": valid_structure and not pending_ids,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "assert-executable", "assert-task-executable"))
    parser.add_argument("--file", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
    parser.add_argument("--pending-file", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--intake-file", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.file.is_file() or not args.pending_file.is_file():
        print("requirements file not found", file=sys.stderr)
        return 2
    result = inspect_documents(args.file, args.pending_file)
    if args.command == "assert-task-executable":
        if not args.request_file or not args.intake_file:
            print("task intake and request files are required", file=sys.stderr)
            return 2
        intake = inspect_manifest(args.file, args.pending_file, args.request_file, args.intake_file)
        result["intake"] = intake
        result["executable"] = bool(result["executable"] and intake["executable"])
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        state = "executable" if result["executable"] else "blocked"
        print(f"{state}: {', '.join(result['pending_ids']) or 'no pending requirements'}")
    if args.command.startswith("assert-") and not result["executable"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
