# NotebookLM 迭代工作流(本项目适配说明)

> 通用方法论见仓库根目录 `SKILL.md`。本文件只记录**本项目**的落地细节,克隆模板后按需填写。

## Git 新鲜度硬闸

任何 codegraph、Sonar/Coverage、NotebookLM 查询或规划前：

1. `git fetch --prune <upstream-remote>`；
2. 记录当前分支、upstream、两端 SHA、ahead/behind 与 dirty 摘要；
3. clean 且与 upstream `0/0` 方可开始规划；本轮实现产生的受控 diff 可继续只读 impact/测试选择，
   不得借此跳过远端分叉裁定；
4. 禁止 agent 擅自 pull/merge/rebase/reset/checkout/switch/stash。

## 确定性验证命令(本项目的 checker)

- typecheck: `<替换为你的命令,如 pnpm typecheck / mypy .>`
- test: `<替换为你的命令,如 cargo test / pytest>`
- lint: `<替换为你的命令,如 clippy -D warnings / ruff check>`
- coverage: `<命令 + line/branch/changed-code 门槛;无则明确 missing>`
- E2E: `<命令 + 场景;不适用则写理由与等价终态测试>`
- Sonar/quality gate: `<命令;未配置则写替代静态闸与缺口>`

以上必须**全绿**才能进入 NotebookLM 环节(见 `SKILL.md` step 3)。

开工前只读预检:

```text
python <skill>/scripts/preflight.py --project-root <repo> --strict
python <skill>/scripts/requirements_gate.py assert-executable \
  --file docs/REQUIREMENTS-SPEC.md --pending-file docs/PENDING-REQUIREMENTS.md
```

迭代控制层:

- 先用 `context_compiler.py --requirement REQ-*` 生成 `.iteration/context.json`；Agent 只读其中物化的
  需求条目及允许文件、symbol、测试，不整读需求文档。
- 需求读写用 `requirements_store.py read|write`；Pending 置 `PENDING-REQUIREMENTS.md` 且不上传；
  Active/删除须附批准或决定证据。
- 首轮用 `iteration_budget.py init` 与 `init-usage` 生成 `.iteration/budget.json`、`.iteration/usage.json`；
  每轮按实际工具调用更新 usage，再以 `iteration_budget.py check` 检查上限；超限停机。
- 默认 `agent_dispatch.enabled:true`；后端:`auto|ridge|native|tmux|serial`。主 Agent 从模板生成单 Worker
  packet；写任务仅独立 worktree 且写集/独占资源无冲突时并行。Worker 不审批、不扩范围、不调 NLM。
- 主 Agent 标 `light|medium|complex`；Ridge 先取 profile 能力快照，脚本映射 tier/effort 并解析
  typed launch profile。revision 或实际执行配置不符即拒绝；禁固化本机模型与启动参数。
- `auto` 顺序:Ridge → tmux → 宿主 native sub-agent → serial；仅任务接受前失败可降级，
  已接受 packet 不得跨后端重派。
- Ridge 仅作传输：`submit_dispatched`、`terminalAccepted`、`agentAcknowledged` 均非完成；完成须结构化
  result 过 `agent_dispatch.py validate-result`，再由主 Agent 联合验证。
- 跨模块/高风险任务使用 `agent/<task>` 分支；Reviewer 只审合同、diff、失败知识与验证，不改代码；人工提升回主线。

缺共享质量 CLI 时按 `references/QUALITY-AND-REQUIREMENTS.md` 装到用户/本机全局并复检；
不得为此改项目 manifest/lockfile，无法全局满足时显式停下裁定。

## codegraph 索引范围

- 索引根目录:`<repo root>`
- 排除:`<vendor/ / node_modules/ / 生成代码目录等>`
- 首次/索引缺失:由项目所有者决定是否 `codegraph init -i`；日常先 `codegraph status`，仅 pending/
  异常/无 catch-up 时 `codegraph sync`；目标查询用 `codegraph explore`。

## NotebookLM 笔记本

- notebook_id:`<填入>`
- 需求来源名:`REQUIREMENTS-SPEC`(仅用户批准后替换)
- 状态来源名:`PROJECT-STATE`(仅冷闸通过后，以 `.iteration/PROJECT-STATE.snapshot.md` 替换)
- 常驻来源数:`2`;其他来源只能临时存在并按 `SKILL.md` 清理
- 冷闸:`state_snapshot.py build` → `preflight.py --require-notebooklm --strict` →
  `notebook_gate.py assert-allowed`

## 目录落点

沿用仓库根目录 `SKILL.md` 的约定;本项目实例见 `docs/`
(`docs/REQUIREMENTS-SPEC.md`、`docs/PENDING-REQUIREMENTS.md`、`docs/PROJECT-STATE.md`、
`docs/archive/`、`docs/iterations/`)。

## 人轨:Obsidian / 文档库

- 配套 skill:`link-to-doc-library`(本方法论仓库 `skills/link-to-doc-library/`)
- 可选对齐 skill:`record-kiro-spec`；仅口令 `执行Kiro补记` 或显式 `$record-kiro-spec` 触发，
  只记录已批准需求与已验证 as-built 实现，不作规划或事实源
- 默认库:`C:\work-specs`(工作文档库)
- 联入源:本项目 `docs/` 绝对路径;junction 名 = 本仓库根目录名
- **真相仍在 git 下 `docs/`**;vault 仅浏览。agent 查现状不读 vault。
- 脚手架或初始化后由 nlm skill 幂等触发联入;未联入时可手动说「把本项目 docs 连入工作文档库」。
