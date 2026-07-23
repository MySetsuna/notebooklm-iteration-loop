# NotebookLM 迭代工作流(本项目适配说明)

> 通用方法论见仓库根目录 `SKILL.md`。本文件只记录**本项目**的落地细节,克隆模板后按需填写。

## 确定性验证命令(本项目的 checker)

- typecheck: `<替换为你的命令,如 pnpm typecheck / mypy .>`
- test: `<替换为你的命令,如 cargo test / pytest>`
- lint: `<替换为你的命令,如 clippy -D warnings / ruff check>`

以上必须**全绿**才能进入 NotebookLM 环节(见 `SKILL.md` step 3)。

## codegraph 索引范围

- 索引根目录:`<repo root>`
- 排除:`<vendor/ / node_modules/ / 生成代码目录等>`
- 首次:`codegraph init -i`;日常:`codegraph sync`。

## NotebookLM 笔记本

- notebook_id:`<填入>`
- 状态文档来源名:`PROJECT-STATE`(见 `SKILL.md` 的单一来源不变量)

## 目录落点

沿用仓库根目录 `SKILL.md` 「文件骨架」一节的约定;本项目实例见 `docs/`
(`docs/PROJECT-STATE.md`、`docs/LOG.md`、`docs/iterations/`)。
