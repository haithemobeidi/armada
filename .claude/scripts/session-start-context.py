#!/usr/bin/env python3
"""
SessionStart hook: replaces the manual `/start` typing.

Runs the branch guard, then the two-remote sync guard, then injects
CURRENT_STATE.md + the open SESSION_LEDGER items + the ROADMAP spine +
the last 5 HANDOFF_LOG.md lines into the first turn so Claude can give
the status report without the user typing /start.

This repo is a FORK with an active upstream, which changes two things
versus the template this script came from:

  1. Branch guard.  Work happens on WORK_BRANCH (odin3-tuning).  `main`
     mirrors upstream/main and must never receive commits, so landing on
     `main` trips the guard the same way a worktree does.

  2. Two remotes.  `origin` is the fork (our pushes; the laptop/desktop
     sync path).  `upstream` is armada-os/armada (read-only; several
     merges a day).  Both are fetched.  Being behind ORIGIN blocks doc
     injection (stale snapshot).  Being behind UPSTREAM is reported as a
     number so the session can decide whether to rebase — never acted on
     automatically.

Output protocol: print a JSON object to stdout with the shape
  {"hookSpecificOutput": {"hookEventName": "SessionStart",
                          "additionalContext": "<text to inject>"}}

The script is silent on every failure path — if anything goes wrong we
exit 0 with no output rather than blocking session start.
"""

import json
import os
import pathlib
import subprocess
import sys

WORK_BRANCH = "odin3-tuning"
UPSTREAM_REF = "upstream/main"


def run(cmd: list[str], cwd: str, timeout: int = 5) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return 1, ""


def remote_state(project_dir: str) -> tuple[int, int, bool, bool]:
    """Fetch origin and report how this checkout stands against its upstream
    tracking branch.  Returns (behind, ahead, dirty, fetch_ok).

    Why this must happen BEFORE the docs are read: every file this hook
    injects is a tracked repo file.  Reading them from a checkout that is
    behind origin loads a snapshot of the past that looks complete and
    self-consistent, so nothing downstream can detect it — the /start
    cross-check only tests whether the docs agree with EACH OTHER, and
    stale docs agree perfectly.

    This hook deliberately does NOT pull.  It detects and refuses to inject
    stale docs; the session does the pull where it is visible.
    """
    fetch_rc, _ = run(["git", "fetch", "origin", "--prune"], project_dir, timeout=20)
    fetch_ok = fetch_rc == 0

    rc, counts = run(
        ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], project_dir
    )
    behind = ahead = 0
    if rc == 0 and counts:
        try:
            ahead_s, behind_s = counts.split()
            ahead, behind = int(ahead_s), int(behind_s)
        except ValueError:
            pass

    rc, porcelain = run(["git", "status", "--porcelain"], project_dir)
    dirty = rc == 0 and bool(porcelain)

    return behind, ahead, dirty, fetch_ok


def upstream_state(project_dir: str) -> tuple[int, str, bool]:
    """Fetch upstream and count commits on upstream/main not in HEAD.
    Returns (behind_upstream, latest_upstream_subject, fetch_ok).

    Reported, never acted on: rebasing rewrites the tuning branch and
    needs a force-with-lease push, which is a human decision made at a
    quiet point in the session — not something a hook does at startup.
    """
    fetch_rc, _ = run(["git", "fetch", "upstream", "--prune"], project_dir, timeout=20)
    fetch_ok = fetch_rc == 0
    rc, count = run(
        ["git", "rev-list", "--count", f"HEAD..{UPSTREAM_REF}"], project_dir
    )
    behind = int(count) if rc == 0 and count.isdigit() else 0
    _, latest = run(
        ["git", "log", "-1", "--format=%h %s (%cr)", UPSTREAM_REF], project_dir
    )
    return behind, latest, fetch_ok


