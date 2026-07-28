import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive  # noqa: E402


def record(record_id: str, at: str, record_type: str = "iteration"):
    return {
        "schema_version": 1,
        "id": record_id,
        "at": at,
        "type": record_type,
        "facts": [record_id],
        "evidence": ["exit:0"],
        "paths": ["src/example.py"],
        "symbols": ["example"],
        "next": [],
    }


class ArchiveTests(unittest.TestCase):
    def test_append_and_tail_filter_are_reverse_chronological(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive.append_record(root, record("old", "2026-07-01"))
            archive.append_record(root, record("guidance", "2026-08-01", "guidance"))
            archive.append_record(root, record("new", "2026-08-02"))

            result = archive.tail_records(root, limit=2)
            self.assertEqual([item["id"] for item in result], ["new", "guidance"])
            filtered = archive.tail_records(root, limit=2, types={"iteration"})
            self.assertEqual([item["id"] for item in filtered], ["new", "old"])

    def test_tail_does_not_use_full_file_deserialization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "events-2026-07.jsonl"
            path.write_text("\n".join(json.dumps(record(str(i), "2026-07-01")) for i in range(80)) + "\n", encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=AssertionError("full read forbidden")):
                result = archive.tail_records(root, limit=3, max_bytes=4096)
            self.assertEqual([item["id"] for item in result], ["79", "78", "77"])

    def test_schema_and_one_way_markdown_migration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "archive"
            source = Path(temp_dir) / "old.md"
            source.write_text("# Result\n\n- passed\n", encoding="utf-8")
            archive.migrate_markdown(root, source, "legacy", "2026-07-29", "guidance")
            migrated = archive.tail_records(root, limit=1)[0]
            self.assertEqual(migrated["id"], "legacy")
            self.assertIn("git-history:", migrated["evidence"][0])
            with self.assertRaises(ValueError):
                archive.append_record(root, {"id": "missing"})
