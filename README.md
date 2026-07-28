# notebooklm-iteration-loop

A Claude/Codex-compatible Skill that combines CodeGraph code facts, NotebookLM planning, deterministic
verification, and bounded local history.

## Token-first loop

- Keep exactly two persistent NotebookLM sources: approved `REQUIREMENTS-SPEC` and `PROJECT-STATE`.
- Reuse the stable `PROJECT-STATE` baseline; inspect only target symbols, direct impact, and changed files.
- Run a full CodeGraph reconstruction only for missing/broken indexes, architecture/data-model boundaries,
  major branch changes, contradictions, or an explicit request.
- Skip NotebookLM source replacement/query unless `planning_delta` is true: requirement semantics, architecture
  boundary, quality regression, external block, or milestone changed.
- Store completed iteration history in monthly JSONL shards and read only bounded tail/type slices.
- Measure gains with `token-usage --all`; do not claim fixed savings.

CodeGraph indexes are the project owner's decision. This Skill never initializes one automatically.

## Install

```sh
git clone https://github.com/MySetsuna/notebooklm-iteration-loop.git
cp -r notebooklm-iteration-loop ~/.claude/skills/notebooklm-iteration-loop
cp -r notebooklm-iteration-loop/skills/install-notebooklm-mcp ~/.claude/skills/
cp -r notebooklm-iteration-loop/skills/refresh-notebooklm-auth ~/.claude/skills/
cp -r notebooklm-iteration-loop/skills/link-to-doc-library ~/.claude/skills/
```

`install-notebooklm-mcp` installs/authenticates NLM. `refresh-notebooklm-auth` repairs external-CDP auth after
the Google sign-in is complete. `link-to-doc-library` is optional human-only vault linking.

## Runtime path

1. Verify Git freshness and the Pending gate.
2. Read Active requirements, current contract, stable state, and a bounded archive tail.
3. Use `git diff` to classify `planning_delta`; skip CodeGraph for non-code changes.
4. Check `codegraph status`; conditionally sync; use `explore` for target symbols and impact/affected tests only.
5. Implement and run affected checks first; run full applicable checks before completion or when impact is uncertain.
6. Update only the state delta unless the stable architecture changed.
7. Query/replace NotebookLM state only when `planning_delta=true`; append one JSONL history record.

## Layout

```text
SKILL.md                         # short hot path
references/                      # cold-path governance, archive, init, deep research
scripts/archive.py               # append + bounded tail JSONL tool
templates/                       # project-doc scaffold
skills/                          # NLM install/refresh and doc-library companions
```

See [SKILL.md](./SKILL.md) for the operational contract.

## License

MIT — see [LICENSE](./LICENSE).
