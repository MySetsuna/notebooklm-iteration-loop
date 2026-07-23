---
name: notebooklm-iteration-loop
description: >
  用 codegraph + NotebookLM 驱动一个项目的持续迭代:每轮先用 codegraph 更新索引并检索,勾勒
  真实架构与细节设计 → 据此**更新同一份**项目状态文档 → 替换 NotebookLM 里那唯一一份来源 →
  让它结合全部来源给下一步计划 → 对抗评审 → 归档 → 下一轮。当用户想「配合 NotebookLM 持续迭代
  某项目」「基于笔记本来源规划下一步开发」「把当前进度同步 NotebookLM 并要下一步指导」,或要
  初始化/压缩/整理某个笔记本的存量来源与 notes(清掉已实现或无关来源、把未实现规划移入 notes)、
  用 loop-engineering 最佳实践搭建开发/规划/归档工作流时使用。
---

# codegraph + NotebookLM 驱动的迭代循环

把「开发 → 索引 → 报告 → 规划 → 归档」做成一个可复用的闭环。核心思想(loop engineering):
人负责定义「done/good」并搭循环;**codegraph 当架构真相源**(本地 AST 索引,给的是代码事实);
**NotebookLM 当规划器 + 根因分析器**(读少而精的来源给方向);代码由本地开发环写;验证只认
**确定性信号**(编译器/测试/退出码),不靠模型自述。

**三条硬规矩(与旧版的区别,别退回去):**
1. **架构事实来自 codegraph,不来自 NotebookLM**。想知道「谁调谁 / 改这个会炸什么 / 这条流怎么走」,
   查索引,别问笔记本。
2. **笔记本里每个项目恒为 1 份来源**:那份状态文档。每轮**更新并替换**它,而不是每轮追加一份新来源——
   来源越堆越多只会让 NotebookLM 引用陈旧快照、张冠李戴。**不留任何常驻的第二份来源**(含存量
   压缩阶段产出的领域报告——那些只进本地 git,不上传/不常驻笔记本)。迭代过程的历史留痕
   (进度报告、NotebookLM 原文指导)**只写入 git 仓库归档,永不上传笔记本**。
3. **迭代要大,轮次要少**(见下节)。NotebookLM 往返是本循环最贵的一段;能在**一轮合同**里
   明确规划完的工作,不要拆成三轮去问三次。

## 迭代粒度:默认「大迭代」

每轮 NotebookLM 往返(上传状态文档 + query + 归档 + 对抗评审)成本远高于本地多写几个模块。
**故默认把一轮做大**,前提是两条都成立:

- **任务明确**:每个目标都能写出「改哪些文件 / 落哪个层 / 用什么现成件」,而非「探索一下 X」;
- **规划清晰**:每个目标都有**可被编译器/测试/退出码判定**的验收,且目标间依赖顺序已理清。

不满足时**先只做一个「勘察目标」**把它变明确,而不是把模糊目标塞进大合同。

实操:
- 一轮合同带 **4–8 个目标**是常态,包含一条主线(占多数工作量)+ 若干可独立验收的支线;
- 目标之间**尽量无强依赖**,某一项触发停机条件时其余仍可继续、不空转一整轮;
- 每个目标独立提交(可回滚),合同内**按序**推进,**全部做完再走 step 4 起的 NotebookLM 环节**;
- 只在真被**外部信息**卡住(需 NotebookLM 定夺方向/根因)时才提前进入往返,不为「汇报进度」而往返;
- 一轮做不完的部分**顺延进下一份合同**,不作为提前往返的理由。

## 何时用

用户表达「用 NotebookLM 持续迭代这个项目 / 同步进度取下一步 / 搭规划归档工作流 / 初始化或整理笔记本存量来源」时。
前置:① `notebooklm-mcp` 能访问目标笔记本(没有就先 `notebook_list` 找,或 `nlm login`);
② 项目已有 codegraph 索引(`.codegraph/` 不存在则先 `codegraph init -i`)。
开工先 `notebook_get` 查验笔记本是否合规(见下节);不合规则**先初始化,再进迭代**。

## 初始化(笔记本不合规时先做)

**合规 = 来源恒 1 份 `PROJECT-STATE`,未实现的规划/愿景类内容活在 notes。**
不合规(多份来源 / 无 PROJECT-STATE / 规划散落在来源里)则先走以下流程。
**用户只要求初始化时,做完即停,不往下推迭代。**

