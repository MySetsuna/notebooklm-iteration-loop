---
name: notebooklm-iteration-loop
description: >
  用 codegraph + NotebookLM 驱动一个项目的持续迭代:每轮先用 codegraph 更新索引并检索,勾勒
  真实架构与细节设计 → 据此**更新同一份**项目状态文档 → 替换 NotebookLM 的状态来源 →
  让它结合全部来源给下一步计划 → 对抗评审 → 归档 → 下一轮。当用户想「配合 NotebookLM 持续迭代
  某项目」「基于笔记本来源规划下一步开发」「把当前进度同步 NotebookLM 并要下一步指导」,或要
  初始化/压缩/整理某个笔记本的存量来源与 notes(清掉已实现或无关来源、把未实现规划移入 notes)、
  把模糊需求转为待审批规范、用 Sonar/Coverage/E2E 质量遥测推演需求/债务/重构/Bug、
  检索与补装项目验证依赖时使用。人眼归档浏览经配套 skill
  link-to-doc-library 把 docs 联入 Obsidian 文档库(人轨;agent 不查 vault)。MCP 未装/认证
  失效时先走配套 skill install-notebooklm-mcp。
---

# codegraph + NotebookLM 驱动的迭代循环

把「开发 → 索引 → 报告 → 规划 → 归档」做成一个可复用的闭环。核心思想(loop engineering):
人负责定义「done/good」并搭循环;**codegraph 当架构真相源**(本地 AST 索引,给的是代码事实);
**NotebookLM 当规划器 + 根因分析器**(读少而精的来源给方向);代码由本地开发环写;验证只认
**确定性信号**(编译器/测试/退出码),不靠模型自述。
**Obsidian / 文档库**只作人眼第二脑外壳(junction 浏览),**不是** agent 真相源。

**八条硬规矩(与旧版的区别,别退回去):**
1. **架构事实来自 codegraph,不来自 NotebookLM**。想知道「谁调谁 / 改这个会炸什么 / 这条流怎么走」,
   查索引,别问笔记本。
2. **笔记本里每个项目恒为 2 份常驻来源**:`REQUIREMENTS-SPEC`(用户批准的需求) +
   `PROJECT-STATE`(代码事实与质量遥测)。两者都**更新并替换**,不按轮追加。Pending 需求、
   领域报告、迭代报告、NotebookLM 原文指导只进本地 git,不常驻笔记本。
3. **迭代要大,轮次要少**(见下节)。NotebookLM 往返是本循环最贵的一段;能在**一轮合同**里
   明确规划完的工作,不要拆成三轮去问三次。
4. **Notes 清空 ≡ 愿景全实现**(见下节「Notes 与愿景清理」)。未代码落地的愿景**禁止**从 notes 抹掉;
   文档入账、维护态、用户轨挂起**都不算**实现。
5. **对抗评审尽量不简单驳回(升值落地,2026-07-24 强制)**：对 NotebookLM/深研/用户 note 的建议,
   **禁止**「rejected + 空转」作为默认结局。能改写为**更高价值、可确定性验收**的 Ridge 切片时,
   **必须 reframing 后写入合同并实现**(例:独立 PTY daemon→foreign 生命周期;CRDT 视口→reconnect 策略;
   Agent Center 视觉大改→health/HITL/roster 数据绑定;通用 VNC→LAN 出站 WS PTY)。
   仅当切片仍违反 SSOT/安全/北极星/不可代劳物理边界时,才记 non-goal,并**同时**写替代落地项与验收信号。
   归档须有 **reframe 表**:`原建议 → 更高价值可测切片 → 验收信号 → 采纳/non-goal+替代`。
6. **单轮约 2 个工作日量级真实代码(禁糊弄小迭代,2026-07-24 强制)**：每份
   `CONTRACT-iteration-{N}` 体量须支撑约 **2 个工程师工作日**的真实代码改动(多模块/多验收目标,
   含确定性测)。**禁止**为凑轮次写 trivial 合同、文档-only 轮、或把同一功能拆成十余个空壳迭代。
   「大迭代、少轮次」与「需推进多轮」并存时,**以每轮够大为准**;多轮推进 = 多份大合同串联,
   不是小改动流水线。达不到 2 日量级的零碎项应并入邻近大合同,不得单独开轮充数。
