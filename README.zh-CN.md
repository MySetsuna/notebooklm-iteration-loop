# notebooklm-iteration-loop

一个 [Claude Code Skill](https://docs.claude.com/en/docs/claude-code/skills),
把 **codegraph**(本地 tree-sitter/AST 代码知识图谱)与 **NotebookLM**
(经由 `notebooklm-mcp` 接入)组合成一条可复用的
「开发 → 索引 → 报告 → 规划 → 归档」闭环,供 LLM 参与的项目持续迭代使用。

> English overview: [README.md](./README.md)。完整方法论见 [`SKILL.md`](./SKILL.md)(本仓库的核心)。

## 为什么

Loop engineering:人负责定义「done/good」并搭循环。**codegraph 是架构真相源**——
本地 AST 索引,回答「谁调谁 / 改这个会炸什么 / 这条流怎么走」给的是代码事实,不是猜测。
**NotebookLM 是规划器 + 根因分析器**——喂给它少而精的来源,由它给出方向。代码由本地
开发环写。验证只认**确定性信号**(编译器/测试/退出码),不靠模型自述。

## 六条硬规矩

1. **架构事实来自 codegraph,不来自 NotebookLM**。想知道谁调谁、改动会炸什么、
   流程怎么走,查索引,别问笔记本。
2. **笔记本里每个项目恒为 2 份常驻来源**:`REQUIREMENTS-SPEC`(用户批准需求)与
   `PROJECT-STATE`(代码事实+质量遥测)。均覆盖替换,不按轮追加；Pending 与迭代历史只留 git。
3. **迭代要大,轮次要少**。NotebookLM 往返是本循环最贵的一步——能在一轮合同里
   规划完的工作,不要拆成三轮问三次。
4. **Notes 清空 ≡ 愿景全实现**。未代码落地禁止抹 notes;可用 `[已实现]` 标记视同清理。
5. **模糊需求先范式化、后审批**。只写单一需求文档 Pending；用户明确批准前禁写对应代码、
   生成执行合同或同步 NotebookLM。
6. **质量遥测是证据,不是 KPI**。Sonar/Coverage/E2E/编译器/测试只传有界摘要、退出码与
   codegraph 影响；不上传长日志，不信模型自评分。

## 前置条件

- 已为目标仓库建好索引的 `codegraph` MCP server(`.codegraph/` 不存在则先
  `codegraph init -i`)。
- 能访问目标笔记本的 `notebooklm-mcp` server。
- Python 3(运行只读 preflight 与需求闸脚本)。
- (可选,人轨)Windows + 配套 skill `link-to-doc-library`,把项目 `docs/` junction
  进文档库供 Obsidian 浏览;agent 查现状仍读仓库文件,不经 vault。

## 安装

克隆后放进 skills 目录(**主 skill + 两个配套**都要装):

```sh
git clone https://github.com/MySetsuna/notebooklm-iteration-loop.git
cp -r notebooklm-iteration-loop ~/.claude/skills/notebooklm-iteration-loop
cp -r notebooklm-iteration-loop/skills/link-to-doc-library \
  ~/.claude/skills/link-to-doc-library
cp -r notebooklm-iteration-loop/skills/install-notebooklm-mcp \
  ~/.claude/skills/install-notebooklm-mcp
```

Claude Code 会自动发现 skill;用自然语言描述意图即可触发(如「用 NotebookLM
持续迭代这个项目」「装 notebooklm mcp」「把 docs 连入工作文档库」),或直接按名调用。

- MCP 未装/认证失效 → 主 skill 触发
  [`install-notebooklm-mcp`](./skills/install-notebooklm-mcp/SKILL.md)
- 脚手架 / 初始化后 → 幂等触发
  [`link-to-doc-library`](./skills/link-to-doc-library/SKILL.md)

## 一次迭代的九步(摘要,完整版见 `SKILL.md`)

1. 读 Active 需求并过 Pending 闸，再读本轮合同与工作日志。
2. 按合同开发,不越界。
3. 跑适用的编译、测试、coverage、E2E、Sonar/lint 闸——必须全绿。
4. 刷新 codegraph 索引并检索,勾勒真实架构。
5. 覆盖式重写 `PROJECT-STATE.md`，写入有界质量遥测与追踪。
6. 替换 `PROJECT-STATE`；`REQUIREMENTS-SPEC` 仅在用户批准后替换。
7. 向 NotebookLM 要下一步计划(附确定性验收信号)。
8. 对每条建议做对抗评审——核对引用、用 codegraph 校验代码事实、用第一性原理检验——
   再决定采纳。
9. 归档本轮,落下一份合同。

## 模板骨架

`templates/` 提供可直接套用的目录骨架:

```
templates/
  WORKFLOW.md                        # 本项目的适配说明(填空)
  REQUIREMENTS-SPEC.md               # 单一 Pending/Active 需求规范
  PROJECT-STATE.md                   # 代码事实 + 质量遥测
  LOG.md                              # 跨迭代 append-only 日志模板
  iterations/
    README.md                        # 命名规范 + 索引表
    CONTRACT-iteration-TEMPLATE.md    # 每轮合同模板
```

把 `templates/` 拷进项目的 `docs/`,填掉占位符即可使用。拷贝后应触发
`link-to-doc-library`,将 `docs/` 联入默认文档库(仓库名作 junction 名)。

## 仓库内 skill 布局

```
SKILL.md                                   # 主 skill:notebooklm-iteration-loop
references/QUALITY-AND-REQUIREMENTS.md     # 需求/质量详规
scripts/                                   # preflight + 需求闸
tests/                                     # 标准库脚本测试
skills/
  install-notebooklm-mcp/SKILL.md          # 配套:安装/认证 notebooklm-mcp
  link-to-doc-library/SKILL.md             # 配套:docs → 文档库 junction(人轨 vault)
templates/                                 # 项目 docs 脚手架
```

## License

MIT,见 [LICENSE](./LICENSE)。
