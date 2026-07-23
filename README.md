# notebooklm-iteration-loop

A [Claude Code Skill](https://docs.claude.com/en/docs/claude-code/skills) that turns
**codegraph** (a local tree-sitter/AST code-knowledge-graph) and **NotebookLM**
(via an MCP server, `notebooklm-mcp`) into a repeatable
develop → index → report → plan → archive loop for iterating on a codebase
with an LLM in the loop.

> 中文说明见 [README.zh-CN.md](./README.zh-CN.md)。Full methodology (Chinese) lives in [`SKILL.md`](./SKILL.md).

## Why

Loop engineering: a human defines what "done/good" means and builds the loop.
**codegraph is the architecture ground truth** — a local AST index that answers
"who calls what / what breaks if I change this / how does this flow work" with
facts, not guesses. **NotebookLM is the planner and root-cause analyst** — fed a
small number of curated sources, it proposes direction. Code is written locally.
Verification only trusts **deterministic signals** (compiler, tests, exit codes),
never a model's self-report.

## Three hard rules

1. **Architecture facts come from codegraph, never from NotebookLM.** If you need
   to know who calls what, what an edit would blast-radius, or how a flow works —
   query the index, don't ask the notebook.
2. **The notebook holds exactly one source per project: the state document.**
   Every iteration **overwrites and replaces** it — never append a new source.
   Piling up sources makes NotebookLM cite stale snapshots and conflate them.
   Iteration history (progress reports, NotebookLM's raw guidance, digest
   reports from initial cleanup) is archived **only in git, never uploaded**.
3. **Iterations should be large, rounds few.** A NotebookLM round trip is the
   most expensive step in this loop — batch a well-scoped contract's worth of
   work into one round instead of asking three times for three small pieces.

## Prerequisites

- A `codegraph` MCP server indexing the target repo (`codegraph init -i` if
  `.codegraph/` doesn't exist).
- A `notebooklm-mcp` server with access to a NotebookLM notebook.

## Install

Drop this skill into your Claude Code skills directory:

```sh
git clone https://github.com/MySetsuna/notebooklm-iteration-loop.git
cp -r notebooklm-iteration-loop ~/.claude/skills/notebooklm-iteration-loop
```

Claude Code picks it up automatically; invoke it by describing what you want
("keep iterating on this project with NotebookLM", "sync progress and get the
next step") or by name.

## The nine-step loop (summary — full detail in `SKILL.md`)

1. Read context: this round's contract + the tail of the running log.
2. Develop against the contract, staying inside its constraints.
3. Run deterministic verification (typecheck/tests/lint) — must be all-green.
4. Refresh codegraph's index and query it to sketch the real architecture.
5. Rewrite the **single** state document, `docs/PROJECT-STATE.md`, in place.
6. Replace the one source in the NotebookLM notebook with the new document.
7. Query NotebookLM for next-step priorities with deterministic acceptance
   signals.
8. Adversarially review every suggestion — cross-check citations, verify
   claimed code facts against codegraph, apply first-principles scrutiny —
   before adopting anything.
9. Archive the round and write the next contract.

## Templates

`templates/` has a ready-to-copy scaffold for adopting this in a project:

```
templates/
  WORKFLOW.md                        # per-project adaptation notes
  PROJECT-STATE.md                   # the one document uploaded to NotebookLM
  LOG.md                              # append-only cross-iteration log
  iterations/
    README.md                        # naming convention + index table
    CONTRACT-iteration-TEMPLATE.md    # per-round contract template
```

Copy `templates/` into your project's `docs/` and fill in the placeholders.

## License

MIT — see [LICENSE](./LICENSE).