7. **模糊需求先范式化、后审批**：只改本地 `docs/REQUIREMENTS-SPEC.md` 的 Pending 区;
   用户明确批准前禁止写对应业务代码、生成执行合同或上传需求来源。修订亦先 Pending,旧 Active
   继续生效。详见 [`references/QUALITY-AND-REQUIREMENTS.md`](./references/QUALITY-AND-REQUIREMENTS.md)。
8. **质量信号是事实输入,不是 KPI**：Sonar/Coverage/E2E/编译器输出经有界摘要关联 codegraph
   后写入 `PROJECT-STATE`;原始长日志不上传。它们可提出需求/债务/重构/Bug 候选,但新产品行为
   仍须走 Pending→审批;禁止模型自评分。

## 配套 skills(同仓 `skills/`)

本仓库除主 skill 外还有两个**独立**配套 skill。触发时**读对应文件全文并执行**,勿在本文件内联复制步骤。

### install-notebooklm-mcp(MCP 安装/认证)

路径:[`skills/install-notebooklm-mcp/SKILL.md`](./skills/install-notebooklm-mcp/SKILL.md)。
职责:安装 `notebooklm-mcp-cli`、Google cookie 认证(含代理/外部 CDP)、注册到宿主 MCP。

| 时机 | 动作 |
| --- | --- |
| 无 notebooklm-mcp 工具 / `nlm` 不可用 | **先**跑本配套 skill 全流程,成功后再进主环 |
| cookie 过期 / `nlm login --check` 失败 / 调用报未认证 | 按该 skill「重新认证」重跑步骤 3(+5) |
| 用户只说「装 notebooklm mcp / 重新登录」 | 只跑该 skill,不进九步 |

**阻断**:未装妥或未认证时禁止假装执行 `notebook_query` / `source_add` 等。

### link-to-doc-library(人轨 vault)

路径:[`skills/link-to-doc-library/SKILL.md`](./skills/link-to-doc-library/SKILL.md)。
职责唯一:把文件夹 **NTFS junction** 进工作文档库(默认 `C:\work-specs`),供 Obsidian 索引浏览。

| 时机 | 动作 |
| --- | --- |
| **脚手架**:把 `templates/` 拷成项目 `docs/` 之后 | 调 link-to-doc-library,源=`<repo>/docs`,库=默认 |
| **初始化终态**:`docs/PROJECT-STATE.md` 已落盘、笔记本合规之后 | 同上(幂等) |
| **九步开工前**:`docs/` 已在但文档库中尚无对应 junction | 同上补一次 |
| 用户单独说「连入文档库」等 | 直接走 link-to-doc-library,不必进本环 |

**默认入参**:源 = 目标项目 `docs` 绝对路径;库 = 工作文档库;junction 名 = **仓库根目录名**(由配套 skill 命名规则保证,禁止库内名 `docs`)。
**幂等**:已联入同目标 → noop 一句带过,不阻断主环。非 Windows / 无法建 junction → 跳过并记一句,主环继续。

**禁止**:用 Obsidian MCP / vault 检索替代 `PROJECT-STATE`+LOG+codegraph;每轮双写 vault;把 vault 当 agent 现状源。

## 需求与质量治理(按需读 reference)

遇到模糊需求/需求修订、质量工具接入、依赖安装、遥测驱动规划或实现偏离时,**先读全文**
[`references/QUALITY-AND-REQUIREMENTS.md`](./references/QUALITY-AND-REQUIREMENTS.md)。
仓库内两只标准库脚本提供确定性闸:

```text
python <skill>/scripts/preflight.py --project-root <repo> --strict
python <skill>/scripts/requirements_gate.py assert-executable --file docs/REQUIREMENTS-SPEC.md
```

