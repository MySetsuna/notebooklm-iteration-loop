# notebooklm-iteration-loop · 本仓适配

## 确定性验证

- 需求闸:`python scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md --pending-file docs/PENDING-REQUIREMENTS.md`
- 任务入口闸:`python scripts/requirements_gate.py assert-task-executable --file docs/REQUIREMENTS-SPEC.md
  --pending-file docs/PENDING-REQUIREMENTS.md --request-file .iteration/request.txt
  --intake-file .iteration/intakes/INTAKE-ID.json`
- 单元测试:`python -m unittest discover -s tests -v`
- preflight:`python scripts/preflight.py --project-root . --strict`
- skill 结构:`python <CODEX_HOME>/skills/.system/skill-creator/scripts/quick_validate.py .`
- codegraph:`codegraph status`；本仓索引 ready，日常只作局部查询，禁止 agent 自动重建
- coverage/E2E/Sonar:本仓仅含 skill 文档与两只标准库脚本，当前未配置；由单元测试与 skill validator
  作等价 checker，缺口保留于状态文档。

## CodeGraph

- 根:`<repo>`
- Markdown 不入 AST；Python 脚本与测试可索引。
- 首次:项目所有者决定是否 `codegraph init -i`；日常先 `status`，仅 pending/异常时 `sync`，查询用
  `codegraph explore`。

## NotebookLM

- notebook_id:`2bf9b409-7b68-4e9c-8bb4-66036003e2c3`
- 标题:`基于NotebookLM与codegraph的迭代开发工作流`
- 目标常驻来源:`REQUIREMENTS-SPEC`、`PROJECT-STATE`
- 状态来源文件:`.iteration/PROJECT-STATE.snapshot.md`（仅 NotebookLM 冷闸通过后生成/替换）
- 默认循环:`HOT_LOOP_SKIP_NOTEBOOKLM`
- 删除既有来源前须用户明确同意。
- 交互预算:无冷闸不调用 NLM；每轮单一主调用者，复用未变化快照/报告；只按精确 task ID 有界轮询；限流即记录并退避，不立即重试。

### 深度调研入口

- 首选 MCP:`chatgpt-nlm-research`，工具顺序:`research_start` → `research_status` → `research_import`。
- `research_start` 传 `provider="chatgpt"`、完整 `query` 与本笔记本 `notebook_id`；返回 task ID 后只按该 ID 查询。
- 多个 ChatGPT CDP 页面并存时，先从 `/json/list` 选定登录态 `browser_target_id`，再启动；不得猜测或重复提交。
- `research_status` 完成后将报告落入本地 gitignored 数据目录；`research_import` 仅把报告文件经现有
  `notebooklm-mcp` `source_add(source_type="file", wait=true)` 导入。
- ChatGPT Web quota/rate-limit 时可传 `provider="auto"` 回退 NotebookLM Deep Research；桥接器经 Chrome CDP 复用已登录页面，普通错误不可静默切换。
- NotebookLM 回退仅选 `result_type=5` 报告；临时报告用毕删除，常驻来源仍只保留 `REQUIREMENTS-SPEC` 与 `PROJECT-STATE`。

## 历史

- `docs/archive/events-YYYY-MM.jsonl`：append-only；用 `scripts/archive.py tail` 有界读取。
- 当前合同留 `docs/iterations/`；结束合同、进度、guidance 不留 Markdown 副本。

## Agent 控制层

- 每项任务先生成 request-bound intake；新需求/修订/Fix 或有歧义者写 Pending、展示后停机。
  空 Pending 不证明当前请求已批准；批准须绑定此前 intake、草稿 hash、Pending ID 与批准原话。
- 每轮先生成 `.iteration/context.json`；其 `read_policy.allowed_files`、目标 symbol、测试与约束为 Agent 允许上下文。
- `.iteration/budget.json`、`.iteration/usage.json` 分别由 `iteration_budget.py init`、`init-usage`
  首次生成；后者按实际调用维护。
- `scripts/iteration_gate.py` 硬控显式入口、允许写集、禁止全图/背景复述，并调用预算闸；失败即停。
- `scripts/agent_dispatch.py` 默认制有界 Worker packet；本仓后端优先宿主 native，Ridge 可用
  Agent's Commune；写任务无独立 worktree 时串行。
- Ridge 先取 launch profile 能力快照；任务难度映射 tier/effort，脚本解析实际 profile。
  profile revision 或实际执行配置不符即拒绝；Skill 不固化模型名与宿主参数。
- `auto` 降级序：Ridge → tmux → 宿主 native sub-agent → serial；仅接受前的能力/启动失败可降级，
  已接受 packet 不得跨后端重派。
- Worker result 须匹配 dispatch/packet/baseline/result hash，并带改动路径、验证退出码与
  `token-usage --all` 分项；主 Agent 仍跑联合回归。
- `scripts/notebook_gate.py` 仅十类显式触发放行；`state_snapshot.py` 先校验 HEAD 与需求 version/hash。
- NotebookLM 输出先过结构闸，再由 CodeGraph、合同与测试验证；不得直接决定实现。
- 失败路径写入 `PROJECT-STATE` 的 Known failed approaches；只记录有证据者，避免重复试错。
- 跨模块任务可用 `agent/<task>` 分支；Reviewer 只读审查，人工提升回主线。
- 可选 Kiro 补记仅以 `执行Kiro补记` 或 `$record-kiro-spec` 触发；写入已批准、已落地、已验证事实，
  格式先有界抽样目标仓既有 spec、无先例才用官方三件套；不作设计/规划依据，不进入 NotebookLM 常驻来源。

## 人轨

- `docs/` 经 junction 联入 `C:\work-specs\notebooklm-iteration-loop`。
- agent 只读仓库 `docs/` 与 codegraph，不把 vault 当真相源。
