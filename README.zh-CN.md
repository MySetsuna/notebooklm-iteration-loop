# notebooklm-iteration-loop

将 CodeGraph 代码事实、NotebookLM 规划、确定性验证与有界本地历史组合为持续迭代 Skill。

## Token 优先

- NotebookLM 常驻仅两源：仅含 Active 的 `REQUIREMENTS-SPEC`、运行时 `PROJECT-STATE` 快照；
  Pending 独立留本地 `PENDING-REQUIREMENTS.md`。
- 复用 `PROJECT-STATE` 稳定基线；仅查目标 symbol、直接影响、changed files。
- 仅索引缺失/损坏、架构或数据模型边界、重大分支变化、事实矛盾、用户明确要求时全量重建。
- 默认热循环不问 NotebookLM；`notebook_gate.py` 仅放行十类有证据的冲突、跨边界、多方案、
  重复失败、里程碑、高风险或用户明确触发。
- 已结束历史写月度 JSONL 分片，仅 tail/type 有界读取。
- 每轮先编译 `.iteration/context.json`，限定 Agent 可读文件、symbol、测试与约束。
- 默认启用有界编排；主 Agent 将精确 Active REQ、CodeGraph 事实、baseline、读写集与验证命令分成
  Worker packet，仅隔离且无冲突波次并行。
- `iteration_gate.py` 再硬验显式入口、允许写集、禁止全图/背景复述；`iteration_budget.py` 限探索、CodeGraph 查询、读文件、重试与 token。
- `state_snapshot.py` 在冷循环前核对 HEAD 与需求 version/hash；NotebookLM 输出仍须经 CodeGraph、
  获批需求与测试验证。
- 收益只以 `token-usage --all` 同任务 A/B 实测。

CodeGraph 是否建索引由项目所有者决定；本 Skill 不自动 `init`。

## 安装

```sh
git clone https://github.com/MySetsuna/notebooklm-iteration-loop.git
cp -r notebooklm-iteration-loop ~/.claude/skills/notebooklm-iteration-loop
cp -r notebooklm-iteration-loop/skills/install-notebooklm-mcp ~/.claude/skills/
cp -r notebooklm-iteration-loop/skills/refresh-notebooklm-auth ~/.claude/skills/
cp -r notebooklm-iteration-loop/skills/link-to-doc-library ~/.claude/skills/
```

`install-notebooklm-mcp` 负责安装/认证；`refresh-notebooklm-auth` 在外部 CDP 已登录后刷新凭据；
`link-to-doc-library` 仅供人眼文档库联接。

## 最短路径

1. 过 Git 新鲜度、Active/Pending 双文件闸。
2. 读 Active、当前合同、稳定状态、少量 JSONL tail。
3. 复制 `templates/ITERATION-BUDGET.json` 为 `.iteration/budget.json`。
4. 用显式 `--symbol`、`--file`、`--test`、`--modify` 编译 `.iteration/context.json`。
5. 运行 `iteration_gate.py`；其拒绝全图、无入口、越界读、越界写、背景复述与预算超限；失败即停。
6. CodeGraph 只执行显式 symbol/query；文件与测试不自动变图查询。
7. 用 `agent_dispatch.py` 制包；默认依次取 Ridge Agent's Commune、tmux、宿主 native sub-agent、serial，
   任务先标轻/中/复杂，再从宿主实时能力解析启动 profile；传输回执不得算完成。
8. Worker 仅在 packet 写集内改；主 Agent 验 result hash 后重跑适用质量闸。
9. Reviewer 只审合同、context、diff、失败知识与证据，不改代码。
10. 默认留热循环；命中冷闸才生成状态快照、调用 NotebookLM、验输出，再回代码与测试；历史 append JSONL。

全量重建须有明确触发：索引缺失/损坏、架构或数据模型边界变化、重大分支切换、事实矛盾或项目所有者明确要求。

## 布局

```text
SKILL.md                         # 热路径
references/                      # 冷路径规约/归档/初始化/深研
scripts/archive.py               # JSONL append + bounded tail
scripts/context_compiler.py      # 任务限定最小上下文包
scripts/iteration_budget.py      # 迭代预算校验
scripts/iteration_gate.py        # 全图/入口/写集/预算硬闸
scripts/agent_dispatch.py        # Worker 制包、并行与结果回收闸
scripts/requirements_store.py    # Active/Pending 分离的定向读写
scripts/state_snapshot.py        # 运行时 PROJECT-STATE 来源
scripts/notebook_gate.py         # 冷循环触发与输出契约闸
templates/ITERATION-BUDGET.json  # 默认迭代上限
templates/AGENT-DISPATCH.json    # 后端无关派发清单
templates/                       # 项目文档脚手架
skills/                          # NLM 安装/刷新、文档库配套 Skill
```

完整契约见 [SKILL.md](./SKILL.md)。

## License

MIT，见 [LICENSE](./LICENSE)。
