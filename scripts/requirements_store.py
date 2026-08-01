#!/usr/bin/env python3
"""Targeted read/write access for approved and pending requirement documents."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

PENDING_HEADING = "## Pending Changes"
ACTIVE_HEADING = "## Active Requirements"
LEDGER_HEADING = "## Revision Ledger"
ENTRY_HEADING = re.compile(
    r"^###\s+((?:PENDING-)?REQ-[A-Za-z0-9._-]+)\b([^\n]*)$",
    re.MULTILINE,
)
EMPTY_PENDING = re.compile(r"(?m)^\s*_none_\s*$")
REQUIRED_LABELS = {
    "pending": (
        "Type:",
        "Original intent:",
        "Related Active requirement:",
        "Target behavior:",
        "Scope:",
        "Non-goals:",
        "Frozen boundary:",
        "Assumptions/open questions:",
        "Deterministic acceptance:",
        "Expected traceability:",
    ),
    "active": ("Status:", "Version:", "Behavior:", "Boundary:", "Acceptance:", "Traceability:"),
}
PENDING_TYPE = re.compile(r"-\s*(?:Type|类型):\s*`?(?:NEW|MODIFY|REMOVE|FIX)\b")
PLACEHOLDER_VALUE = re.compile(r"^(?:<[^>]+>|TODO|TBD)$", re.IGNORECASE)
LEGACY_HEADINGS = {
    PENDING_HEADING: "## 待审批变更 (Pending Changes)",
    ACTIVE_HEADING: "## 正式需求 (Active Requirements)",
    LEDGER_HEADING: "## 修订账本 (Revision Ledger)",
}
LEGACY_LABELS = {
    "Type:": "类型:", "Original intent:": "原始意图:", "Related Active requirement:": "关联 Active 条款:",
    "Target behavior:": "目标行为:", "Scope:": "范围:", "Non-goals:": "非目标:",
    "Frozen boundary:": "不可动边界:", "Assumptions/open questions:": "假设/待确认:",
    "Deterministic acceptance:": "确定性验收:", "Expected traceability:": "预期追踪:",
    "Status:": "状态:", "Version:": "版本:", "Behavior:": "行为:", "Boundary:": "边界:",
    "Acceptance:": "验收:", "Traceability:": "追踪:", "Approval evidence:": "批准依据:",
}


def _items(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def _field_value(markdown: str, label: str) -> str | None:
    prefixes = (f"- {label}", f"- {LEGACY_LABELS[label]}") if label in LEGACY_LABELS else (f"- {label}",)
    for line in markdown.splitlines():
        stripped = line.strip()
        for prefix in prefixes:
            if stripped.startswith(prefix):
                return stripped[len(prefix) :].strip().strip("`").strip()
    return None


def _section_bounds(text: str, section: str) -> tuple[int, int]:
    if section == "active":
        active_heading = ACTIVE_HEADING if ACTIVE_HEADING in text else LEGACY_HEADINGS[ACTIVE_HEADING]
        ledger_heading = LEDGER_HEADING if LEDGER_HEADING in text else LEGACY_HEADINGS[LEDGER_HEADING]
        start = text.find(active_heading)
        end = text.find(ledger_heading, start + len(active_heading))
        if start < 0 or end < 0:
            raise ValueError("active requirements headings are missing or out of order")
        return start + len(active_heading), end
    pending_heading = PENDING_HEADING if PENDING_HEADING in text else LEGACY_HEADINGS[PENDING_HEADING]
    start = text.find(pending_heading)
    if start < 0:
        raise ValueError("pending requirements heading is missing")
    return start + len(pending_heading), len(text)


def _parse(text: str, section: str) -> tuple[dict[str, dict[str, str]], str]:
    start, end = _section_bounds(text, section)
    body = text[start:end]
    shadow = re.sub(
        r"<!--.*?-->",
        lambda match: re.sub(r"[^\n]", " ", match.group(0)),
        body,
        flags=re.S,
    )
    matches = list(ENTRY_HEADING.finditer(shadow))
    prefix = body[: matches[0].start()] if matches else body
    records: dict[str, dict[str, str]] = {}
    for index, match in enumerate(matches):
        record_id = match.group(1)
        if record_id in records:
            raise ValueError(f"duplicate requirement id: {record_id}")
        if (section == "pending") != record_id.startswith("PENDING-REQ-"):
            raise ValueError(f"{record_id} is in the wrong requirement document")
        finish = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        records[record_id] = {
            "id": record_id,
            "section": section,
            "title": match.group(2).strip().lstrip("·").strip(),
            "markdown": body[match.start() : finish].strip(),
        }
    return records, prefix


def read_records(path: Path, section: str) -> dict[str, dict[str, str]]:
    records, _ = _parse(path.read_text(encoding="utf-8"), section)
    return records


def select_records(path: Path, ids: Iterable[str], max_bytes: int = 16384) -> list[dict[str, str]]:
    requested = _items(ids)
    if not requested or any(record_id.startswith("PENDING-REQ-") for record_id in requested):
        raise ValueError("at least one Active REQ id is required")
    records = read_records(path, "active")
    missing = [record_id for record_id in requested if record_id not in records]
    if missing:
        raise ValueError(f"requirement ids not found: {', '.join(missing)}")
    selected = [records[record_id] for record_id in requested]
    size = len(json.dumps(selected, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if max_bytes <= 0 or size > max_bytes:
        raise ValueError(f"selected requirements use {size} bytes; limit is {max_bytes}")
    return selected


def pending_index(path: Path) -> list[dict[str, str]]:
    records = read_records(path, "pending")
    return [
        {
            "id": record["id"],
            "topic": record["title"],
            "status": "pending",
            "frozen_scope": _field_value(record["markdown"], "Frozen boundary:") or "",
        }
        for record in records.values()
    ]


def _validated_operation(operation: dict[str, Any], evidence: str | None) -> tuple[list[dict[str, str]], list[str]]:
    if operation.get("schema_version") != 1:
        raise ValueError("operation schema_version must be 1")
    upserts = operation.get("upsert", [])
    raw_removals = operation.get("remove", [])
    if not isinstance(upserts, list) or not isinstance(raw_removals, list):
        raise ValueError("upsert and remove must be arrays")
    removals = _items(raw_removals)
    normalized = []
    seen: set[str] = set()
    requires_evidence = bool(removals)
    for record in upserts:
        if not isinstance(record, dict):
            raise ValueError("each upsert must be an object")
        record_id = record.get("id")
        section = record.get("section")
        markdown = record.get("markdown")
        if not all(isinstance(value, str) and value.strip() for value in (record_id, section, markdown)):
            raise ValueError("each upsert requires non-empty id, section, and markdown")
        heading = ENTRY_HEADING.match(markdown.strip())
        if not heading or heading.group(1) != record_id:
            raise ValueError(f"markdown heading must match id: {record_id}")
        if section not in {"pending", "active"}:
            raise ValueError(f"invalid section: {section}")
        if (section == "pending") != record_id.startswith("PENDING-REQ-"):
            raise ValueError(f"id does not match section: {record_id}")
        values = {label: _field_value(markdown, label) for label in REQUIRED_LABELS[section]}
        missing = [label for label, value in values.items() if value is None]
        empty = [label for label, value in values.items() if value == ""]
        placeholders = [label for label, value in values.items() if value and PLACEHOLDER_VALUE.fullmatch(value)]
        if missing:
            raise ValueError(f"{record_id} missing fields: {', '.join(missing)}")
        if empty:
            raise ValueError(f"{record_id} has empty fields: {', '.join(empty)}")
        if placeholders:
            raise ValueError(f"{record_id} has placeholder fields: {', '.join(placeholders)}")
        if section == "pending" and not PENDING_TYPE.search(markdown):
            raise ValueError(f"{record_id} has invalid type")
        if section == "active" and not any(status in markdown for status in ("Status:`ACTIVE`", "状态:`ACTIVE`")):
            raise ValueError(f"{record_id} must have ACTIVE status")
        if record_id in seen or record_id in removals:
            raise ValueError(f"duplicate operation id: {record_id}")
        seen.add(record_id)
        requires_evidence = requires_evidence or section == "active"
        normalized.append({"id": record_id, "section": section, "markdown": markdown.strip()})
    if not normalized and not removals:
        raise ValueError("operation has no changes")
    if requires_evidence and not (evidence and evidence.strip()):
        raise ValueError("active writes and removals require --evidence")
    return normalized, removals


def validate_records(records: Iterable[dict[str, str]]) -> None:
    _validated_operation(
        {"schema_version": 1, "upsert": list(records), "remove": []},
        evidence="structure validation",
    )


def _render(prefix: str, records: list[str], pending: bool) -> str:
    prefix = re.sub(r"(?m)^\s*_无_\s*$", "", EMPTY_PENDING.sub("", prefix)).strip()
    parts = [part for part in [prefix, *records] if part]
    if pending and not records:
        parts.insert(0, "_none_")
    return "\n\n" + "\n\n".join(parts) + "\n"


def _replace_section(text: str, section: str, prefix: str, records: list[str]) -> str:
    start, end = _section_bounds(text, section)
    return text[:start] + _render(prefix, records, section == "pending") + text[end:]


def _write_temporary(path: Path, text: str) -> Path:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    return temporary


def apply_operation(
    active_path: Path,
    pending_path: Path,
    operation: dict[str, Any],
    evidence: str | None = None,
) -> None:
    upserts, removals = _validated_operation(operation, evidence)
    active_text = active_path.read_text(encoding="utf-8")
    pending_text = pending_path.read_text(encoding="utf-8")
    active, active_prefix = _parse(active_text, "active")
    pending, pending_prefix = _parse(pending_text, "pending")
    active_changed = any(record["section"] == "active" for record in upserts) or any(
        record_id in active for record_id in removals
    )
    pending_changed = any(record["section"] == "pending" for record in upserts) or any(
        record_id in pending for record_id in removals
    )
    records = {**active, **pending}
    missing = [record_id for record_id in removals if record_id not in records]
    if missing:
        raise ValueError(f"requirement ids not found: {', '.join(missing)}")
    for record_id in removals:
        records.pop(record_id)
    for record in upserts:
        existing = records.get(record["id"])
        if existing and existing["section"] != record["section"]:
            raise ValueError(f"cannot move requirement between sections: {record['id']}")
        markdown = record["markdown"]
        if record["section"] == "active" and not any(label in markdown for label in ("Approval evidence:", "批准依据:")):
            lines = markdown.splitlines()
            body = lines[1:]
            while body and not body[0].strip():
                body.pop(0)
            markdown = "\n".join([lines[0], "", f"- Approval evidence:`{evidence.strip()}`", *body]).strip()
        records[record["id"]] = {**record, "markdown": markdown}

    active_blocks = [item["markdown"] for item in records.values() if item["section"] == "active"]
    pending_blocks = [item["markdown"] for item in records.values() if item["section"] == "pending"]
    if active_changed:
        active_text = _replace_section(active_text, "active", active_prefix, active_blocks)
    if pending_changed:
        pending_text = _replace_section(pending_text, "pending", pending_prefix, pending_blocks)
    active_temp = _write_temporary(active_path, active_text) if active_changed else None
    pending_temp = _write_temporary(pending_path, pending_text) if pending_changed else None
    try:
        if active_temp:
            active_temp.replace(active_path)
        if pending_temp:
            pending_temp.replace(pending_path)
    finally:
        if active_temp:
            active_temp.unlink(missing_ok=True)
        if pending_temp:
            pending_temp.unlink(missing_ok=True)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("operation must contain an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    read = subparsers.add_parser("read")
    read.add_argument("--file", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
    read.add_argument("--pending-file", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
    read.add_argument("--id", action="append", required=True, dest="ids")
    read.add_argument("--max-bytes", type=int, default=16384)
    read.add_argument("--format", choices=("json", "markdown"), default="json")
    write = subparsers.add_parser("write")
    write.add_argument("--file", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
    write.add_argument("--pending-file", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
    write.add_argument("--operation", type=Path, required=True)
    write.add_argument("--evidence")
    args = parser.parse_args()
    try:
        if args.command == "read":
            active_ids = [record_id for record_id in args.ids if not record_id.startswith("PENDING-REQ-")]
            pending_ids = [record_id for record_id in args.ids if record_id.startswith("PENDING-REQ-")]
            records = {}
            if active_ids:
                records.update((record["id"], record) for record in select_records(args.file, active_ids, args.max_bytes))
            if pending_ids:
                records.update(read_records(args.pending_file, "pending"))
            selected = [records[record_id] for record_id in args.ids if record_id in records]
            missing = [record_id for record_id in args.ids if record_id not in records]
            if missing:
                raise ValueError(f"requirement ids not found: {', '.join(missing)}")
            payload = json.dumps(selected, ensure_ascii=False, separators=(",", ":"))
            if len(payload.encode("utf-8")) > args.max_bytes:
                raise ValueError("selected requirements exceed byte limit")
            print("\n\n".join(record["markdown"] for record in selected) if args.format == "markdown" else payload)
        else:
            apply_operation(args.file, args.pending_file, _load_object(args.operation), args.evidence)
            print(json.dumps({"file": args.file.as_posix(), "pending_file": args.pending_file.as_posix()}))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
