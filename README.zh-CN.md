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

## 三条硬规矩

1. **架构事实来自 codegraph,不来自 NotebookLM**。想知道谁调谁、改动会炸什么、
   流程怎么走,查索引,别问笔记本。
2. **笔记本里每个项目恒为 1 份来源:那份状态文档**。每轮**更新并替换**它,不追加。
   来源堆积会让 NotebookLM 引用陈旧快照、张冠李戴。迭代历史(进度报告、NotebookLM
   原文指导、初次整理产出的领域报告)**只进 git 归档,永不上传**。
3. **迭代要大,轮次要少**。NotebookLM 往返是本循环最贵的一步——能在一轮合同里
   规划完的工作,不要拆成三轮问三次。

## 前置条件

- 已为目标仓库建好索引的 `codegraph` MCP server(`.codegraph/` 不存在则先
  `codegraph init -i`)。
- 能访问目标笔记本的 `notebooklm-mcp` server。

## 安装

克隆后放进 Claude Code 的 skills 目录:

```sh
git clone https://github.com/MySetsuna/notebooklm-iteration-loop.git
cp -r notebooklm-iteration-loop ~/.claude/skills/notebooklm-iteration-loop
```

Claude Code 会自动发现该 skill;用自然语言描述意图即可触发(如「用 NotebookLM
持续迭代这个项目」「同步进度取下一步」),或直接按名调用。

## 一次迭代的九步(摘要,完整版见 `SKILL.md`)

1. 读上下文:本轮合同 + 工作日志末尾几条。
2. 按合同开发,不越界。
3. 跑确定性验证(typecheck/测试/lint)——必须全绿。
4. 刷新 codegraph 索引并检索,勾勒真实架构。
5. **覆盖式重写**唯一的状态文档 `docs/PROJECT-STATE.md`。
6. 用新文档替换笔记本里的那唯一一份来源。
7. 向 NotebookLM 要下一步计划(附确定性验收信号)。
8. 对每条建议做对抗评审——核对引用、用 codegraph 校验代码事实、用第一性原理检验——
   再决定采纳。
9. 归档本轮,落下一份合同。

## 模板骨架

`templates/` 提供可直接套用的目录骨架:

```
templates/
  WORKFLOW.md                        # 本项目的适配说明(填空)
  PROJECT-STATE.md                   # 唯一上传 NotebookLM 的文档模板
  LOG.md                              # 跨迭代 append-only 日志模板
  iterations/
    README.md                        # 命名规范 + 索引表
    CONTRACT-iteration-TEMPLATE.md    # 每轮合同模板
```

把 `templates/` 拷进项目的 `docs/`,填掉占位符即可使用。

## License

MIT,见 [LICENSE](./LICENSE)。