def open_ledger_view(text: str) -> tuple[str, int, int]:
    """Return the ledger header + ONLY the open `[ ]` item blocks.
    Returns (filtered_text, open_count, closed_count).

    Closed items ([x]/[-]) keep their full pre-closure text struck through,
    so a single closed line can run hundreds of words.  They are history,
    not context, and are deliberately never injected.
    """
    header: list[str] = []
    blocks: list[list[str]] = []
    current: list[str] | None = None
    in_items = False
    for ln in text.splitlines():
        s = ln.lstrip()
        if s.startswith("- ["):
            in_items = True
            current = [ln]
            blocks.append(current)
        elif not in_items:
            header.append(ln)
        elif s and current is not None:
            current.append(ln)
    open_blocks = [b for b in blocks if b[0].lstrip().startswith("- [ ]")]
    body = "\n".join("\n".join(b) for b in open_blocks)
    filtered = "\n".join(header).rstrip() + "\n\n" + body
    return filtered, len(open_blocks), len(blocks) - len(open_blocks)


def emit(text: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": text,
        }
    }
    sys.stdout.write(json.dumps(payload))
    sys.exit(0)


def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir or not pathlib.Path(project_dir).is_dir():
        sys.exit(0)

    # Branch guard — mirrors Step 0 of /start.
    cwd_norm = project_dir.replace("\\", "/")
    in_worktree = ".claude/worktrees/" in cwd_norm
    rc, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], project_dir)
    on_claude_branch = rc == 0 and branch.startswith("claude/")
    on_main = rc == 0 and branch == "main"

    if in_worktree or on_claude_branch or on_main:
        why = (
            "`main` mirrors upstream/main and must never receive commits"
            if on_main
            else "worktrees / `claude/*` branches are forbidden in this project"
        )
        emit(
            "⚠️ **Branch guard tripped at session start.** "
            f"cwd `{project_dir}` on branch `{branch or '(unknown)'}` — {why}. "
            f"Expected branch: `{WORK_BRANCH}`. Tell the user verbatim from "
            "`.claude/commands/start.md` Step 0 and DO NOT proceed with reading state, "
            "editing files, or running other commands until they resolve it."
        )

    # Sync guard (origin) — mirrors Step 0.5 of /start.
    behind, ahead, dirty, fetch_ok = remote_state(project_dir)

    if behind > 0:
        _, incoming = run(
            ["git", "log", "--oneline", "--no-decorate", "-15", "HEAD..@{u}"],
            project_dir,
        )
        if ahead > 0:
            resolution = (
                f"The branch has DIVERGED from origin ({ahead} ahead, {behind} behind). "
                "**Do NOT auto-merge or rebase.** Surface this to the user and let them decide. "
                "(Common cause: a rebase onto upstream was pushed from another machine.)"
            )
        elif dirty:
            resolution = (
                f"The tree is behind by {behind} AND has uncommitted changes. **Do NOT stash or "
                "merge.** Surface both to the user and let them decide."
            )
        else:
            resolution = (
                f"The tree is clean and strictly {behind} behind origin. Run `git pull --ff-only`, "
                "then read `docs/CURRENT_STATE.md`, the OPEN `[ ]` lines of "
                "`docs/SESSION_LEDGER.md`, the ROADMAP status spine, and the last 5 "
                "`docs/HANDOFF_LOG.md` lines YOURSELF before reporting."
            )
        emit(
            "## ⚠️ Session context NOT auto-loaded — this checkout is behind origin\n\n"
            f"`git fetch` found **{behind} commit(s) on origin/{branch} that are not here** "
            "(commonly: the last session ran on another machine). The state docs were "
            "deliberately NOT injected, because a stale snapshot reads as complete and "
            "self-consistent.\n\n"
            f"**Incoming commits:**\n```\n{incoming or '(unavailable)'}\n```\n\n"
            f"**Resolution:** {resolution}\n\n"
            "Then give the normal status plus a sync line naming the pulled commit count. "
            "Never report state read from a checkout you have not confirmed is current."
        )

    # Upstream drift — reported, never acted on.
    up_behind, up_latest, up_fetch_ok = upstream_state(project_dir)

    sync_note = (
        f"✅ Fetched origin — checkout is current on `{branch}`.\n"
        if fetch_ok
        else "⚠️ **Could not reach origin** — the docs below are from the local checkout and "
        "their currency is UNVERIFIED, not confirmed. Say so in the status report.\n"
    )
    if not up_fetch_ok:
        upstream_note = "⚠️ Could not fetch `upstream` — upstream drift is unknown this session.\n"
    elif up_behind == 0:
        upstream_note = f"✅ Tuning branch contains everything on `{UPSTREAM_REF}`.\n"
    else:
        upstream_note = (
            f"📥 **`{UPSTREAM_REF}` has {up_behind} commit(s) not in this branch** "
            f"(latest: {up_latest}). Rebasing is Claude's call at the first quiet point "
            "(D-2: clean tree, not during start/end, --force-with-lease, always reported): "
            "mention the count in the status report and plan the rebase — never do it as "
            "part of session start.\n"
        )

    parts: list[str] = [
        "## Auto-loaded session context (SessionStart hook)\n",
        sync_note,
        upstream_note,
    ]

    state_path = pathlib.Path(project_dir) / "docs" / "CURRENT_STATE.md"
    if state_path.exists():
        try:
            parts.append("\n### docs/CURRENT_STATE.md\n")
            parts.append(state_path.read_text(encoding="utf-8").rstrip() + "\n")
        except OSError:
            pass

    ledger_path = pathlib.Path(project_dir) / "docs" / "SESSION_LEDGER.md"
    if ledger_path.exists():
        try:
            filtered, n_open, n_closed = open_ledger_view(
                ledger_path.read_text(encoding="utf-8")
            )
            parts.append(
                f"\n### docs/SESSION_LEDGER.md — OPEN items only ({n_open} open; "
                f"{n_closed} closed line(s) omitted — closed items are history, "
                "read the file only if one is explicitly needed)\n"
            )
            parts.append(filtered.rstrip() + "\n")
        except OSError:
            pass

    roadmap_path = pathlib.Path(project_dir) / "ROADMAP.md"
    if roadmap_path.exists():
        try:
            rlines = roadmap_path.read_text(encoding="utf-8").splitlines()
            spine: list[str] = []
            capturing = False
            for ln in rlines:
                if "status at a glance" in ln.lower():
                    capturing = True
                elif capturing and ln.startswith("## "):
                    break
                if capturing:
                    spine.append(ln)
            if spine:
                parts.append(
                    "\n### ROADMAP.md — status-at-a-glance spine (SOURCE OF TRUTH for block status)\n"
                )
                parts.append("\n".join(spine).rstrip() + "\n")
        except OSError:
            pass

    handoff_path = pathlib.Path(project_dir) / "docs" / "HANDOFF_LOG.md"
    if handoff_path.exists():
        try:
            lines = handoff_path.read_text(encoding="utf-8").splitlines()
            entries = [ln for ln in lines if "|" in ln and not ln.startswith("**")][-5:]
            if entries:
                parts.append("\n### Last 5 lines of docs/HANDOFF_LOG.md\n")
                parts.append("\n".join(entries) + "\n")
        except OSError:
            pass

    parts.append(
        "\n---\n"
        "**Action requested — session start.** The hook fetched origin AND upstream, ran the "
        "branch guard, and auto-loaded CURRENT_STATE.md, the SESSION_LEDGER's open items "
        "(closed lines omitted by design — never read them at start), the ROADMAP status "
        "spine, and the last HANDOFF lines. Now:\n"
        "1. **CROSS-CHECK (mandatory).** Does CURRENT_STATE's '📍 NEXT ACTION' agree with the "
        "ROADMAP spine's ⬅ CURRENT block AND the last HANDOFF line's 'Next:', AND does no open "
        "`[ ]` ledger gate contradict it? **If they contradict, STOP and surface the "
        "contradiction to the user — do NOT pick one and proceed.**\n"
        "2. If they agree, give the status report: where we are (block **name + number** from "
        "the spine) / what last session accomplished / the single **NEXT ACTION** / open ledger "
        "items (count + gates) / a **sync line** stating origin currency explicitly AND the "
        "upstream drift count. Never let currency be assumed.\n"
        "3. **Device line.** If `docs/DEVICE.md` says an overlay is applied on the handheld, "
        "state which overlay version the device is believed to be running. Do not SSH at start "
        "unless the NEXT ACTION needs it.\n"
        "During the session, follow the ledger's moment-of-event rule: queue and strike items "
        "THE MOMENT they arise or resolve — never wait for /end. Trust but verify — "
        "CURRENT_STATE is hand-written and CAN be stale; the ROADMAP spine wins on any "
        "block-status disagreement. Block numbers are frozen (never renumber). Don't run "
        "`/start` (this hook covered it)."
    )

    emit("".join(parts))


if __name__ == "__main__":
    main()
