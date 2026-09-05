#!/usr/bin/env python3
"""
Statusline: block + build status + branch + dirty count + upstream drift.

Format example:
  B1 measure | build: untested | odin3-tuning | clean | upstream +7

Reads `**Current block:**` and `**Build status:**` from docs/CURRENT_STATE.md.
The upstream number is `git rev-list --count HEAD..upstream/main` against the
LOCAL remote-tracking ref (no fetch — the statusline must return in <300ms);
it is only as fresh as the last fetch, which the SessionStart hook performs.

Statusline contract: JSON on stdin (we use workspace.current_dir), exactly
one line on stdout, fast.
"""

import json
import pathlib
import re
import subprocess
import sys


def run(cmd: list[str], cwd: str) -> str:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.SubprocessError, OSError):
        return ""


def extract_block(text: str) -> str:
    # Preferred: **Current block:** B3 — Fan and thermal   → "B3 fan and thermal"
    m = re.search(r"\*\*Current block:\*\*\s*([^\n]+)", text, re.IGNORECASE)
    if not m:
        return "?"
    raw = m.group(1).strip()
    raw = re.sub(r"\s+[—-]\s+", " ", raw, count=1)
    return raw[:34]


def extract_build(text: str) -> str:
    m = re.search(r"\*\*Build status:\*\*\s*\*?\*?([a-zA-Z]+)", text)
    return m.group(1).strip().lower() if m else "?"


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        payload = {}

    cwd = payload.get("workspace", {}).get("current_dir") or payload.get("cwd") or "."
    project_dir = pathlib.Path(cwd)

    block = build = "?"
    state_path = project_dir / "docs" / "CURRENT_STATE.md"
    if state_path.exists():
        try:
            text = state_path.read_text(encoding="utf-8")
            block = extract_block(text)
            build = extract_build(text)
        except OSError:
            pass

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], str(project_dir)) or "no-git"

    porcelain = run(["git", "status", "--porcelain"], str(project_dir))
    dirty_count = len([ln for ln in porcelain.splitlines() if ln.strip()]) if porcelain else 0
    dirty_part = f"{dirty_count} dirty" if dirty_count else "clean"

    behind = run(["git", "rev-list", "--count", "HEAD..upstream/main"], str(project_dir))
    upstream_part = f"upstream +{behind}" if behind.isdigit() and int(behind) > 0 else "upstream ok"

    sys.stdout.write(f"{block} | build: {build} | {branch} | {dirty_part} | {upstream_part}")


if __name__ == "__main__":
    main()