1. **codegraph 立事实**:`codegraph sync` 更新索引(索引可疑则 `codegraph index`,首次
   `codegraph init -i`),再用 `codegraph_context` / `codegraph_explore` / `codegraph_trace`
   探明当前真实实现:模块边界、关键符号与调用路径、已落地能力清单——这是逐源分诊的判据。
2. **先立新来源**:据代码事实写出首份 `docs/PROJECT-STATE.md`(结构见九步之 step 5),
   `source_add` 上传、`source_rename` 为 `PROJECT-STATE`,确认入库。先立后拆,避免空窗。
3. **逐来源分诊**:对其余每份来源 `source_get_content` 取原文,对照 codegraph 代码事实归类:
   - **所述内容已实现** → 删(现状事实已由 PROJECT-STATE 承载,留着只会被引旧快照);
   - **偏离项目 / 与项目无关** → 删;
   - **未实现的规划、愿景与展望** → 先 `note(action="create")` 摘录进 notes(标题带原来源名,
     便于溯源),再删;
   - 拿不准,或含仍有效但未入代码的决策理由/坑 → 并入 `PROJECT-STATE.md` 对应章节后再删
     (知识密度高的来源按「存量来源压缩」一节先深挖)。
4. **批量删除**:`source_delete(confirm=true)`。删除不可逆:先确认 PROJECT-STATE 已入库、
   规划类已落 notes,并**当面向用户确认**再删。
5. **终态**:来源恒 1 份 = `PROJECT-STATE`;未实现规划全在 notes。此后每轮迭代照常走九步;
   制定 contract 时用 `note(action="list")` 读存量规划作参考(notes 不参与 `notebook_query`
   的来源检索,取用要靠 note 工具)。

## 一次迭代的九步

1. **读上下文**:项目里的 `docs/iterations/CONTRACT-iteration-{N}.md`(本轮目标+验收)与
   `docs/LOG.md` 末尾 5–10 条(跨迭代长期记忆)。首轮没有就跳过。
2. **开发**:按 contract 优先级实现,受 constraints 约束。别超出本轮范围。
3. **确定性验证**:跑项目的客观质量闸(如 `pnpm typecheck` / `cargo test` / `clippy -D warnings`,
   或对应语言的等价物)。**必须全绿**才算这步过 —— 这是 maker-checker 里 checker 的信号。
4. **codegraph 刷新 + 检索勾勒架构**(替代了旧版的「每轮上传一堆文档」):
   - `codegraph sync`(增量;大改动或索引可疑时 `codegraph index`),再 `codegraph_status` 确认节点/边数合理。
   - 用 **MCP 工具**检索,勾勒本轮之后的真实架构与细节:`codegraph_context <本轮主题>` 起手 →
     `codegraph_explore` 一次拿多个关键符号的源码 → 流程用 `codegraph_trace from→to` →
     改动面用 `codegraph_impact`。**别用 grep+read 循环重建索引已有的答案。**
   - 产出是「代码事实」:模块边界、关键符号签名、调用路径、受影响面。写进下一步的状态文档。
5. **更新那唯一一份状态文档** `docs/PROJECT-STATE.md`(路径按项目定,但**全程只此一份**),覆盖式重写,含:
   - 项目是什么 + 不可动摇的设计主线 / 已锁定决策(稳定段,少改);
   - **由 codegraph 勾勒的当前架构**:模块与落点、关键接口签名、关键调用路径、目录现状;
   - 本轮做了什么 + 确定性验证证据(命令 + 结果);
   - 能力对照(距最终目标差什么)、开放问题、**请 NotebookLM 定夺的具体问题**。
   同时照旧在本地写一份带时间戳的迭代报告 `docs/iterations/{YYYY-MM-DD}-iteration-{N}.md` 作历史存档——
   **它只留在本地仓库,不上传**。
6. **替换 NotebookLM 里的那份来源**(顺序别反,避免空窗):
   - `source_add(notebook_id, source_type="file", file_path=<PROJECT-STATE.md 绝对路径>, wait=true)`;
   - 确认新来源出现在 `notebook_get` 里之后,再 `source_delete(source_id=<上一版那份>, confirm=true)`;
   - `source_rename` 把新来源命名为稳定名(如 `PROJECT-STATE`),便于下轮定位。
   - 排障期需要 NotebookLM 做根因分析时,可**临时**加 `trace.json`/报错日志,**用完即删**,不占常驻额度。
7. **取下一步计划**:`notebook_query`,让它结合全部来源给「下一迭代优先级排序 + 每步的
   **确定性验收信号** + 里程碑地图」。把原文归档为
   `docs/iterations/{YYYY-MM-DD}-notebooklm-guidance-{N}.md`。
