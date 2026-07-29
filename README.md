# notebooklm-iteration-loop

A Claude/Codex-compatible Skill that combines CodeGraph code facts, NotebookLM planning, deterministic
verification, and bounded local history.

## Token-first loop

- Keep exactly two persistent NotebookLM sources: approved-only `REQUIREMENTS-SPEC` and a generated
  `PROJECT-STATE` runtime snapshot. Pending stays local in `PENDING-REQUIREMENTS.md`.
- Reuse the stable `PROJECT-STATE` baseline; inspect only target symbols, direct impact, and changed files.
- Run a full CodeGraph reconstruction only for missing/broken indexes, architecture/data-model boundaries,
  major branch changes, contradictions, or an explicit request.
- Default to the hot loop without NotebookLM. `notebook_gate.py` allows only ten evidenced conflict,
  cross-boundary, multi-solution, repeated-failure, milestone, risk, or explicit-user triggers.
- Store completed iteration history in monthly JSONL shards and read only bounded tail/type slices.
- Compile `.iteration/context.json` before exploration; Agent may read only listed files, symbols, tests, constraints.
- Enable bounded orchestration by default. The lead emits per-worker packets with exact Active requirements,
  CodeGraph facts, scope, baseline, and checks; only isolated, conflict-free waves fan out.
- Enforce explicit entries, allowed write paths, no full scan/background recap, and exploration/CodeGraph/file/retry/token limits with `iteration_gate.py`.
- `state_snapshot.py` checks HEAD plus requirement version/hash before a cold-loop call. NotebookLM output remains
  advice until CodeGraph, approved requirements, and deterministic tests verify it.
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

1. Verify Git freshness and the separate Active/Pending gate.
2. Read Active requirements, current contract, stable state, and a bounded archive tail.
3. Copy `templates/ITERATION-BUDGET.json` to `.iteration/budget.json`.
4. Compile `.iteration/context.json` with explicit `--symbol`, `--file`, `--test`, and `--modify` entries.
5. Run `iteration_gate.py`; it rejects full scans, missing entries, unlisted reads, unlisted writes, background recaps,
   and budget overruns. Gate failure stops the iteration.
6. Use only explicit CodeGraph symbol/queries; files and tests do not silently become graph queries.
7. Build `agent_dispatch.py` packets. Use Ridge Agent's Commune, host-native agents, tmux, or serial;
   transport receipts never count as completion.
8. Workers implement only within packet scope; the lead validates result hashes and reruns applicable checks.
9. Reviewer checks contract, context, diff, failed knowledge, and evidence; Reviewer does not edit code.
10. Stay in the hot loop by default. For an evidenced trigger, build a state snapshot, pass `notebook_gate.py`,
   validate NotebookLM output, then return to code/tests. Append only bounded JSONL history.

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
scripts/agent_dispatch.py         # bounded worker packets and result gate
scripts/requirements_store.py     # split Active/Pending targeted access
scripts/state_snapshot.py         # runtime PROJECT-STATE source
scripts/notebook_gate.py          # cold-loop trigger and output contract
templates/ITERATION-BUDGET.json  # default per-iteration limits
templates/AGENT-DISPATCH.json    # backend-neutral dispatch manifest
templates/                       # project-doc scaffold
skills/                          # NLM install/refresh and doc-library companions
```

See [SKILL.md](./SKILL.md) for the operational contract.

## License

MIT — see [LICENSE](./LICENSE).
