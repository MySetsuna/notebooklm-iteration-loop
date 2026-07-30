#!/usr/bin/env python3
"""Synchronize the NotebookLM iteration skill into local host catalogs.

Copies source files without deleting target-only files.  This keeps Codex,
Grok, and Claude on the same mother skill while preserving host-local extras.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


EXCLUDED_PARTS = {".git", ".codegraph", ".cursor", "__pycache__"}
DEFAULT_HOSTS = (".codex", ".grok", ".claude")


def source_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in source.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        files.append(path.relative_to(source))
    return sorted(files)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync(source: Path, targets: list[Path]) -> list[dict[str, str]]:
    files = source_files(source)
    changes: list[dict[str, str]] = []
    for target in targets:
        target.mkdir(parents=True, exist_ok=True)
        for relative in files:
            src = source / relative
            dst = target / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            before = digest(dst) if dst.is_file() else ""
            shutil.copy2(src, dst)
            after = digest(dst)
            if before != after:
                changes.append({"target": str(dst), "sha256": after})
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync notebooklm-iteration-loop skill copies.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--host", action="append", dest="hosts", default=None)
    args = parser.parse_args()
    source = args.source.resolve()
    hosts = args.hosts or list(DEFAULT_HOSTS)
    targets = [(args.home / host / "skills" / source.name).resolve() for host in hosts]
    changes = sync(source, targets)
    print(f"synced={len(targets)} files_changed={len(changes)}")
    for change in changes:
        print(f"changed {change['target']} {change['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
