#!/usr/bin/env python3
"""
Stop hook: enforces /end Step 4a (clean-tree guarantee) as a fail-safe.

Fires whenever Claude finishes a turn. Silent during normal work — it only
intervenes when this exact protocol-violation pattern is detected:

  1. The most recent commit subject starts with "Session:" AND was made
     within the last 5 minutes (i.e. /end just completed), AND
  2. `git status --porcelain` is non-empty (the tree is NOT actually clean).

When that matches, /end Step 4a was skipped: return decision=block with a
reason that forces Claude to address the dirty tree before stopping.

Silent on every failure path.
"""

import json
import os
import pathlib
import subprocess
import sys
import time


def run(cmd: list[str], cwd: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=5
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return 1, ""


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Already triggered once this turn — don't loop.
    if data.get("stop_hook_active"):
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir or not pathlib.Path(project_dir).is_dir():
        sys.exit(0)

    rc, _ = run(["git", "rev-parse", "--git-dir"], project_dir)
    if rc != 0:
        sys.exit(0)

    rc, commit_info = run(["git", "log", "-1", "--format=%s|%ct"], project_dir)
    if rc != 0 or "|" not in commit_info:
        sys.exit(0)

    subject, _, ts_str = commit_info.partition("|")
    try:
        age_seconds = int(time.time()) - int(ts_str)
    except ValueError:
        sys.exit(0)

    if not (subject.startswith("Session:") and age_seconds <= 300):
        sys.exit(0)

    rc, status = run(["git", "status", "--porcelain"], project_dir)
    if rc != 0 or not status:
        sys.exit(0)

    payload = {
        "decision": "block",
        "reason": (
            "PROTOCOL VIOLATION: /end Step 4a (clean-tree guarantee) was skipped. "
            "The most recent commit is a 'Session:' commit but `git status --porcelain` "
            "is non-empty. You must NOT stop here. Run `git status`, categorize each "
            "remaining entry per /end Step 4a (real in-scope work → second 'Session followup:' "
            "commit; out-of-scope → ask the user to commit/stash/discard), then push again. "
            "Only stop once the tree is clean."
        ),
    }
    sys.stdout.write(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
