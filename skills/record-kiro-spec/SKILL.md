---
name: record-kiro-spec
description: >
  将已批准需求与已验证、已落地代码实现，补记为项目 `.kiro/specs/feature-name/` 下的
  `requirements.md`、`design.md`、`tasks.md`。仅当用户明确调用 `$record-kiro-spec`、
  明说“补 Kiro spec / 对齐 Kiro 工作流”，或在主流程给出的可选项中选择执行时使用；
  不用于设计、规划、需求审批、任务执行或指导代码实现。
---

# 补记 Kiro Spec

仅作事后记录与跨工具对齐。事实、需求及质量权威仍属获批合同、当前代码、Git 与确定性验证；
`.kiro/specs/` 不反向驱动实现。

## 前置闸

同时满足方执行：

1. 用户本轮明确选择执行；未选择则跳过，勿反复询问。
2. 需求已批准且可由 ID 定位。
3. 对应代码已落地，目标测试及适用质量闸退出码为 `0`。
4. 文件、symbol、命令、commit 或 diff 等证据可核验。

Pending、提案、未实现任务、NotebookLM 建议及推测，一律不写。

## 流程

1. 查 `.kiro/specs/`，复用对应 feature slug；无对应项才取稳定 kebab-case 新名。
2. 若仓内已有 spec，最多精读三个相近项的 `requirements.md`、`design.md`、`tasks.md` 及
   `spec.json`，沿用其标题层级、Objective、追踪字段与语言；勿扫描整棵 `.kiro/specs/`。
3. 从需求合同提取已批准行为；验收准则改写为 EARS：`WHEN ... THE SYSTEM SHALL ...`。
4. 从当前代码与验证结果提取 as-built 组件、职责、证据；勿补拟议架构。
5. 在 `.iteration/kiro-record.json` 写有界清单：

```json
{
  "schema_version": 1,
  "spec_name": "feature-slug",
  "title": "Feature title",
  "language": "zh",
  "recorded_at": "2026-07-30T00:00:00Z",
  "summary": "已落地能力摘要",
  "boundary": {
    "in_scope": ["本次已落地范围"],
    "out_of_scope": ["本次未改范围"]
  },
  "requirements": [{
    "id": "REQ-010",
    "title": "Requirement title",
    "user_story": "作为协作者，我希望……，以便……",
    "acceptance_criteria": [{"id": "1.1", "when": "条件", "shall": "行为"}],
    "evidence": ["docs/REQUIREMENTS-SPEC.md#REQ-010"]
  }],
  "implementation": {
    "components": [{
      "name": "module.symbol",
      "responsibility": "已实现职责",
      "evidence": ["relative/path.py:Symbol"]
    }],
    "verification": [{"command": "test command", "exit_code": 0}]
  },
  "tasks": [{
    "id": "1",
    "description": "已完成工作",
    "requirement_ids": ["REQ-010"],
    "evidence": ["relative/path.py:Symbol"]
  }]
}
```

6. 构建并校验：

```text
python <skill>/scripts/record_kiro_spec.py build --root <repo> \
  --input <repo>/.iteration/kiro-record.json
```

脚本仅替换自身标记区块；保留既有 Kiro 内容。官方核心约束为三文件；具体标题无仓内先例时采用
`pi-web` 已验证惯例：Introduction、Boundary Context、Objective、Acceptance Criteria、
Boundary Commitments、完成任务追踪。三文件分别表达：

- `requirements.md`：已批准用户故事、EARS 验收及合同证据。
- `design.md`：已落地架构、组件及通过验证；不写未来式方案。
- `tasks.md`：仅 `[x]` 已完成项及代码证据；不生成待执行项。

仓内任一同级 spec 已有 `spec.json` 时，新 spec 补同形元数据并标 `phase: implemented`；
目标已有 `spec.json` 则不改。`brief.md`、`research.md`、`evidence/` 仅在目标项目已有明确强制约定且
存在对应事实时补，不由脚本默认生成。

7. 只审 `.kiro/specs/<name>/` diff；核对无 Pending、无未验证陈述、无越界覆盖。

若 Kiro 文档与高权威事实冲突，修正文档；不得据其修改需求、代码或测试。
