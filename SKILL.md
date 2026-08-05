---
name: notebooklm-iteration-loop
description: >
  Iterate projects efficiently with CodeGraph, Codex, and NotebookLM. Maintain approved
  requirements, project-state snapshots, deterministic quality gates, local code queries,
  bounded multi-agent orchestration, and a conditional NotebookLM cold loop. Use for
  initialization, iterations, bounded parallel work, planning, notebook hygiene, complex
  root-cause or architecture decisions, and constrained scans or model usage.
---

# Efficient CodeGraph + Codex + NotebookLM Iteration

Goal: deterministic facts, local queries, minimal changes, and verified closure. NotebookLM is a low-frequency strategy layer only.

## Invariants

1. Fact order: runtime/tests/build → current code and Git → CodeGraph → `PROJECT-STATE`; lower-order evidence cannot rewrite higher-order evidence.
2. Specification order: explicit user approval → `REQUIREMENTS-SPEC` → current contract; existing code and tests cannot turn a deviation into a requirement.
3. NotebookLM does not decide code facts, root cause, requirement approval, or quality. Its output is only a hypothesis to verify.
4. NotebookLM has exactly two persistent sources: approved `REQUIREMENTS-SPEC` and the runtime `PROJECT-STATE` snapshot.
5. Pending work exists only in local `PENDING-REQUIREMENTS.md`; never upload, implement, or add it to the approved-requirements source.
6. Agents may read only the allow-list in `.iteration/context.json`; every round is bounded by budget/usage and `iteration_gate.py`.
7. The primary agent retains authority for requirement approval, conflict resolution, joint verification, state, commit, and push. Workers never call NotebookLM.
8. Do not initialize CodeGraph automatically, upload raw logs, or claim savings without a `token-usage --all` A/B measurement.
9. Deleting sources, overwriting user work, and remote merge/history rewrite require separate authorization. Do not commit `.iteration` runtime state by default. Only explicit user authorization to “commit iteration state” permits non-sensitive state, decisions, controlled evidence, and execution packets; never commit cookies, tokens, browser storage, lock files, temporary credentials, or raw sensitive logs.
10. `.kiro/specs/` is a post-hoc alignment record only; it is not authoritative for requirements, design, planning, or implementation.
11. Every user task must first bind to a request intake; an empty Pending file alone never proves approval.
12. Documents are UTF-8 without BOM. On Windows PowerShell 5.1, always read with `Get-Content -Encoding UTF8`; never write back text decoded by the ANSI default.
13. At the end of every completed iteration, reconcile NotebookLM Notes: retain only an explicitly useful current note, otherwise delete it or mark it `Completed` with the iteration ID and closure evidence. Archive the compact decision/evidence record locally; do not leave open-ended planning Notes behind.
14. NotebookLM interaction is budgeted: keep the hot loop local; after a cold trigger, use one primary caller, reuse unchanged snapshots/reports, poll only an active exact task ID at bounded intervals, and never issue redundant or immediate retries. On rate-limit evidence, record it and back off.

## Request-intake gate

This gate precedes the Git start gate, CodeGraph exploration, context compilation, dispatch, and code changes.

1. Store the exact current user request in local `.iteration/request.txt` (do not commit or upload it), then copy `templates/REQUIREMENTS-INTAKE.json` to `.iteration/intake-decision.json`.
2. Classify only as:
   - `active`: the task is fully covered by existing active `REQ-*`; list every ID.
   - `pending`: a new, revised, removed, or fixed requirement, or any unresolved goal, scope, non-goal, acceptance criterion, or assumption.
   - `approved`: the current message explicitly approves a previously shown Pending item; bind it to the prior intake.
3. For `pending`, write the complete Pending record with `requirements_store.py write`, then create intake:

```text
python <skill>/scripts/requirements_intake.py build \
  --request-file .iteration/request.txt \
  --decision .iteration/intake-decision.json \
  --intake-file .iteration/intakes/INTAKE-ID.json
```

Show the Pending ID, specification draft, and `draft_sha256` verbatim, then end the turn; only request approval, revision, or rejection. Do not start work, create a contract, dispatch an agent, call NotebookLM, write a Kiro record, or change business code. A `pending` build exits `3`, meaning “recorded but unapproved”; this is an expected stop and must not be bypassed by retrying.