- `preflight.py` 只读探测 CLI、索引、项目原生测试、Sonar/Coverage/E2E 配置;不安装、不改项目。
- `requirements_gate.py` 检测 Pending 与文档结构;退出码非 0 则禁止开发。
- 缺已声明依赖可用既有 lockfile/包管理器做项目级恢复;新增工具、全局安装、系统服务、MCP 注册须授权。
- 质量结果只写有界摘要、相对基线、证据指针与 codegraph 影响;原始日志留本地/CI artifact。

## 迭代粒度:默认「大迭代」(约 2 日工作量)

每轮 NotebookLM 往返(上传状态文档 + query + 归档 + 对抗评审)成本远高于本地多写几个模块。
**故默认把一轮做大**,前提是两条都成立:

- **任务明确**:每个目标都能写出「改哪些文件 / 落哪个层 / 用什么现成件」,而非「探索一下 X」;
- **规划清晰**:每个目标都有**可被编译器/测试/退出码判定**的验收,且目标间依赖顺序已理清。

不满足时**先只做一个「勘察目标」**把它变明确,而不是把模糊目标塞进大合同。

### 体量底线(硬)

- **约 2 个工作日**真实代码量/轮:主线通常跨 2+ 模块或一条完整垂直切片(transport→session→UI 路由等),
  并带**新增/加厚**的确定性测(禁止 mock 掉被测唯一出口后宣称绿)。
- **禁止糊弄小迭代**:单文件润色、只改 markdown、仅 bump 版本、仅改注释/日志文案、无新验收信号的
  「维护态空转」——**不得**单独算作一轮合同完成。
- 用户要求「至少 N 轮」时:交付 **N 份各自够大**的合同串联;不得把 2 日工作拆成 N 个 trivial PR 充数。

实操:
- 一轮合同带 **4–8 个目标**是常态,包含一条主线(占多数工作量)+ 若干可独立验收的支线;
- 目标之间**尽量无强依赖**,某一项触发停机条件时其余仍可继续、不空转一整轮;
- 每个目标独立提交(可回滚),合同内**按序**推进,**全部做完再走 step 4 起的 NotebookLM 环节**;
- 只在真被**外部信息**卡住(需 NotebookLM 定夺方向/根因)时才提前进入往返,不为「汇报进度」而往返;
- 一轮做不完的部分**顺延进下一份合同**,不作为提前往返的理由。

## 何时用

用户表达「用 NotebookLM 持续迭代这个项目 / 同步进度取下一步 / 搭规划归档工作流 / 初始化或整理笔记本存量来源」时。
前置:① `notebooklm-mcp` 能访问目标笔记本——没有工具、装不上、或认证失败时**先触发**
   [`install-notebooklm-mcp`](./skills/install-notebooklm-mcp/SKILL.md),完成后再继续;
   已可用则 `notebook_list` / `nlm login --check` 探活;
② 项目已有 codegraph 索引(`.codegraph/` 不存在则先 `codegraph init -i`);
③(可选,人轨)Windows 下已装/可发现配套 `link-to-doc-library`,用于把 `docs/` 联入 Obsidian 文档库。
开工先跑只读 preflight 与需求闸,再用 `notebook_get` 查验笔记本是否合规(见下节);
不合规则**先初始化,再进迭代**。
若本次会落地或已有 `docs/`,在进入开发前按上节触发一次 link-to-doc-library(幂等)。

## 初始化(笔记本不合规时先做)

**合规 = 常驻来源恒 2 份:`REQUIREMENTS-SPEC` + `PROJECT-STATE`;未批准 Pending 仅在本地,
未转成需求的规划/愿景活在 notes。**
不合规(来源不是这两份 / 缺任一真相源 / 规划散落在来源里)则先走以下流程。
**用户只要求初始化时,做完即停,不往下推迭代。**

1. **codegraph 立事实**:`codegraph sync` 更新索引(索引可疑则 `codegraph index`,首次
   `codegraph init -i`),再用 `codegraph_context` / `codegraph_explore` / `codegraph_trace`
   探明当前真实实现:模块边界、关键符号与调用路径、已落地能力清单——这是逐源分诊的判据。
