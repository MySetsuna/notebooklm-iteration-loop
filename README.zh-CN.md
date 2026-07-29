# notebooklm-iteration-loop

将 CodeGraph 代码事实、NotebookLM 规划、确定性验证与有界本地历史组合为持续迭代 Skill。

## Token 优先

- NotebookLM 常驻仅两源：获批 `REQUIREMENTS-SPEC`、`PROJECT-STATE`。
- 复用 `PROJECT-STATE` 稳定基线；仅查目标 symbol、直接影响、changed files。
- 仅索引缺失/损坏、架构或数据模型边界、重大分支变化、事实矛盾、用户明确要求时全量重建。
- 仅 `planning_delta=true`（需求语义、架构边界、质量回归、外部阻塞、里程碑变化）才替换状态源并问
  NotebookLM。
- 已结束历史写月度 JSONL 分片，仅 tail/type 有界读取。
- 每轮先编译 `.iteration/context.json`，限定 Agent 可读文件、symbol、测试与约束。
- `iteration_gate.py` 再硬验显式入口、允许写集、禁止全图/背景复述；`iteration_budget.py` 限探索、CodeGraph 查询、读文件、重试与 token。
- NotebookLM 仅产 hypothesis/risk/candidate/question，CodeGraph、合同与测试裁决实现。
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

1. 过 Git 新鲜度、Pending 闸。
2. 读 Active、当前合同、稳定状态、少量 JSONL tail。
3. `git diff` 判 `planning_delta`；非代码变更不查 CodeGraph。
4. `codegraph status` 后按需 sync；只 `explore` 目标与直接 impact/affected tests。
5. 先受影响测试；完成/不确定时全量适用验证。
6. 边界未变只写状态 delta；`planning_delta=false` 不往返 NotebookLM。
7. append 一条 JSONL 历史。

## 布局

```text
SKILL.md                         # 热路径
references/                      # 冷路径规约/归档/初始化/深研
scripts/archive.py               # JSONL append + bounded tail
scripts/context_compiler.py      # 任务限定最小上下文包
scripts/iteration_budget.py      # 迭代预算校验
scripts/iteration_gate.py        # 全图/入口/写集/预算硬闸
templates/                       # 项目文档脚手架
skills/                          # NLM 安装/刷新、文档库配套 Skill
```

完整契约见 [SKILL.md](./SKILL.md)。

## License

MIT，见 [LICENSE](./LICENSE)。
