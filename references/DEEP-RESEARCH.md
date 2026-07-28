# NotebookLM 深度调研

仅在外部生态、架构选型或根因无法由代码/现有两源确定，且结论会复用时使用：

```text
nlm research start "<question>" -n <notebook_id> -m deep
nlm research status
```

完成后仅导入调研报告为临时第三来源，绝不导入数十网页参考。以两常驻源和报告发起一次有格式、
有证据上限的决策问题；建议必须经代码事实与确定性验收对抗核验。相关实现完成后，将结论压成 note/
JSONL 事实，删除临时报告来源，恢复两常驻源。
