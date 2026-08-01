import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archive  # noqa: E402
import iteration_budget  # noqa: E402


class TokenWorkflowTests(unittest.TestCase):
    def test_hot_skill_is_routed_and_incremental(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Default hot loop", skill)
        self.assertIn("notebook_gate.py assert-allowed", skill)
        self.assertIn("Do not initialize CodeGraph automatically", skill)
        self.assertIn(".iteration/context.json", skill)
        self.assertIn("iteration_gate.py", skill)
        self.assertIn("assert-task-executable", skill)
        self.assertIn("requirements_intake.py", skill)
        self.assertIn("reviewer", skill)
        self.assertIn("PENDING-REQUIREMENTS.md", skill)
        self.assertIn("agent_dispatch.py", skill)
        self.assertIn("MULTI-AGENT-PROTOCOL.md", skill)
        self.assertNotIn("codegraph_context", skill)
        self.assertNotIn("codegraph_trace", skill)
        self.assertNotIn("planning_delta", skill)
        self.assertNotIn("docs/LOG.md", skill)
        self.assertIn("never relay through Mycelium", skill)
        self.assertIn("ridge_list_launch_profiles", skill)
        self.assertIn("http://127.0.0.1:51081", skill)
        self.assertIn("nlm_auth_flow.py", skill)
        self.assertNotIn("paneId\":\"", skill)
        self.assertIn("execute Kiro backfill", skill)
        self.assertIn("record-kiro-spec", skill)
        self.assertIn("Get-Content -Encoding UTF8", skill)

    def test_markdown_is_strict_utf8_without_mojibake(self):
        mojibake = ("锟斤拷", "鈥攖", "鈹溾攢", "鎵ц", "琛ヨ")
        for path in ROOT.rglob("*.md"):
            with self.subTest(path=path.relative_to(ROOT)):
                raw = path.read_bytes()
                self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
                text = raw.decode("utf-8")
                self.assertNotIn("\ufffd", text)
                for marker in mojibake:
                    self.assertNotIn(marker, text)

    def test_templates_keep_current_truth_and_drop_markdown_history(self):
        state = (ROOT / "templates" / "PROJECT-STATE.md").read_text(encoding="utf-8")
        workflow = (ROOT / "templates" / "WORKFLOW.md").read_text(encoding="utf-8")
        self.assertIn("## 架构边界", state)
        self.assertIn("repository_head", state)
        self.assertIn("本轮 delta", state)
        self.assertIn("docs/archive/", workflow)
        self.assertFalse((ROOT / "templates" / "LOG.md").exists())
        self.assertTrue((ROOT / "templates" / "ITERATION-BUDGET.json").exists())
        self.assertTrue((ROOT / "templates" / "AGENT-DISPATCH.json").exists())
        self.assertTrue((ROOT / "templates" / "AGENT-RESULT.json").exists())
        self.assertTrue((ROOT / "templates" / "REQUIREMENTS-INTAKE.json").exists())
        dispatch = json.loads(
            (ROOT / "templates" / "AGENT-DISPATCH.json").read_text(encoding="utf-8")
        )
        result = json.loads(
            (ROOT / "templates" / "AGENT-RESULT.json").read_text(encoding="utf-8")
        )
        self.assertIn("ridge_capabilities", dispatch)
        self.assertIn("difficulty", dispatch["tasks"][0])
        self.assertIn("model_execution", result)
        kiro_skill = (ROOT / "skills" / "record-kiro-spec" / "SKILL.md").read_text(encoding="utf-8")
        kiro_agent = (ROOT / "skills" / "record-kiro-spec" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn(".kiro/specs/", kiro_skill)
        self.assertIn("allow_implicit_invocation: false", kiro_agent)

    def test_committed_archive_records_match_schema(self):
        path = ROOT / "docs" / "archive" / "events-2026-07.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertGreaterEqual(len(records), 7)
        for record in records:
            archive.validate_record(record)

    def test_usage_initializer_writes_all_zero_metrics(self):
        self.assertEqual(
            iteration_budget.DEFAULT_USAGE,
            {metric: 0 for metric in iteration_budget.METRICS},
        )