2. **先立状态来源**:据代码事实写首份 `docs/PROJECT-STATE.md`(结构见九步之 step 5),
   `source_add` 上传、`source_rename` 为 `PROJECT-STATE`,确认入库。
3. **立需求来源**:把明确且仍有效的用户要求范式化到本地 `docs/REQUIREMENTS-SPEC.md`;
   模糊或修订项进 Pending,展示并等用户批准。只将 Active 部分获批的版本上传并命名
   `REQUIREMENTS-SPEC`;批准前不写对应代码、不上传 Pending。
4. **逐来源分诊**:对其余每份来源 `source_get_content` 取原文,对照 codegraph 与 Active 需求归类:
   - **所述内容已实现** → 删(现状事实已由 PROJECT-STATE 承载,留着只会被引旧快照);
   - **偏离项目 / 与项目无关** → 删;
   - **未实现的规划、愿景与展望** → 先 `note(action="create")` 摘录进 notes(标题带原来源名,
     便于溯源),再删;
   - 拿不准,或含仍有效但未入代码的决策理由/坑 → 并入 `PROJECT-STATE.md` 对应章节后再删
     (知识密度高的来源按「存量来源压缩」一节先深挖)。
5. **批量删除**:`source_delete(confirm=true)`。删除不可逆:先确认两份替代来源已入库、
   规划类已落 notes,并**当面向用户确认**再删。
6. **终态**:常驻来源恒 2 份;**未实现**规划全在 notes,未批准需求仅在本地 Pending。
   此后每轮迭代照常走九步;制定 contract 时用 `note(action="list")` 读存量规划作参考
   (notes 不参与 `notebook_query` 的来源检索,取用要靠 note 工具)。
7. **人轨 vault(触发配套 skill)**:`docs/` 已存在则执行 `link-to-doc-library`
   (源=`docs` 绝对路径,库=默认)。失败/非 Windows 不阻断;成功或 noop 一句记入对用户报告即可。

## Notes 与愿景清理(硬规矩,2026-07-24 起强制)

**语义等式(不可破):**

| 笔记本状态 | 含义 |
| --- | --- |
| 存在未标「已实现」的愿景 note 行 | 仍有开放愿景,循环**未完成** |
| 全部开放愿景已**代码实现**并验收,note 已删 **或** 正文/标题标 `[已实现]` | **视同清理**,愿景全实现 |
| `note list` count=0 且无「已实现」档案 note | **仅当** PROJECT-STATE 与 codegraph 证明零开放愿景时才合法;否则必须重建开放清单 |

### 什么叫「代码侧实现」(判据)

同时满足才可标记/清理该愿景:

1. **源码存在**对应能力(codegraph 或精确读文件可指到符号/路径);
2. **确定性验收**通过(测试/退出码/合同闸),不得仅靠文档声明或「用户轨以后再做」;
3. 在 `PROJECT-STATE` 差距表或对账表写明**已实现**及证据指针。

**不算实现:**「已关闭—待用户轨」「设计已定稿未写码」「实验室模拟冒充真机」「仅 LOG 一笔」。

### 清理方式(二选一,等价)

1. **标记视同清理(推荐)**:`note update` 标题加前缀 `[已实现]` 或正文首行 `STATUS: implemented` + 证据链接;
   **不必** `note delete`。开放愿景清单 note 中对应行划入「已实现」段。
2. **物理删除**:仅在该项已满足「代码侧实现」判据后;`delete` 前本地 git 须有全文归档。

**禁止:**

- 因「自动轨做尽 / 维护态 / 用户未回」批量 `note delete` 未实现愿景;
- 把未实现项只写进 PROJECT-STATE「待用户」然后清空 notes;
- 宣称「notes=0 即循环完成」却仍有未落地能力。

### 开放愿景清单(常驻形态)

