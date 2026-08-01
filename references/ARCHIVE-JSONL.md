# JSONL historical archive

History lives only in `docs/archive/events-YYYY-MM.jsonl`, one independent JSON object per line. Git preserves the history of migrated Markdown; the working tree retains no human-readable duplicate.

Minimal schema:

```json
{"schema_version":1,"id":"unique-id","at":"YYYY-MM-DD","type":"iteration|guidance|ledger|telemetry","facts":["bounded fact"],"evidence":["command/sha/path"],"paths":["relative/path"],"symbols":["symbol"],"next":["next action"]}
```

- `facts` are verified facts, never raw model prose or complete terminal output.
- `evidence` contains only commands, exit codes, hashes, or artifact/CI pointers.
- The caller supplies a stable `id`; a human-readable title is unnecessary.
- Add a rebuildable sidecar for ID lookup only when scale proves it necessary; SQLite and binary indexes are prohibited for now.

Use the standard-library tools supplied by this skill:

```text
python <skill>/scripts/archive.py append --root docs/archive --record <record.json>
python <skill>/scripts/archive.py tail --root docs/archive --limit 5 --type iteration --max-bytes 65536
python <skill>/scripts/archive.py migrate-markdown --root docs/archive --source <old.md> --id <id> --at YYYY-MM-DD --type guidance
```

`tail` reads from the file end within a byte limit; when insufficient, prefer incomplete output to a full archive scan. Migrate once only, delete the former Markdown afterward, and retain its original path and SHA-256 as JSONL evidence.
