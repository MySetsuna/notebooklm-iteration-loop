# Initialization, source cleanup, and Notes

Read this only when the notebook is non-compliant, sources require consolidation, or vision/Notes need maintenance.

1. First confirm the baseline through the main Skill start gate. If the CodeGraph index is absent, stop and ask the owner to decide; never initialize it automatically.
2. Use code facts to classify sources: delete implemented or irrelevant material; turn unimplemented vision into a Note; compress still-valid rationale into the current `PROJECT-STATE` or approved requirements.
3. Before deleting a source, confirm both replacement truth sources are present and the user explicitly agrees. The end state is exactly two persistent sources.
4. An `open` vision requires a Note. Mark it `implemented` or delete it only after the corresponding code exists and deterministic acceptance passes. User-side physical steps do not imply missing feature code, but they also cannot be used to clear unimplemented Notes.
5. At every completed iteration, reconcile all Notes created or relied on by that iteration. Write the compact verified decision/evidence record to local archive; then delete superseded Notes, or label retained Notes `Completed — <iteration-id>` with closure evidence. Never retain a stale planning Note merely because it was once useful.
6. When consolidating existing sources, query by domain and write only a local temporary digest. Merge facts into the two truth sources, then obtain authorization before deleting fragmented sources.