- 推荐**一份**总清单 note,标题固定如 `开放愿景清单`(可另有专题 note)。
- 每行:`ID | 主题 | 状态(open/implemented) | 验收信号 | 证据`。
- `open` 愿景先转为 `REQUIREMENTS-SPEC` Pending 并获批,才可进入 contract;做完改
  `implemented` 并更新 PROJECT-STATE。
- **纠偏**:若错误清空 notes,从本地归档**立即重建**开放清单,再继续迭代——不得用空 notes 假装完成。

### 原「待用户裁定」项(实现决策可拍板,产品语义不可)

合同或状态里写「待用户 / 用户轨 / 需产品定义」时,**不得无限挂起**,但先分流:

1. **产品行为/验收语义变化** → 写 `REQUIREMENTS-SPEC` Pending,必须用户批准;
2. **纯实现选型且不改变 Active 需求** → 可先 `nlm research`/`notebook_query`,经对抗评审自行拍板,
   写入 contract 与 PROJECT-STATE「锁定决策」;
3. 按已批准需求与锁定实现决策写代码并过确定性闸;
4. 真机/生产凭据/合并发布等**物理不可代劳**项:代码侧做到「可执行脚本 + 假凭据门禁 + 明确手工一步」即算代码愿景闭合;证据槽位留用户,但**不得**因此保留「未实现功能」note——若功能码未写仍算 open。

区分:**缺功能代码** = open 愿景;**功能已有、仅缺人持设备点一次** = 代码愿景可标实现,用户 checklist 另列。

## 一次迭代的九步

1. **读上下文 + 需求闸**:读 `docs/REQUIREMENTS-SPEC.md` Active、本轮
   `docs/iterations/CONTRACT-iteration-{N}.md` 与 `docs/LOG.md` 末尾 5–10 条。运行
   `requirements_gate.py assert-executable`;存在 Pending 则停在审批,不得开发。
2. **开发**:按 contract 优先级实现,受 constraints 约束。别超出本轮范围。
3. **确定性验证 + 质量遥测**:按 `WORKFLOW.md` 跑编译/typecheck、unit/coverage、E2E、
   Sonar/lint 等适用闸。**必须全绿**才算过;记录退出码、相对基线与 evidence pointer。
   未配置的闸写 `missing/not-applicable + 理由`,不得伪称通过。
4. **codegraph 刷新 + 检索勾勒架构**(替代了旧版的「每轮上传一堆文档」):
   - `codegraph sync`(增量;大改动或索引可疑时 `codegraph index`),再 `codegraph_status` 确认节点/边数合理。
   - 用 **MCP 工具**检索,勾勒本轮之后的真实架构与细节:`codegraph_context <本轮主题>` 起手 →
     `codegraph_explore` 一次拿多个关键符号的源码 → 流程用 `codegraph_trace from→to` →
     改动面用 `codegraph_impact`。**别用 grep+read 循环重建索引已有的答案。**
   - 产出是「代码事实」:模块边界、关键符号签名、调用路径、受影响面。写进下一步的状态文档。
5. **更新那唯一一份状态文档** `docs/PROJECT-STATE.md`(路径按项目定,但**全程只此一份**),覆盖式重写,含:
   - 项目是什么 + 不可动摇的设计主线 / 已锁定决策(稳定段,少改);
   - **由 codegraph 勾勒的当前架构**:模块与落点、关键接口签名、关键调用路径、目录现状;
   - **架构图与关键流程图(必备,便于 LLM 与人快速建模)**:至少一张模块/数据流架构图 +
     主链路流程图,用 **mermaid 代码块**(`graph TD`/`sequenceDiagram`,NotebookLM 与多数
     LLM 对 mermaid 文本的理解远好于 ASCII 手绘);图中节点用真实符号/文件名,与 codegraph
     事实一致;**每轮增量更新时图随现状同步改**,过时的图等于错误事实;
   - 本轮做了什么 + 确定性验证证据(命令 + 退出码);
   - 质量遥测有界摘要:验证能力、相对基线、Sonar/Coverage/E2E 信号、证据与 codegraph 影响;
   - Active REQ → 代码符号/路径 → 测试/质量闸追踪;
   - 能力对照(距最终目标差什么)、开放问题、**请 NotebookLM 定夺的具体问题**。
   同时照旧在本地写一份带时间戳的迭代报告 `docs/iterations/{YYYY-MM-DD}-iteration-{N}.md` 作历史存档——
   **它只留在本地仓库,不上传**。
