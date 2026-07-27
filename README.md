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

## Six hard rules

1. **Architecture facts come from codegraph, never from NotebookLM.** If you need
   to know who calls what, what an edit would blast-radius, or how a flow works —
   query the index, don't ask the notebook.
2. **The notebook holds exactly two persistent sources per project:**
   `REQUIREMENTS-SPEC` (user-approved behavior) and `PROJECT-STATE` (code facts
   and quality telemetry). Replace them in place; never append per-round copies.
   Pending requirements and iteration history stay local in git.
3. **Iterations should be large, rounds few.** A NotebookLM round trip is the
   most expensive step in this loop — batch a well-scoped contract's worth of
   work into one round instead of asking three times for three small pieces.
4. **Empty notes ≡ all visions implemented.** Do not wipe open vision notes
   without code + deterministic proof; `[已实现]` marks count as cleaned.
5. **Normalize vague requirements before coding.** Write them into the single
   local requirements document as Pending. No code, execution contract, or
   NotebookLM sync until the user explicitly approves that exact Pending item.
6. **Quality telemetry is evidence, not a KPI.** Summarize Sonar, coverage, E2E,
   compiler, and test outputs with exit codes and codegraph impact. Never upload
   raw long logs or trust model self-scoring.

## Prerequisites

- A `codegraph` MCP server indexing the target repo (`codegraph init -i` if
  `.codegraph/` doesn't exist).
- A `notebooklm-mcp` server with access to a NotebookLM notebook.
- Python 3 for the bundled read-only preflight and requirement gate scripts.
- (Optional, human-facing) On Windows, the companion skill
  `link-to-doc-library` junctions project `docs/` into a doc library vault
  (e.g. Obsidian). Agents still read repo files for status — never the vault.

## Install

Install the **main skill + both companions**:

```sh
git clone https://github.com/MySetsuna/notebooklm-iteration-loop.git
cp -r notebooklm-iteration-loop ~/.claude/skills/notebooklm-iteration-loop
cp -r notebooklm-iteration-loop/skills/link-to-doc-library \
  ~/.claude/skills/link-to-doc-library
cp -r notebooklm-iteration-loop/skills/install-notebooklm-mcp \
  ~/.claude/skills/install-notebooklm-mcp
```

Claude Code picks them up automatically; invoke by intent ("iterate with
NotebookLM", "install notebooklm mcp", "link docs into the work doc library")
or by name.

- Missing / expired MCP auth → main skill runs
  [`install-notebooklm-mcp`](./skills/install-notebooklm-mcp/SKILL.md)
- After scaffolding `docs/` → idempotent
  [`link-to-doc-library`](./skills/link-to-doc-library/SKILL.md)

## The nine-step loop (summary — full detail in `SKILL.md`)

1. Read active requirements, enforce the Pending gate, then read the contract
   and running log.
2. Develop against the contract, staying inside its constraints.
3. Run applicable compiler, tests, coverage, E2E, and Sonar/lint gates.
4. Refresh codegraph's index and query it to sketch the real architecture.
5. Rewrite the state document with bounded quality telemetry and traceability.
6. Replace only the `PROJECT-STATE` source; replace `REQUIREMENTS-SPEC` only
   after explicit user approval.
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
  REQUIREMENTS-SPEC.md               # one Pending/Active requirements document
  PROJECT-STATE.md                   # current code facts + quality telemetry
  LOG.md                              # append-only cross-iteration log
  iterations/
    README.md                        # naming convention + index table
    CONTRACT-iteration-TEMPLATE.md    # per-round contract template
```

Copy `templates/` into your project's `docs/` and fill in the placeholders.
Then run `link-to-doc-library` so `docs/` is junctioned into the default doc
library (junction name = repo root name).

## Layout

```
SKILL.md                                   # main: notebooklm-iteration-loop
references/QUALITY-AND-REQUIREMENTS.md     # detailed governance and telemetry
scripts/                                   # deterministic preflight + requirement gate
tests/                                     # standard-library script tests
skills/
  install-notebooklm-mcp/SKILL.md          # companion: install/auth notebooklm-mcp
  link-to-doc-library/SKILL.md             # companion: docs → vault junction (human rail)
templates/                                 # project docs scaffold
```

## License

MIT — see [LICENSE](./LICENSE).
