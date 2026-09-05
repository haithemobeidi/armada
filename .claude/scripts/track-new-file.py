#!/usr/bin/env python3
"""
PostToolUse hook for the Write and Edit tools.

When Claude touches a file that is NOT yet listed in docs/CODEBASE_INDEX.md,
this script appends the project-relative path to .claude/pending-index-updates.txt.
The /end protocol refuses to complete until every queued path has an index entry.

FORK NOTE — the index is scoped to the FORK DELTA, not the whole tree.
This repo carries ~500 upstream files (armada-os/armada) that we never
touch and must not catalogue: indexing them is busywork that rots on every
rebase. The scoping falls out of the hook's design for free:

  * an upstream file we never edit never fires this hook → never indexed;
  * an upstream file we DO edit fires it and is absent from the index →
    queued, and /end requires its entry to say WHY we diverged;
  * a file we create is absent from the index → queued.

So the index doubles as the list of what this fork changes — which is
exactly the list you need when preparing an upstream PR.

The script is silent on every failure path — it never blocks Claude's work.
"""

import json
import os
import pathlib
import sys


# Protocol bookkeeping — tracking these would loop (write index → hook →
# queue index → /end fails).
SKIP_FILENAMES = (
    "pending-index-updates.txt",
    "CODEBASE_INDEX.md",
    "CURRENT_STATE.md",
    "HANDOFF_LOG.md",
    "SESSION_LEDGER.md",
)

# Project-relative POSIX prefixes that never belong in the index: protocol
# state, build output, caches.  Matched against paths RELATIVE to
# $CLAUDE_PROJECT_DIR so an ancestor directory named ".claude/" (a worktree)
# cannot cause false positives.
SKIP_PREFIXES = (
    ".claude/",
    "output/",
    "_build",
    "__pycache__/",
    "node_modules/",
    "decky/armada-control/node_modules/",
    "decky/armada-store/node_modules/",
    "decky/armada-control/dist/",
    "decky/armada-store/dist/",
)

# Firmware blobs and other binaries are never "documented"; if one is ever
# touched, the commit message is the record, not the index.
SKIP_SUFFIXES = (".bin", ".mbn", ".b04", ".b08", ".b13", ".b19", ".b24", ".b31",
                 ".b34", ".b36", ".b41", ".b43", ".b46", ".b47", ".elf", ".img",
                 ".gz", ".sqsh", ".png", ".svg", ".ttf", ".pyc")


def project_relative(file_path: str) -> str | None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return None
    try:
        abs_path = pathlib.Path(file_path).resolve()
        project_root = pathlib.Path(project_dir).resolve()
        rel = abs_path.relative_to(project_root)
        return rel.as_posix()
    except (OSError, ValueError):
        return None


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool = data.get("tool_name", "")
    file_path = data.get("tool_input", {}).get("file_path", "")
    if tool not in ("Write", "Edit") or not file_path:
        sys.exit(0)

    rel_posix = project_relative(file_path)
    if rel_posix is None:
        sys.exit(0)  # outside the project tree (memory files, other repos)

    if pathlib.PurePath(rel_posix).name in SKIP_FILENAMES:
        sys.exit(0)
    if any(rel_posix == p.rstrip("/") or rel_posix.startswith(p) for p in SKIP_PREFIXES):
        sys.exit(0)
    if rel_posix.lower().endswith(SKIP_SUFFIXES):
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    try:
        index_path = pathlib.Path(project_dir) / "docs" / "CODEBASE_INDEX.md"
        if index_path.exists() and rel_posix in index_path.read_text(encoding="utf-8"):
            sys.exit(0)
    except OSError:
        pass  # can't read the index → over-queue; /end sorts it out

    try:
        script_dir = pathlib.Path(__file__).resolve().parent
        pending = script_dir.parent / "pending-index-updates.txt"
        pending.parent.mkdir(parents=True, exist_ok=True)
        existing = set()
        if pending.exists():
            existing = {
                line.strip()
                for line in pending.read_text(encoding="utf-8").splitlines()
                if line.strip()
            }
        if rel_posix not in existing:
            # newline="\n": on Windows, text mode would write CRLF and every
            # shell loop reading this file would see "path\r" (bit us 2026-09-05).
            with open(pending, "a", encoding="utf-8", newline="\n") as f:
                f.write(rel_posix + "\n")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
