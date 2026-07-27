#!/usr/bin/env python3
"""Deterministic Pending-requirement gate for REQUIREMENTS-SPEC.md."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PENDING_HEADING = "## 待审批变更 (Pending Changes)"
ACTIVE_HEADING = "## 正式需求 (Active Requirements)"
LEDGER_HEADING = "## 修订账本 (Revision Ledger)"
PENDING_ID = re.compile(r"\bPENDING-REQ-[A-Za-z0-9._-]+\b")
PLACEHOLDER_ONLY = re.compile(r"^\s*(?:_?无_?|[-*]\s*无|<!--.*?-->)\s*$", re.S)


def inspect_document(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    headings = [PENDING_HEADING, ACTIVE_HEADING, LEDGER_HEADING]
    missing = [heading for heading in headings if heading not in text]
    pending_ids: list[str] = []
    if not missing:
        start = text.index(PENDING_HEADING) + len(PENDING_HEADING)
        end = text.index(ACTIVE_HEADING, start)
        pending_body = text[start:end].strip()
        pending_body = re.sub(r"<!--.*?-->", "", pending_body, flags=re.S).strip()
        if pending_body and not PLACEHOLDER_ONLY.fullmatch(pending_body):
            pending_ids = sorted(set(PENDING_ID.findall(pending_body)))
            if not pending_ids:
                pending_ids = ["unstructured-pending-content"]
    return {
        "file": str(path.resolve()),
        "valid_structure": not missing,
        "missing_headings": missing,
        "pending_ids": pending_ids,
        "executable": not missing and not pending_ids,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "assert-executable"))
    parser.add_argument("--file", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.file.is_file():
        print(f"requirements file not found: {args.file}", file=sys.stderr)
        return 2
    result = inspect_document(args.file)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        state = "executable" if result["executable"] else "blocked"
        print(f"{state}: {', '.join(result['pending_ids']) or 'no pending requirements'}")
    if args.command == "assert-executable" and not result["executable"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
