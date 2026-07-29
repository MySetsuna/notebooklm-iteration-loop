import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.notebook_gate import evaluate, validate_decision, validate_notebook_output
from scripts.state_snapshot import decision_hash

DECISION = {
    "question": "Which design?",
    "target": "choose storage",
    "approved_constraints": ["keep API"],
    "verified_facts": [{"fact": "two stores exist", "evidence": "codegraph:Store"}],
    "failure_signals": [],
    "attempts": [],
    "candidate_solutions": ["A", "B"],
    "hypotheses": [],
    "prohibitions": ["no migration"],
    "questions": ["which is reversible?"],
}


class NotebookGateTests(unittest.TestCase):
    def _evaluate(self, decision, triggers):
        snapshot = f"<!-- PROJECT_STATE_RUNTIME -->\n- decision_hash:`{decision_hash(decision)}`\n"
        with (
            patch("scripts.notebook_gate.validate_snapshot", return_value={"ok": True}),
            patch("pathlib.Path.read_text", return_value=snapshot),
        ):
            return evaluate(Path("."), Path("state"), Path("req"), decision, triggers)

    def test_default_hot_loop_rejects_notebook_call(self):
        result = self._evaluate(DECISION, [])
        self.assertFalse(result["allowed"])
        self.assertIn("notebook_trigger_missing", result["reasons"])

    def test_allows_evidenced_multi_solution_trigger(self):
        result = self._evaluate(DECISION, ["multiple_viable_solutions"])
        self.assertTrue(result["allowed"])

    def test_two_failed_repairs_requires_two_distinct_evidenced_attempts(self):
        result = self._evaluate(DECISION, ["two_failed_local_repairs"])
        self.assertFalse(result["allowed"])
        decision = {**DECISION, "attempts": [
            {
                "experiment": "A",
                "result": {"status": "failed", "summary": "still red"},
                "evidence": {"command": "test a", "exit_code": 1, "pointer": "log:a"},
            },
            {
                "experiment": "B",
                "result": {"status": "failed", "summary": "still red"},
                "evidence": {"command": "test b", "exit_code": 1, "pointer": "log:b"},
            },
        ]}
        result = self._evaluate(decision, ["two_failed_local_repairs"])
        self.assertTrue(result["allowed"])
        duplicate = {**decision, "attempts": [decision["attempts"][0], decision["attempts"][0]]}
        self.assertIn(
            "two_failed_repairs_not_evidenced",
            self._evaluate(duplicate, ["two_failed_local_repairs"])["reasons"],
        )

    def test_rejects_unstructured_attempt_evidence(self):
        decision = {
            **DECISION,
            "attempts": [{"experiment": "A", "result": "failed", "evidence": "test:a"}],
        }
        self.assertIn("attempt_evidence_invalid", validate_decision(decision))

    def test_rejects_decision_not_embedded_in_snapshot(self):
        with (
            patch("scripts.notebook_gate.validate_snapshot", return_value={"ok": True}),
            patch(
                "pathlib.Path.read_text",
                return_value="<!-- PROJECT_STATE_RUNTIME -->\n- decision_hash:`wrong`\n",
            ),
        ):
            result = evaluate(
                Path("."), Path("state"), Path("req"), DECISION, ["multiple_viable_solutions"]
            )
        self.assertIn("decision_snapshot_mismatch", result["reasons"])

    def test_notebook_output_contract_rejects_final_root_cause(self):
        output = {
            "status": "PROCEED",
            "confirmed_facts": [],
            "contradictions": [],
            "unverified_hypotheses": [],
            "candidates": [],
            "recommendation": "run experiment",
            "next_step": {"type": "experiment", "value": "test"},
            "stop_conditions": ["test fails"],
            "confirmed_root_cause": "guess",
        }
        self.assertIn("final_root_cause_forbidden", validate_notebook_output(output))

    def test_notebook_output_requires_structured_hypothesis(self):
        output = {
            "status": "NEEDS_MORE_EVIDENCE",
            "confirmed_facts": [],
            "contradictions": [],
            "unverified_hypotheses": ["maybe cache"],
            "candidates": [],
            "recommendation": "run experiment",
            "next_step": {"type": "experiment", "value": "disable cache"},
            "stop_conditions": ["signal changes"],
        }
        self.assertIn("hypothesis_contract_invalid", validate_notebook_output(output))


if __name__ == "__main__":
    unittest.main()