4. On approval, atomically promote and remove Pending with `requirements_store.py write --evidence "<approval quote>"`. An `approved` intake binds the shown draft with `--previous-intake <prior intake>`. Ambiguous assent, an unseen draft, a missing prior intake, or missing approval text cannot promote it.
5. After `active` or `approved` intake, run:

```text
python <skill>/scripts/requirements_gate.py assert-task-executable \
  --file docs/REQUIREMENTS-SPEC.md --pending-file docs/PENDING-REQUIREMENTS.md \
  --request-file .iteration/request.txt --intake-file .iteration/intakes/INTAKE-ID.json
```

Stop for missing intake, request/hash mismatch, document changes, uncleared Pending items, or an incomplete approval chain. The script cannot read host chat; a primary agent that skips this gate has failed the workflow and cannot substitute an old intake or an empty Pending file.

## Start gate

Check branch, upstream, ahead/behind, and dirty state. For non-`0/0`, detached HEAD, missing upstream, or pre-existing dirty work, obtain a decision to continue on the current baseline. Do not independently pull, merge, rebase, reset, checkout, or stash.

```text
python <skill>/scripts/preflight.py --project-root <repo> --strict
```

See [`references/QUALITY-AND-REQUIREMENTS.md`](./references/QUALITY-AND-REQUIREMENTS.md) for approval and quality details.

## Default hot loop

1. The request intake has passed `assert-task-executable`. On the first round run `iteration_budget.py init` and `iteration_budget.py init-usage` to create `.iteration/budget.json` and `.iteration/usage.json`; update usage from actual tool calls every round.
2. Read only the referenced current contract records with `requirements_store.py read --id REQ-*`; do not bulk-read requirements or history.
3. Create `.iteration/context.json` with explicit requirement/symbol/file/test/modify/constraint entries, then run `iteration_gate.py`. See [`references/CONTEXT-CONTROL.md`](./references/CONTEXT-CONTROL.md).
4. Inspect the controlled diff. Use CodeGraph in order: target symbol → file → direct callers/dependencies → current module. Expand to adjacent modules only when needed. Full-repository analysis is reserved for first use, index faults, material branch/boundary/data-model changes, conflicting facts, or an explicit user request.
5. Run the default multi-agent orchestration gate and create a bounded packet under [`references/MULTI-AGENT-PROTOCOL.md`](./references/MULTI-AGENT-PROTOCOL.md). Parallelize only safe independent waves; otherwise dispatch one bounded worker or work serially. The user may disable or select a backend.
6. Complete one approved objective per round. Do not bundle refactors, optimizations, upgrades, scope expansion, or unrelated files.
7. After structured worker results return, the primary agent reruns target tests, relevant regressions, and applicable typecheck/lint/build/runtime checks. A worker claim or delivery receipt is never success evidence.
8. Update only new facts and state changes. Append history with `archive.py append`; keep raw logs local or in CI.
9. Rerun the requirements/iteration gates. A reviewer is read-only and checks the contract, diff, known failures, and evidence.
10. Only when the user says `execute Kiro backfill` or invokes `$record-kiro-spec`, read and run [`skills/record-kiro-spec/SKILL.md`](./skills/record-kiro-spec/SKILL.md); otherwise skip it.
11. On completed iteration closure, perform the Note reconciliation required by invariant 13 before reporting completion.

Default: local query, local change, local verification, **no NotebookLM call**.

## Multi-agent orchestration

```text
python <skill>/scripts/agent_dispatch.py build --root <repo> \
  --manifest .iteration/dispatch.json \
  --capabilities .iteration/ridge-launch-profiles.json \
  --output-dir .iteration/agents
```

