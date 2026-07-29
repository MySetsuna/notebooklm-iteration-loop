import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archive  # noqa: E402


class TokenWorkflowTests(unittest.TestCase):
    def test_hot_skill_is_routed_and_incremental(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("planning_delta", skill)
        self.assertIn("仅 status 显示 pending/异常", skill)
        self.assertIn("不自动 `codegraph init`", skill)
        self.assertIn(".iteration/context.json", skill)
        self.assertIn("iteration_budget.py", skill)
        self.assertIn("iteration_gate.py", skill)
        self.assertIn("hypothesis", skill)
        self.assertIn("Reviewer", skill)
        self.assertNotIn("codegraph_context", skill)
        self.assertNotIn("codegraph_trace", skill)
        self.assertNotIn("docs/LOG.md", skill)

    def test_templates_keep_current_truth_and_drop_markdown_history(self):
        state = (ROOT / "templates" / "PROJECT-STATE.md").read_text(encoding="utf-8")
        workflow = (ROOT / "templates" / "WORKFLOW.md").read_text(encoding="utf-8")
        self.assertIn("稳定架构基线", state)
        self.assertIn("本轮 delta", state)
        self.assertIn("docs/archive/", workflow)
        self.assertFalse((ROOT / "templates" / "LOG.md").exists())
        self.assertTrue((ROOT / "templates" / "ITERATION-BUDGET.json").exists())

    def test_committed_archive_records_match_schema(self):
        path = ROOT / "docs" / "archive" / "events-2026-07.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertGreaterEqual(len(records), 7)
        for record in records:
            archive.validate_record(record)
