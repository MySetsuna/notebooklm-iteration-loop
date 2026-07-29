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
- Compile `.iteration/context.json` before exploration; Agent may read only listed files, symbols, tests, constraints.
- Enforce explicit entries, allowed write paths, no full scan/background recap, and exploration/CodeGraph/file/retry/token limits with `iteration_gate.py`.
- NotebookLM emits hypothesis/risk/candidate/question only; CodeGraph, contract, and tests decide implementation.
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
3. Copy `templates/ITERATION-BUDGET.json` to `.iteration/budget.json`.
4. Compile `.iteration/context.json` with explicit `--symbol`, `--file`, `--test`, and `--modify` entries.
5. Run `iteration_gate.py`; it rejects full scans, missing entries, unlisted reads, unlisted writes, background recaps,
   and budget overruns. Gate failure stops the iteration.
6. Classify `planning_delta`; only then use CodeGraph targeted queries. Never let exploration expand the context package.
7. Implement only within the write set; run affected checks first, then all applicable checks when required.
8. Reviewer checks contract, context, diff, failed knowledge, and evidence; Reviewer does not edit code.
9. Update only the state delta, query/replace NotebookLM only when `planning_delta=true`, then append JSONL history.

Full reconstruction requires an explicit trigger: missing/broken index, architecture or data-model boundary change,
major branch change, contradictory facts, or explicit owner request.

## Layout

```text
SKILL.md                         # short hot path
references/                      # cold-path governance, archive, init, deep research
scripts/archive.py               # append + bounded tail JSONL tool
scripts/context_compiler.py      # task-scoped minimal context package
scripts/iteration_budget.py       # iteration budget checker
scripts/iteration_gate.py         # hard scope and budget gate
templates/ITERATION-BUDGET.json  # default per-iteration limits
templates/                       # project-doc scaffold
skills/                          # NLM install/refresh and doc-library companions
```

See [SKILL.md](./SKILL.md) for the operational contract.

## License

MIT — see [LICENSE](./LICENSE).
