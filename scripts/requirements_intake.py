#!/usr/bin/env python3
"""Bind each task to an auditable requirement-intake and approval decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .requirements_store import read_records
except ImportError:  # direct script execution
    from requirements_store import read_records

SCHEMA_VERSION = 1
MAX_REQUEST_BYTES = 65536
CLASSIFICATIONS = {"active", "pending", "approved"}
INTAKE_ID = re.compile(r"^INTAKE-[A-Za-z0-9._-]+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _text(value: Any, field: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"{field} must be a {'string' if allow_empty else 'non-empty string'}")
    return value.strip()


def _items(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must be an array of non-empty strings")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field} must not contain duplicates")
    return normalized


def _common(decision: dict[str, Any]) -> dict[str, Any]:
    if decision.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    intake_id = _text(decision.get("intake_id"), "intake_id")
    if not INTAKE_ID.fullmatch(intake_id):
        raise ValueError("intake_id must start with INTAKE-")
    classification = _text(decision.get("classification"), "classification")
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"classification must be one of {sorted(CLASSIFICATIONS)}")
    return {
        "schema_version": SCHEMA_VERSION,
        "intake_id": intake_id,
        "classification": classification,
        "summary": _text(decision.get("summary"), "summary"),
        "requirement_ids": _items(decision.get("requirement_ids"), "requirement_ids"),
        "pending_ids": _items(decision.get("pending_ids"), "pending_ids"),
        "approval_reasons": _items(decision.get("approval_reasons"), "approval_reasons"),
        "open_questions": _items(decision.get("open_questions"), "open_questions"),
        "approval_evidence": _text(decision.get("approval_evidence"), "approval_evidence", allow_empty=True),
    }


def _request(path: Path) -> bytes:
    payload = path.read_bytes()
    if not payload or len(payload) > MAX_REQUEST_BYTES:
        raise ValueError(f"request must contain 1..{MAX_REQUEST_BYTES} bytes")
    return payload


def _draft_hash(pending_records: dict[str, dict[str, str]], pending_ids: list[str]) -> str:
    markdown = "\n\n".join(pending_records[item]["markdown"] for item in sorted(pending_ids))
    return _hash_bytes(markdown.encode("utf-8"))


def build_manifest(
    active_path: Path,
    pending_path: Path,
    request_path: Path,
    decision: dict[str, Any],
    previous_intake: Path | None = None,
) -> dict[str, Any]:
    normalized = _common(decision)
    active_records = read_records(active_path, "active")
    pending_records = read_records(pending_path, "pending")
    request_payload = _request(request_path)
    request_text = request_payload.decode("utf-8")
    active_ids = set(active_records)
    current_pending_ids = set(pending_records)
    requirement_ids = normalized["requirement_ids"]
    pending_ids = normalized["pending_ids"]
    classification = normalized["classification"]
    reasons: list[str] = []
    previous_hash = ""
    draft_hash = ""

    unknown_active = sorted(set(requirement_ids) - active_ids)
    if unknown_active:
        reasons.append("active_requirements_missing:" + ",".join(unknown_active))

    if classification == "active":
        if not requirement_ids:
            reasons.append("active_requirement_ids_required")
        if pending_ids or normalized["approval_reasons"] or normalized["open_questions"]:
            reasons.append("active_intake_must_be_resolved")
        if normalized["approval_evidence"]:
            reasons.append("active_intake_approval_evidence_forbidden")
    elif classification == "pending":
        missing_pending = sorted(set(pending_ids) - current_pending_ids)
        if not pending_ids:
            reasons.append("pending_ids_required")
        if missing_pending:
            reasons.append("pending_records_missing:" + ",".join(missing_pending))
        if not normalized["approval_reasons"]:
            reasons.append("approval_reasons_required")
        if normalized["approval_evidence"]:
            reasons.append("pending_approval_evidence_forbidden")
        if pending_ids and not missing_pending:
            draft_hash = _draft_hash(pending_records, pending_ids)
        reasons.append("approval_required")
    else:
        if not requirement_ids:
            reasons.append("approved_requirement_ids_required")
        if not pending_ids:
            reasons.append("approved_pending_ids_required")
        if normalized["approval_reasons"] or normalized["open_questions"]:
            reasons.append("approved_intake_must_be_resolved")
        if not normalized["approval_evidence"]:
            reasons.append("approval_evidence_required")
        elif normalized["approval_evidence"] not in request_text:
            reasons.append("approval_evidence_not_in_request")
        if previous_intake is None or not previous_intake.is_file():
            reasons.append("previous_pending_intake_required")
        else:
            previous = _load(previous_intake)
            previous_hash = _hash_file(previous_intake)
            try:
                previous_common = _common(previous)
            except ValueError:
                reasons.append("previous_pending_intake_invalid")
            else:
                if previous_common["classification"] != "pending":
                    reasons.append("previous_intake_not_pending")
                if previous_common["pending_ids"] != pending_ids:
                    reasons.append("approved_pending_ids_mismatch")
                draft_hash = previous.get("draft_sha256", "")
                if not isinstance(draft_hash, str) or not SHA256.fullmatch(draft_hash):
                    reasons.append("previous_draft_hash_invalid")
        still_pending = sorted(set(pending_ids) & current_pending_ids)
        if still_pending:
            reasons.append("approved_records_still_pending:" + ",".join(still_pending))

    if current_pending_ids and classification != "pending":
        reasons.append("pending_requirements_exist")
    reasons = sorted(set(reasons))
    return {
        **normalized,
        "request_sha256": _hash_bytes(request_payload),
        "requirements_sha256": _hash_file(active_path),
        "pending_sha256": _hash_file(pending_path),
        "draft_sha256": draft_hash,
        "previous_intake_sha256": previous_hash,
        "executable": classification in {"active", "approved"} and not reasons,
        "reasons": reasons,
    }


def inspect_manifest(
    active_path: Path,
    pending_path: Path,
    request_path: Path,
    intake_path: Path,
) -> dict[str, Any]:
    reasons: list[str] = []
    try:
        manifest = _load(intake_path)
        normalized = _common(manifest)
        _request(request_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {"valid": False, "executable": False, "reasons": [str(error)]}
    expected = {
        "request_sha256": _hash_file(request_path),
        "requirements_sha256": _hash_file(active_path),
        "pending_sha256": _hash_file(pending_path),
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            reasons.append(f"{field}_mismatch")
    manifest_reasons = manifest.get("reasons")
    if not isinstance(manifest_reasons, list) or any(not isinstance(item, str) for item in manifest_reasons):
        reasons.append("manifest_reasons_invalid")
        manifest_reasons = []
    declared_executable = manifest.get("executable")
    if not isinstance(declared_executable, bool):
        reasons.append("manifest_executable_invalid")
        declared_executable = False
    expected_executable = normalized["classification"] in {"active", "approved"} and not manifest_reasons
    if declared_executable != expected_executable:
        reasons.append("manifest_execution_inconsistent")
    if normalized["classification"] == "pending" and declared_executable:
        reasons.append("pending_intake_cannot_execute")
    if normalized["classification"] == "pending" and not SHA256.fullmatch(str(manifest.get("draft_sha256", ""))):
        reasons.append("pending_draft_hash_invalid")
    if normalized["classification"] == "approved":
        if not normalized["approval_evidence"]:
            reasons.append("approval_evidence_required")
        elif normalized["approval_evidence"] not in request_path.read_text(encoding="utf-8"):
            reasons.append("approval_evidence_not_in_request")
        if not SHA256.fullmatch(str(manifest.get("draft_sha256", ""))):
            reasons.append("approved_draft_hash_invalid")
        if not SHA256.fullmatch(str(manifest.get("previous_intake_sha256", ""))):
            reasons.append("approved_previous_intake_hash_invalid")
    reasons = sorted(set(reasons))
    return {
        "valid": not reasons,
        "executable": not reasons and declared_executable,
        "classification": normalized["classification"],
        "intake_id": normalized["intake_id"],
        "reasons": reasons or manifest_reasons,
    }


def _write(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "check"):
        child = subparsers.add_parser(command)
        child.add_argument("--file", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
        child.add_argument("--pending-file", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
        child.add_argument("--request-file", type=Path, required=True)
        child.add_argument("--intake-file", type=Path, required=True)
        if command == "build":
            child.add_argument("--decision", type=Path, required=True)
            child.add_argument("--previous-intake", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            manifest = build_manifest(
                args.file,
                args.pending_file,
                args.request_file,
                _load(args.decision),
                args.previous_intake,
            )
            _write(args.intake_file, manifest)
            print(json.dumps(manifest, ensure_ascii=False))
            return 0 if manifest["executable"] else 3
        result = inspect_manifest(args.file, args.pending_file, args.request_file, args.intake_file)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["executable"] else 3
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
