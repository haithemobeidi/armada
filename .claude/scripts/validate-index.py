#!/usr/bin/env python3
"""
Bidirectional CODEBASE_INDEX validator (reverse direction).

The PostToolUse hook (track-new-file.py) covers the forward direction:
files on disk absent from the index. This script covers the reverse:
index rows pointing at files that no longer exist (phantom rows left by
renames, splits, deletes — or by an upstream rebase that removed a file
we had annotated).

Usage (called from /end Step 1c):
    python .claude/scripts/validate-index.py

Prints one line per phantom path. Exits 0 always — never blocks.
"""

import os
import pathlib
import re
import sys

# Matches the first backtick-quoted segment in a Markdown table row:
#   | `path/to/file` | Description |
ROW_RE = re.compile(r"^\|\s+`([^`]+)`\s+\|")


def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        script_dir = pathlib.Path(__file__).resolve().parent  # .claude/scripts/
        project_dir = str(script_dir.parent.parent)

    project_root = pathlib.Path(project_dir).resolve()
    index_path = project_root / "docs" / "CODEBASE_INDEX.md"
    if not index_path.exists():
        sys.exit(0)

    try:
        lines = index_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        sys.exit(0)

    phantoms: list[str] = []
    for line in lines:
        m = ROW_RE.match(line)
        if not m:
            continue
        rel_path = m.group(1)
        if not (project_root / rel_path).exists():
            phantoms.append(rel_path)

    if phantoms:
        print(f"PHANTOM ROWS ({len(phantoms)}) — index entries pointing at non-existent files:")
        for p in phantoms:
            print(f"  {p}")

    sys.exit(0)


if __name__ == "__main__":
    main()