Defaults: `enabled:true`, backend `auto`; order is Ridge Agent's Commune → tmux → host native sub-agent → serial. Fall back only for missing capability, explicit unsupported state, or spawn failure before task acceptance. Never redispatch an accepted task. The primary agent labels each packet `light|medium|complex`; scripts map those to `secondary+low|intermediate+medium|frontier+high`. Deeper reasoning requires an explicit override; workers cannot self-escalate. For Ridge, first call `ridge_list_launch_profiles`, pass the unmodified capability snapshot via `--capabilities`, let the script choose the profile, and recheck revision before spawn. Writing workers run in parallel only when separate worktrees and write/locked-resource sets cannot conflict; shared workspaces serialize. Pass large packets by file path or Ridge stash URI, never full text in messages. Keep delivery, terminal acceptance, agent ACK, execution result, and primary verification separate. Only results with matching baseline/packet/result hashes and complete verification evidence can enter joint verification. Discover Ridge connectivity, models, and launch options dynamically from the host MCP schema, capability list, and launcher help; never record or guess local ports, tokens, paths, pane IDs, model names, or commands. If Ridge tools are absent, report that fact; never relay through Mycelium.

## NotebookLM cold gate

Only the ten triggers in [`references/HOT-COLD-PROTOCOL.md`](./references/HOT-COLD-PROTOCOL.md) may enter the cold loop. Before login, credential refresh, or NotebookLM CLI execution, use [`skills/refresh-notebooklm-auth/SKILL.md`](./skills/refresh-notebooklm-auth/SKILL.md). The fixed reachable local proxy is `http://127.0.0.1:51081`: provide it to both CLI environment variables and Chrome `--proxy-server`; never configure only one side or change the system proxy.

```text
python <skill>/skills/refresh-notebooklm-auth/scripts/nlm_auth_flow.py launch \
  --proxy http://127.0.0.1:51081 --cdp-port 19222
python <skill>/skills/refresh-notebooklm-auth/scripts/nlm_auth_flow.py status \
  --cdp-url http://127.0.0.1:19222
```

The valid NotebookLM site may currently be `https://notebook.google.com/`; do not infer logged-out state merely because it differs from `notebooklm.google.com`. Authentication extraction may report only success/failure and non-sensitive metadata; never read, print, or commit cookies, tokens, or local credentials.

For deep research, prefer the installed `chatgpt-nlm-research` stdio MCP when `OPENAI_API_KEY` is available:
call `research_start` with `provider="chatgpt"`, poll the returned task ID with `research_status`, then call
`research_import` to add only the persisted report through the local NotebookLM MCP. Use `provider="auto"` only when
quota/rate-limit fallback is desired; it switches to NotebookLM Deep Research only for explicit API quota/limit errors.
The report is a temporary third source and must be removed after the decision is compressed into verified local facts.
If the bridge is unavailable or no API key exists, use the existing NotebookLM Deep Research path below.

Create the decision JSON and state snapshot before calling:

```text
python <skill>/scripts/state_snapshot.py build --root <repo> \
  --state docs/PROJECT-STATE.md --requirements docs/REQUIREMENTS-SPEC.md \
  --pending docs/PENDING-REQUIREMENTS.md --decision .iteration/decision.json
python <skill>/scripts/notebook_gate.py assert-allowed --root <repo> \
  --snapshot .iteration/PROJECT-STATE.snapshot.md --requirements docs/REQUIREMENTS-SPEC.md \
  --pending docs/PENDING-REQUIREMENTS.md \
  --decision .iteration/decision.json --trigger <trigger>
```

Only after the gate passes may the snapshot replace NotebookLM's `PROJECT-STATE` source and be queried. Validate output with `notebook_gate.py validate-output`, then verify against code, CodeGraph, approved requirements, and tests. Never implement or write requirements directly from NotebookLM output.

## Documents

- `REQUIREMENTS-SPEC.md`: active items only; replace the NotebookLM source after approval.
- `PENDING-REQUIREMENTS.md`: local approval surface; never upload.
- `PROJECT-STATE.md`: stable tracked body; `state_snapshot.py` creates the dynamic tail in `.iteration/`.
- `docs/archive/events-YYYY-MM.jsonl`: sharded, append-only, bounded tail; never upload.
- The current contract and `WORKFLOW` remain Markdown; runtime context/decision/snapshot are not a third persistent source.
- `.kiro/specs/`: optional post-hoc alignment copies; never upload to NotebookLM or drive the main workflow backward.

Stop the relevant action for Pending work, a state-snapshot mismatch, insufficient trigger evidence, index contradiction, verification failure, out-of-scope writes, or budget exhaustion.