8. **对抗评审(关键步,别跳)**:**不要全信 NotebookLM**。它是计划的 *maker*,不是 ground truth——
   它会硬凑不相关的引用、把 app 层的东西塞进底层、给「听起来对」的过度设计。对每条关键建议做独立
   *checker*:①核对它引用的来源**是否真的支撑**该结论(常张冠李戴);②**用 codegraph 对代码事实**
   (它说的这个符号/这层/这条依赖真的存在吗?`codegraph_search`/`codegraph_impact` 一查便知)——
   这是驳回幻觉建议最快的手段;③用第一性原理检验(这抽象该放哪层?验收信号真的可判吗?);
   ④对高影响/不可逆决策,另起干净上下文(子 agent / 新会话)当**对抗评审员**,专挑反例。
   把「采纳/驳回 + 理由」写进归档。**采纳经过检验的部分,不是它说的全部。**
9. **归档 + 落下一份 contract**:据(经对抗评审后的)结论写 `CONTRACT-iteration-{N+1}.md`;在 `docs/LOG.md`
   顶部追加一条本轮记录(做了什么 + 下一步 + 触发的熔断 + 驳回了 NotebookLM 的哪些建议)。

## 深度调研(遇疑难时的外部信息通道)

迭代中遇到**要探讨的问题或拿不准的方向**(架构选型、外部生态、最佳实践、疑难根因),
不要靠猜,让 NotebookLM 做深度调研:

1. `nlm research start "<问题>" -n <notebook_id> -m deep` 发起(web 深研,约 5 分钟);
   `nlm research status` 轮询至完成。
2. **只把「调研报告」导入为来源,排除全部参考材料**——几十份网页源只会稀释检索、
   引来陈旧引用。若导入无法排除参考材料,导入后立刻 `source_delete` 之,仅留报告一份。
3. 报告是**临时第二来源**:与 `PROJECT-STATE` 并存,供后续 `notebook_query` 制定合同时引用;
   其建议仍须过对抗评审(step 8),不全信。
4. **相关研究全部在项目中实现(确定性验证通过)后**,先把报告结论
   `note(action="create")` 归档进 notes(标题带日期与主题),再 `source_delete(confirm=true)`
   移除该来源报告。终态回归「来源恒 1 份」。

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
4. 把各领域深度报告的骨架与结论,合并改写进 `docs/PROJECT-STATE.md` 对应章节(架构现状/
   稳定决策/开放问题),使其成为覆盖全部领域的**单一**现状文档。
5. `source_add` 上传合并后的 `PROJECT-STATE.md`,确认入库后,`source_delete(source_ids=[...全部旧来源],
   confirm=true)` **批量删除原有碎片(含压缩阶段查询用的临时来源)**。删除不可逆:先确认新文档
   已成功入库,并**当面向用户确认**再删。
6. 终态:**笔记本内恒为 1 份来源** = `PROJECT-STATE.md`。领域深度报告只留本地 git 存档,
   不再上传或常驻。

## 文件骨架(artifacts / contracts / logs)

```
docs/
  WORKFLOW.md                 # 这个循环在本项目的说明
  PROJECT-STATE.md            # ★唯一上传 NotebookLM 的文档,每轮覆盖式更新 + 替换来源
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
- **一个项目一份状态文档**:更新+替换,不追加。**笔记本来源恒为 1**(仅 `PROJECT-STATE`);
  压缩产出的领域报告、每轮进度报告、NotebookLM 原文指导,一律只进本地 git 归档,永不上传。
  唯二例外皆**临时**:排障日志(用完即删)与深度调研报告(研究实现完毕即归档 notes 后删,
  见「深度调研」节)。
- **规划/愿景不当来源存**:未实现的规划、愿景、展望记入 notes(`note` 工具);来源只承载
  现状事实。已实现或与项目无关的来源,初始化时删。
- **停机条件写成合同不是愿望**:验收必须能被编译器/测试/退出码客观判定,不写「改进代码」。
- **maker ≠ checker**:生成的东西不给自己打分;验证只认确定性证据。
- **授权阶梯**:默认 Level 2(Draft)——改动在分支/worktree,人做物理验证后合并,不 auto-merge;
  当前级稳定产出「本来就会手动合的」质量,才往上爬一级。
- **每轮留熔断记录**:硬回合上限 / 预算 / 无进展检测触发的情况写进报告,用于判断健壮性。
- **NotebookLM 是 maker 不是裁判**:任何关键决策必须过对抗评审(step 8)再采纳。
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