6. **替换 NotebookLM 的状态来源**(需求来源只在审批后另行替换;顺序别反):
   - `source_add(notebook_id, source_type="file", file_path=<PROJECT-STATE.md 绝对路径>, wait=true)`;
   - 确认新来源出现在 `notebook_get` 里之后,再 `source_delete(source_id=<上一版那份>, confirm=true)`;
   - `source_rename` 把新来源命名为稳定名(如 `PROJECT-STATE`),便于下轮定位。
   - 排障期需要 NotebookLM 做根因分析时,可**临时**加 `trace.json`/报错日志,**用完即删**,不占常驻额度。
7. **取下一步计划**:`notebook_query`,让它结合两份真相源给「需求候选/债务/重构/Bug 分类 +
   下一迭代优先级 + 每步**确定性验收信号** + 里程碑地图」。新产品行为只能成为 Pending 候选,
   不得直接进合同。把原文归档为
   `docs/iterations/{YYYY-MM-DD}-notebooklm-guidance-{N}.md`。
8. **对抗评审(关键步,别跳)**:**不要全信 NotebookLM**。它是计划的 *maker*,不是 ground truth——
   它会硬凑不相关的引用、把 app 层的东西塞进底层、给「听起来对」的过度设计。对每条关键建议做独立
   *checker*:①核对它引用的来源**是否真的支撑**该结论(常张冠李戴);②**用 codegraph 对代码事实**
   (它说的这个符号/这层/这条依赖真的存在吗?`codegraph_search`/`codegraph_impact` 一查便知)——
   这是戳穿幻觉建议最快的手段;③用第一性原理检验(这抽象该放哪层?验收信号真的可判吗?);
   ④对高影响/不可逆决策,另起干净上下文(子 agent / 新会话)当**对抗评审员**,专挑反例。
   **默认路径不是驳回**:对每条建议先填 **reframe 表**——能否换成更高价值、落在现有架构上的可测切片?
   能则**必须**写入合同落地;仅当仍违 SSOT/安全/北极星/物理不可代劳时才 non-goal,且须附替代项。
   禁止归档里只写 `rejected` 而无替代落地。把「采纳 / reframed 采纳 / non-goal+替代 + 理由」写进归档。
   **采纳经过检验的部分(含升值切片),不是它说的全部,也不是全盘否定。**
9. **归档 + 落下一份 contract**:据(经对抗评审后的)结论写 `CONTRACT-iteration-{N+1}.md`;在 `docs/LOG.md`
   顶部追加一条本轮记录(做了什么 + 下一步 + 触发的熔断 + 驳回了 NotebookLM 的哪些建议)。
   归档正文**只写 git 下 `docs/`**;人若用 Obsidian 看,靠既有 junction 穿透,无需本步再上传 vault。
   若发现文档库尚未联入本项目 `docs/`,此处**补触发一次** `link-to-doc-library`(幂等),否则跳过。

## 深度调研(遇疑难时的外部信息通道)

迭代中遇到**要探讨的问题或拿不准的方向**(架构选型、外部生态、最佳实践、疑难根因),
不要靠猜,让 NotebookLM 做深度调研:

1. `nlm research start "<问题>" -n <notebook_id> -m deep` 发起(web 深研,约 5 分钟);
   `nlm research status` 轮询至完成。
2. **只把「调研报告」导入为来源,排除全部参考材料**——几十份网页源只会稀释检索、
   引来陈旧引用。若导入无法排除参考材料,导入后立刻 `source_delete` 之,仅留报告一份。
3. 报告是**临时第三来源**:与两份真相源并存,供后续 `notebook_query` 制定合同时引用;
   其建议仍须过对抗评审(step 8),不全信。
