#!/usr/bin/env python3
"""Deterministic trigger, decision-package, and output gate for NotebookLM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .state_snapshot import decision_hash, metadata, validate_snapshot
except ImportError:  # direct script execution
    from state_snapshot import decision_hash, metadata, validate_snapshot

TRIGGERS = {
    "requirements_conflict",
    "cross_architecture_boundaries",
    "multiple_viable_solutions",
    "two_failed_local_repairs",
    "conflicting_root_cause_evidence",
    "state_behavior_mismatch",
    "new_requirement_or_debt_candidate",
    "milestone_review",
    "high_risk_low_reversibility",
    "user_requested",
}
DECISION_FIELDS = {
    "question": str,
    "target": str,
    "approved_constraints": list,
    "verified_facts": list,
    "failure_signals": list,
    "attempts": list,
    "candidate_solutions": list,
    "hypotheses": list,
    "prohibitions": list,
    "questions": list,
}
OUTPUT_STATUSES = {
    "PROCEED",
    "NEEDS_DECISION",
    "NEEDS_MORE_EVIDENCE",
    "REQUIREMENTS_CONFLICT",
}
OUTPUT_FIELDS = {
    "status": str,
    "confirmed_facts": list,
    "contradictions": list,
    "unverified_hypotheses": list,
    "candidates": list,
    "recommendation": str,
    "next_step": dict,
    "stop_conditions": list,
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def validate_decision(decision: dict[str, Any], max_bytes: int = 32768) -> list[str]:
    reasons = []
    size = len(json.dumps(decision, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if size > max_bytes:
        reasons.append("decision_package_too_large")
    for field, expected in DECISION_FIELDS.items():
        value = decision.get(field)
        if not isinstance(value, expected) or (expected is str and not value.strip()):
            reasons.append(f"decision_{field}_invalid")
    facts = decision.get("verified_facts", [])
    if not facts or any(
        not isinstance(item, dict) or not item.get("fact") or not item.get("evidence")
        for item in facts
    ):
        reasons.append("verified_facts_without_evidence")
    attempts = decision.get("attempts", [])
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("experiment"), str)
        or not item["experiment"].strip()
        or not isinstance(item.get("result"), dict)
        or item["result"].get("status") != "failed"
        or not isinstance(item["result"].get("summary"), str)
        or not item["result"]["summary"].strip()
        or not isinstance(item.get("evidence"), dict)
        or not isinstance(item["evidence"].get("command"), str)
        or not item["evidence"]["command"].strip()
        or not isinstance(item["evidence"].get("exit_code"), int)
        or not isinstance(item["evidence"].get("pointer"), str)
        or not item["evidence"]["pointer"].strip()
        for item in attempts
    ):
        reasons.append("attempt_evidence_invalid")
    return sorted(set(reasons))


def evaluate(
    root: Path,
    snapshot_path: Path,
    requirements_path: Path,
    decision: dict[str, Any],
    triggers: list[str],
    max_bytes: int = 32768,
    pending_path: Path = Path("docs/PENDING-REQUIREMENTS.md"),
) -> dict[str, Any]:
    reasons = validate_decision(decision, max_bytes)
    unknown = sorted(set(triggers) - TRIGGERS)
    if unknown:
        reasons.append("unknown_triggers")
    if not triggers:
        reasons.append("notebook_trigger_missing")
    if "two_failed_local_repairs" in triggers:
        attempts = decision.get("attempts", [])
        experiments = {
            item.get("experiment", "").strip()
            for item in attempts
            if isinstance(item, dict) and isinstance(item.get("experiment"), str)
        }
        if len(attempts) < 2 or len(experiments) < 2:
            reasons.append("two_failed_repairs_not_evidenced")
    if "multiple_viable_solutions" in triggers and len(decision.get("candidate_solutions", [])) < 2:
        reasons.append("multiple_solutions_not_evidenced")
    if "conflicting_root_cause_evidence" in triggers and len(decision.get("hypotheses", [])) < 2:
        reasons.append("conflicting_hypotheses_not_evidenced")
    snapshot = validate_snapshot(root, snapshot_path, requirements_path, pending_path)
    if not snapshot["ok"]:
        reasons.append("state_snapshot_stale")
    snapshot_decision_hash = metadata(snapshot_path.read_text(encoding="utf-8")).get(
        "decision_hash"
    )
    if snapshot_decision_hash != decision_hash(decision):
        reasons.append("decision_snapshot_mismatch")
    return {
        "allowed": not reasons,
        "mode": "cold_loop" if not reasons else "hot_loop",
        "triggers": sorted(set(triggers)),
        "reasons": sorted(set(reasons)),
        "snapshot": snapshot,
    }


def validate_notebook_output(output: dict[str, Any]) -> list[str]:
    reasons = []
    for field, expected in OUTPUT_FIELDS.items():
        value = output.get(field)
        if not isinstance(value, expected) or (expected is str and not value.strip()):
            reasons.append(f"output_{field}_invalid")
    if output.get("status") not in OUTPUT_STATUSES:
        reasons.append("output_status_invalid")
    candidates = output.get("candidates", [])
    if len(candidates) > 3:
        reasons.append("too_many_candidates")
    required_candidate_fields = {"core", "constraints", "risks", "reversibility", "scope", "validation"}
    if any(
        not isinstance(item, dict)
        or not required_candidate_fields.issubset(item)
        or not isinstance(item.get("core"), str)
        or not item["core"].strip()
        or not isinstance(item.get("constraints"), list)
        or not isinstance(item.get("risks"), list)
        or not isinstance(item.get("reversibility"), str)
        or not item["reversibility"].strip()
        or not isinstance(item.get("scope"), list)
        or not isinstance(item.get("validation"), list)
        for item in candidates
    ):
        reasons.append("candidate_contract_invalid")
    facts = output.get("confirmed_facts", [])
    if any(
        not isinstance(item, dict) or not item.get("fact") or not item.get("evidence")
        for item in facts
    ):
        reasons.append("confirmed_fact_evidence_invalid")
    hypotheses = output.get("unverified_hypotheses", [])
    hypothesis_fields = {"hypothesis", "support", "against", "experiment"}
    if any(
        not isinstance(item, dict)
        or not hypothesis_fields.issubset(item)
        or not isinstance(item.get("hypothesis"), str)
        or not item["hypothesis"].strip()
        or not isinstance(item.get("support"), list)
        or not isinstance(item.get("against"), list)
        or not isinstance(item.get("experiment"), str)
        or not item["experiment"].strip()
        for item in hypotheses
    ):
        reasons.append("hypothesis_contract_invalid")
    next_step = output.get("next_step", {})
    if isinstance(next_step, dict) and next_step.get("type") not in {"implementation", "experiment", "decision"}:
        reasons.append("next_step_type_invalid")
    if isinstance(next_step, dict) and (
        not isinstance(next_step.get("value"), str) or not next_step["value"].strip()
    ):
        reasons.append("next_step_value_invalid")
    if "confirmed_root_cause" in output:
        reasons.append("final_root_cause_forbidden")
    serialized = json.dumps(output, ensure_ascii=False).lower()
    if any(phrase in serialized for phrase in ("最终根因", "confirmed root cause", "root cause is")):
        reasons.append("final_root_cause_forbidden")
    return sorted(set(reasons))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "assert-allowed"):
        command = subparsers.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--snapshot", type=Path, required=True)
        command.add_argument("--requirements", type=Path, default=Path("docs/REQUIREMENTS-SPEC.md"))
        command.add_argument("--pending", type=Path, default=Path("docs/PENDING-REQUIREMENTS.md"))
        command.add_argument("--decision", type=Path, required=True)
        command.add_argument("--trigger", action="append", default=[])
        command.add_argument("--max-bytes", type=int, default=32768)
    output = subparsers.add_parser("validate-output")
    output.add_argument("--response", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate-output":
            reasons = validate_notebook_output(_load(args.response))
            result = {"valid": not reasons, "reasons": reasons}
            print(json.dumps(result, ensure_ascii=False))
            if reasons:
                raise SystemExit(3)
        else:
            result = evaluate(
                args.root,
                args.snapshot,
                args.requirements,
                _load(args.decision),
                args.trigger,
                args.max_bytes,
                args.pending,
            )
            print(json.dumps(result, ensure_ascii=False))
            if args.command == "assert-allowed" and not result["allowed"]:
                raise SystemExit(3)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
