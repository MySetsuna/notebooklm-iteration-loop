#!/usr/bin/env python3
"""Bounded append/tail access for machine-first iteration history."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
REQUIRED_FIELDS = {
    "schema_version": int,
    "id": str,
    "at": str,
    "type": str,
    "facts": list,
    "evidence": list,
    "paths": list,
    "symbols": list,
    "next": list,
}


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    for field, expected_type in REQUIRED_FIELDS.items():
        value = record.get(field)
        if not isinstance(value, expected_type) or (expected_type is str and not value):
            raise ValueError(f"invalid or missing {field}")
    if record["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if len(record["at"]) < 7 or record["at"][4:5] != "-":
        raise ValueError("at must begin with YYYY-MM")


def shard_path(root: Path, record: dict[str, Any]) -> Path:
    return root / f"events-{record['at'][:7]}.jsonl"


def append_record(root: Path, record: dict[str, Any]) -> Path:
    validate_record(record)
    path = shard_path(root, record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        handle.write("\n")
    return path


def _tail_bytes(path: Path, byte_limit: int) -> tuple[bytes, bool]:
    if byte_limit <= 0:
        return b"", False
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        start = max(0, size - byte_limit)
        handle.seek(start)
        return handle.read(), start > 0


def tail_records(
    root: Path,
    limit: int = 10,
    types: set[str] | None = None,
    max_bytes: int = 65536,
) -> list[dict[str, Any]]:
    """Return newest matching records without deserializing complete shards."""
    if limit <= 0 or max_bytes <= 0:
        return []
    records: list[dict[str, Any]] = []
    remaining = max_bytes
    for path in sorted(root.glob("events-*.jsonl"), reverse=True):
        if remaining <= 0 or len(records) >= limit:
            break
        payload, truncated = _tail_bytes(path, remaining)
        remaining -= len(payload)
        lines = payload.splitlines()
        if truncated and lines:
            lines = lines[1:]
        for line in reversed(lines):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict) or (types and record.get("type") not in types):
                continue
            records.append(record)
            if len(records) >= limit:
                break
    return records


def migrate_markdown(
    root: Path,
    source: Path,
    record_id: str,
    at: str,
    record_type: str,
) -> Path:
    """One-way compact migration; Git preserves the original Markdown history."""
    text = source.read_text(encoding="utf-8")
    facts = [line.lstrip("#- ").strip() for line in text.splitlines() if line.startswith(("#", "-"))]
    record = {
        "schema_version": SCHEMA_VERSION,
        "id": record_id,
        "at": at,
        "type": record_type,
        "facts": facts[:32] or [source.name],
        "evidence": [f"git-history:{source.as_posix()}", f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"],
        "paths": [source.as_posix()],
        "symbols": [],
        "next": [],
    }
    return append_record(root, record)


def _load_record(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append")
    append.add_argument("--root", type=Path, required=True)
    append.add_argument("--record", type=Path, required=True)

    tail = subparsers.add_parser("tail")
    tail.add_argument("--root", type=Path, required=True)
    tail.add_argument("--limit", type=int, default=10)
    tail.add_argument("--type", action="append", dest="types")
    tail.add_argument("--max-bytes", type=int, default=65536)

    migrate = subparsers.add_parser("migrate-markdown")
    migrate.add_argument("--root", type=Path, required=True)
    migrate.add_argument("--source", type=Path, required=True)
    migrate.add_argument("--id", required=True)
    migrate.add_argument("--at", required=True)
    migrate.add_argument("--type", required=True, dest="record_type")

    args = parser.parse_args()
    if args.command == "append":
        path = append_record(args.root, _load_record(args.record))
        print(json.dumps({"path": path.as_posix()}, ensure_ascii=False))
    elif args.command == "tail":
        print(json.dumps(tail_records(args.root, args.limit, set(args.types or []), args.max_bytes), ensure_ascii=False))
    else:
        path = migrate_markdown(args.root, args.source, args.id, args.at, args.record_type)
        print(json.dumps({"path": path.as_posix()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