4. **相关研究全部在项目中实现(确定性验证通过)后**,先把报告结论
   `note(action="create")` 归档进 notes(标题带日期与主题),再 `source_delete(confirm=true)`
   移除该来源报告。终态回归「常驻来源恒 2 份」。

## 存量来源压缩(初始化分诊的深挖子流程)

老笔记本常有 20–50 个碎片来源,导致引用陈旧、答非所问。初始化分诊中遇到**知识密集型**来源
(大量未入代码的决策理由、接口约束、坑)时,删除前先按本节深挖:

1. `notebook_get` 拿全量来源清单,按标题聚类出 **3–5 个领域**(例:协议/传输、服务端与会话、
   前端与 UI 扩展、Agent 与工具、安全与部署)。
2. 每个领域用 `notebook_query(notebook_id, query, source_ids=[该领域的源])` 做**深入**调研——
   一个领域问多轮(架构、关键接口、约束与坑、未决问题),别一问了事;必要时
   `source_get_content` 拿原文核对。涉及本地代码的部分**用 codegraph 校正**。
3. 每个领域写成一份**深度报告** md(不是摘要:保留接口签名、文件路径、决策理由、反例与坑),
   落到本地 `docs/<notebook>-digest/`——**这只是本地合并素材,不上传、不常驻笔记本**。
4. 把代码事实合并进 `PROJECT-STATE`,把明确用户要求范式化进 `REQUIREMENTS-SPEC` Active/Pending;
   Pending 获批前不上传、不开发。
5. `source_add` 上传合并后的两份真相源并确认入库后,`source_delete(source_ids=[...全部旧来源],
   confirm=true)` **批量删除原有碎片(含压缩阶段查询用的临时来源)**。删除不可逆:先确认新文档
   已成功入库,并**当面向用户确认**再删。
6. 终态:**笔记本内恒为 2 份常驻来源** = `REQUIREMENTS-SPEC` + `PROJECT-STATE`。领域深度报告只留本地 git 存档,
   不再上传或常驻。

## 文件骨架(artifacts / contracts / logs)

```
docs/
  WORKFLOW.md                 # 这个循环在本项目的说明
  REQUIREMENTS-SPEC.md        # ★单一需求规范:Pending 本地审批;Active 批准后替换来源
  PROJECT-STATE.md            # ★单一状态文档:每轮覆盖式更新 + 替换来源
  LOG.md                      # 全局 append-only 工作日志,开工先读末尾几条
  <notebook>-digest/          # 存量来源压缩出的领域深度报告,仅本地存档,不上传/不常驻笔记本
  iterations/
    README.md                 # 命名规范 + 索引表
    CONTRACT-iteration-{N}.md # 每轮合同:目标/边界/可验证验收/停机条件
    {date}-iteration-{N}.md   # 每轮进度报告(仅本地历史存档,不上传)
    {date}-notebooklm-guidance-{N}.md  # NotebookLM 指导 + 对抗评审结论
```

## 不变量(别破坏)

- **架构问 codegraph,方向问 NotebookLM**。前者是代码事实,后者是意见。冲突时以 codegraph 为准。
- **一个项目两份真相文档**:更新+替换,不追加。**笔记本常驻来源恒为 2**
  (`REQUIREMENTS-SPEC` + `PROJECT-STATE`);
  压缩产出的领域报告、每轮进度报告、NotebookLM 原文指导,一律只进本地 git 归档,永不上传。
  唯二额外来源皆**临时**:排障日志(用完即删)与深度调研报告(研究实现完毕即归档 notes 后删,
  见「深度调研」节)。
- **需求审批不可代理**:模糊需求/产品语义修订只进本地 Pending;用户明确批准后才替换需求来源、
  生成合同并改代码。实现选型且不改 Active 语义者方可自行拍板。
- **质量遥测不是自评分**:只认工具输出、退出码、相对基线与证据;原始长日志不上传。
- **规划/愿景不当来源存**:未转成批准需求的规划、愿景、展望记入 notes(`note` 工具);
  常驻来源只承载批准需求与现状事实。已实现旧快照或无关来源,初始化时删。
