#!/usr/bin/env python3
"""Render verified, retrospective Kiro spec records without replacing user content."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MAX_INPUT_BYTES = 65536
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIREMENT_ID = re.compile(r"^REQ-[A-Za-z0-9._-]+$")
NUMBERED_ID = re.compile(r"^\d+(?:\.\d+)*$")
START = "<!-- record-kiro-spec:start -->"
END = "<!-- record-kiro-spec:end -->"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if START in value or END in value:
        raise ValueError(f"{field} contains a reserved marker")
    return value.strip()


def _evidence(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    return [_text(item, field) for item in value]


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict) or record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    spec_name = _text(record.get("spec_name"), "spec_name")
    if not SLUG.fullmatch(spec_name):
        raise ValueError("spec_name must be kebab-case")
    _text(record.get("title"), "title")
    _text(record.get("summary"), "summary")

    requirements = record.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("requirements must be a non-empty list")
    requirement_ids: set[str] = set()
    criterion_ids: set[str] = set()
    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            raise ValueError(f"requirements[{index}] must be an object")
        requirement_id = _text(requirement.get("id"), f"requirements[{index}].id")
        if not REQUIREMENT_ID.fullmatch(requirement_id):
            raise ValueError(f"invalid approved requirement id: {requirement_id}")
        if requirement_id in requirement_ids:
            raise ValueError(f"duplicate requirement id: {requirement_id}")
        requirement_ids.add(requirement_id)
        _text(requirement.get("title"), f"requirements[{index}].title")
        _text(requirement.get("user_story"), f"requirements[{index}].user_story")
        sources = _evidence(requirement.get("evidence"), f"requirements[{index}].evidence")
        if not any("REQUIREMENTS-SPEC.md" in item and "PENDING" not in item for item in sources):
            raise ValueError(f"requirement {requirement_id} lacks approved contract evidence")
        criteria = requirement.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria:
            raise ValueError(f"requirements[{index}].acceptance_criteria must be non-empty")
        for criterion in criteria:
            if not isinstance(criterion, dict):
                raise ValueError("acceptance criterion must be an object")
            criterion_id = _text(criterion.get("id"), "criterion.id")
            if not NUMBERED_ID.fullmatch(criterion_id):
                raise ValueError(f"invalid criterion id: {criterion_id}")
            if criterion_id in criterion_ids:
                raise ValueError(f"duplicate criterion id: {criterion_id}")
            criterion_ids.add(criterion_id)
            _text(criterion.get("when"), f"criterion {criterion_id}.when")
            _text(criterion.get("shall"), f"criterion {criterion_id}.shall")

    implementation = record.get("implementation")
    if not isinstance(implementation, dict):
        raise ValueError("implementation must be an object")
    components = implementation.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("implementation.components must be non-empty")
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("component must be an object")
        _text(component.get("name"), "component.name")
        _text(component.get("responsibility"), "component.responsibility")
        _evidence(component.get("evidence"), "component.evidence")
    verification = implementation.get("verification")
    if not isinstance(verification, list) or not verification:
        raise ValueError("implementation.verification must be non-empty")
    for check in verification:
        if not isinstance(check, dict):
            raise ValueError("verification item must be an object")
        _text(check.get("command"), "verification.command")
        if check.get("exit_code") != 0:
            raise ValueError("only successful verification (exit_code 0) may be recorded")

    tasks = record.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks must be a non-empty list")
    task_ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("task must be an object")
        task_id = _text(task.get("id"), "task.id")
        if not NUMBERED_ID.fullmatch(task_id):
            raise ValueError(f"invalid task id: {task_id}")
        if task_id in task_ids:
            raise ValueError(f"duplicate task id: {task_id}")
        task_ids.add(task_id)
        _text(task.get("description"), f"task {task_id}.description")
        linked = task.get("requirement_ids")
        if not isinstance(linked, list) or not linked:
            raise ValueError(f"task {task_id}.requirement_ids must be non-empty")
        unknown = set(linked) - requirement_ids
        if unknown:
            raise ValueError(f"task {task_id} references unknown requirements: {sorted(unknown)}")
        _evidence(task.get("evidence"), f"task {task_id}.evidence")


def render(record: dict[str, Any]) -> dict[str, str]:
    validate_record(record)
    requirements = [
        "# Requirements Document",
        "",
        "> Retrospective alignment record; not an implementation authority.",
        "",
        f"## {record['title']}",
        "",
        record["summary"],
        "",
    ]
    for number, item in enumerate(record["requirements"], 1):
        requirements += [
            f"### Requirement {number}: {item['title']}",
            "",
            f"**User Story:** {item['user_story']}",
            "",
            "#### Acceptance Criteria",
            "",
        ]
        for criterion in item["acceptance_criteria"]:
            requirements.append(
                f"{criterion['id']}. WHEN {criterion['when']} THE SYSTEM SHALL {criterion['shall']}"
            )
        requirements += [
            "",
            f"**Traceability:** `{item['id']}`; " + "; ".join(item["evidence"]),
            "",
        ]

    design = [
        "# Design Document",
        "",
        "> As-built retrospective record; proposed design is out of scope.",
        "",
        "## Overview",
        "",
        record["summary"],
        "",
        "## Implemented Components",
        "",
    ]
    for component in record["implementation"]["components"]:
        design += [
            f"### {component['name']}",
            "",
            component["responsibility"],
            "",
            "**Evidence:** " + "; ".join(component["evidence"]),
            "",
        ]
    design += ["## Verification", ""]
    for check in record["implementation"]["verification"]:
        design.append(f"- `{check['command']}` — exit code `0`")
    design.append("")

    tasks = [
        "# Implementation Plan",
        "",
        "> Retrospective completion record; contains no work authorization.",
        "",
    ]
    for task in record["tasks"]:
        tasks += [
            f"- [x] {task['id']}. {task['description']}",
            f"  - Requirements: {', '.join(task['requirement_ids'])}",
            f"  - Evidence: {'; '.join(task['evidence'])}",
        ]
    tasks.append("")
    return {
        "requirements.md": "\n".join(requirements),
        "design.md": "\n".join(design),
        "tasks.md": "\n".join(tasks),
    }


def _managed(content: str) -> str:
    return f"{START}\n{content.rstrip()}\n{END}\n"


def merge_managed(existing: str, content: str) -> str:
    starts, ends = existing.count(START), existing.count(END)
    if starts != ends or starts > 1:
        raise ValueError("invalid record-kiro-spec managed markers")
    block = _managed(content)
    if starts == 1:
        prefix, remainder = existing.split(START, 1)
        _, suffix = remainder.split(END, 1)
        return f"{prefix}{block}{suffix.lstrip(chr(10))}"
    if not existing.strip():
        return block
    return f"{existing.rstrip()}\n\n{block}"


def build(root: Path, record: dict[str, Any]) -> list[Path]:
    rendered = render(record)
    root = root.resolve()
    target = (root / ".kiro" / "specs" / record["spec_name"]).resolve()
    if root not in target.parents:
        raise ValueError("target escapes project root")
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, content in rendered.items():
        path = target / name
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        updated = merge_managed(existing, content)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(updated, encoding="utf-8", newline="\n")
        temporary.replace(path)
        written.append(path)
    return written


def load_record(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("input must contain a JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    record = load_record(args.input)
    validate_record(record)
    if args.command == "build":
        paths = [path.relative_to(args.root.resolve()).as_posix() for path in build(args.root, record)]
        print(json.dumps({"written": paths}, ensure_ascii=False))
    else:
        print(json.dumps({"valid": True, "spec_name": record["spec_name"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
