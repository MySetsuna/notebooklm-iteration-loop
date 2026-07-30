import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "record-kiro-spec" / "scripts" / "record_kiro_spec.py"
SPEC = importlib.util.spec_from_file_location("record_kiro_spec", SCRIPT)
record_kiro_spec = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(record_kiro_spec)


def valid_record():
    return {
        "schema_version": 1,
        "spec_name": "verified-feature",
        "title": "Verified Feature",
        "language": "en",
        "recorded_at": "2026-07-30T00:00:00Z",
        "summary": "Approved behavior is implemented.",
        "boundary": {
            "in_scope": ["Verified retrospective record"],
            "out_of_scope": ["Future implementation planning"],
        },
        "requirements": [
            {
                "id": "REQ-010",
                "title": "Retrospective Kiro record",
                "user_story": "As a collaborator, I want a Kiro record for alignment.",
                "acceptance_criteria": [
                    {"id": "1.1", "when": "the explicit trigger is used", "shall": "write verified facts"}
                ],
                "evidence": ["docs/REQUIREMENTS-SPEC.md#REQ-010"],
            }
        ],
        "implementation": {
            "components": [
                {
                    "name": "record_kiro_spec.build",
                    "responsibility": "Writes managed Kiro blocks.",
                    "evidence": ["skills/record-kiro-spec/scripts/record_kiro_spec.py:build"],
                }
            ],
            "verification": [{"command": "python -m unittest", "exit_code": 0}],
        },
        "tasks": [
            {
                "id": "1",
                "description": "Implement verified retrospective export",
                "requirement_ids": ["REQ-010"],
                "evidence": ["skills/record-kiro-spec/scripts/record_kiro_spec.py"],
            }
        ],
    }


class RecordKiroSpecTests(unittest.TestCase):
    def test_build_preserves_existing_content_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / ".kiro" / "specs" / "verified-feature"
            target.mkdir(parents=True)
            requirements = target / "requirements.md"
            requirements.write_text("# Existing Kiro content\n", encoding="utf-8")

            record_kiro_spec.build(root, valid_record())
            first = requirements.read_text(encoding="utf-8")
            record_kiro_spec.build(root, valid_record())
            second = requirements.read_text(encoding="utf-8")

            self.assertEqual(first, second)
            self.assertTrue(second.startswith("# Existing Kiro content"))
            self.assertEqual(second.count(record_kiro_spec.START), 1)
            self.assertIn("## Retrospective Alignment Record", second)
            self.assertIn("WHEN the explicit trigger is used THE SYSTEM SHALL write verified facts", second)
            self.assertIn("- [x] 1.", (target / "tasks.md").read_text(encoding="utf-8"))

    def test_rejects_failed_verification_and_unknown_requirement(self):
        failed = valid_record()
        failed["implementation"]["verification"][0]["exit_code"] = 1
        with self.assertRaisesRegex(ValueError, "only successful verification"):
            record_kiro_spec.validate_record(failed)

        unknown = valid_record()
        unknown["tasks"][0]["requirement_ids"] = ["REQ-404"]
        with self.assertRaisesRegex(ValueError, "unknown requirements"):
            record_kiro_spec.validate_record(unknown)

        pending = valid_record()
        pending["requirements"][0]["id"] = "PENDING-010"
        with self.assertRaisesRegex(ValueError, "invalid approved requirement"):
            record_kiro_spec.validate_record(pending)

    def test_rejects_invalid_slug_and_broken_markers(self):
        record = valid_record()
        record["spec_name"] = "../escape"
        with self.assertRaisesRegex(ValueError, "kebab-case"):
            record_kiro_spec.validate_record(record)
        with self.assertRaisesRegex(ValueError, "managed markers"):
            record_kiro_spec.merge_managed(record_kiro_spec.START, "content")

    def test_uses_local_metadata_convention_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            precedent = root / ".kiro" / "specs" / "existing"
            precedent.mkdir(parents=True)
            (precedent / "spec.json").write_text('{"phase":"implemented"}\n', encoding="utf-8")

            paths = record_kiro_spec.build(root, valid_record())
            metadata = root / ".kiro" / "specs" / "verified-feature" / "spec.json"
            self.assertIn(metadata, paths)
            self.assertIn('"phase": "implemented"', metadata.read_text(encoding="utf-8"))
            original = metadata.read_text(encoding="utf-8")
            record_kiro_spec.build(root, valid_record())
            self.assertEqual(original, metadata.read_text(encoding="utf-8"))