- **Notes 清空 ≡ 愿景全实现**:未代码落地禁止删 note;可用 `[已实现]` 标记视同清理。详见专节。
- **实现侧判断可代理拍板**:深研 → 对抗评审 → 锁定实现决策;产品需求审批仍由用户完成。
- **Obsidian / 文档库是人轨外壳,不是 agent 真相源**:现状与历史以仓库 `docs/` + codegraph 为准;
  vault 仅经 `link-to-doc-library` junction 浏览同一批文件。禁止 agent 默认走 vault/Obsidian MCP
  查 feat 状态;禁止每轮双写。junction 失败不阻断主环。
- **停机条件写成合同不是愿望**:验收必须能被编译器/测试/退出码客观判定,不写「改进代码」。
- **maker ≠ checker**:生成的东西不给自己打分;验证只认确定性证据。
- **授权阶梯**:默认 Level 2(Draft)——改动在分支/worktree,人做物理验证后合并,不 auto-merge;
  当前级稳定产出「本来就会手动合的」质量,才往上爬一级。
- **每轮留熔断记录**:硬回合上限 / 预算 / 无进展检测触发的情况写进报告,用于判断健壮性。
- **NotebookLM 是 maker 不是裁判**:任何关键决策必须过对抗评审(step 8)再采纳。
- **不简单驳回**:对抗默认 reframing 升值落地;禁止 `rejected` 空转(见硬规矩 5)。
- **约 2 日大迭代**:禁止糊弄小迭代/文档-only 充轮次(见硬规矩 6 与「迭代粒度」)。
- **删除来源不可逆**:`source_delete` 前必须先确认替代来源已入库,并取得用户明确同意。
- 密钥/敏感信息永不上传、永不写日志。

## 关键工具

**codegraph(MCP,架构真相源)**:`codegraph_status` 看索引健康;`codegraph_context <task>` 起手;
`codegraph_explore` 一次看多个符号源码;`codegraph_trace from→to` 追流程(含回调/JSX 动态跳);
`codegraph_impact` 看改动爆炸半径;`codegraph_search` 按名找符号。
CLI:`codegraph sync`(增量刷新)/ `codegraph index`(全量)/ `codegraph init -i`(首次)。

**notebooklm-mcp**:`notebook_list` / `notebook_get`(找笔记本、看来源清单);
`source_add(source_type="file"|"text", ...)`(`file` 需路径对 MCP 服务器可见,否则用 `text` 贴内容);
`source_rename`(给常驻来源稳定名);`source_delete(confirm=true)`(替换旧版/清理碎片);
`source_get_content`(拿来源原文,比 query 快);`notebook_query(notebook_id, query, source_ids=...)`;
`note(notebook_id, action="create"|"list"|"update"|"delete", content=..., title=..., note_id=...,
confirm=...)`(统一 notes 工具:初始化时收纳未实现规划,制定 contract 时 `list` 读取;
delete 需 confirm=true)。

**nlm CLI(深度调研)**:`nlm research start "<问题>" -n <notebook_id> -m deep` 发起;
`nlm research status` 看进度;导入只留调研报告、排除参考材料(见「深度调研」节)。

**install-notebooklm-mcp(配套 skill)**:见 `skills/install-notebooklm-mcp/SKILL.md`。
MCP 未装、cookie 过期、宿主未注册时**读取并执行**;装妥前阻断 NotebookLM 相关步骤。

**link-to-doc-library(配套 skill,人轨)**:见 `skills/link-to-doc-library/SKILL.md`。
脚手架 / 初始化终态 / 九步发现未联入时**读取并执行**该 skill;PowerShell `New-Item -ItemType Junction`。
不替代 codegraph / PROJECT-STATE。

**本 skill 的确定性脚本**:`scripts/preflight.py` 只读探测验证能力;
`scripts/requirements_gate.py` 阻断未批准 Pending。详细 schema、安装阶梯、质量遥测与防偏离规则见
`references/QUALITY-AND-REQUIREMENTS.md`。
