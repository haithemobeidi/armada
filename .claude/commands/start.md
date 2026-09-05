# /start — Session Start Protocol

Begin a development session. The `SessionStart` hook normally does Steps 0–3 and injects the docs automatically; type `/start` to force the full protocol if the hook output is missing.

> **Workflow note:** sessions run **directly in the main checkout** at `C:\Users\haith\Documents\Vibe Projects\armada-odin3\` on branch **`odin3-tuning`**. This repo is a fork of `armada-os/armada`; `main` is a read-only mirror of `upstream/main` and never receives commits. Worktrees and `claude/*` branches are forbidden (Claude Code Desktop force-creates them — see [anthropics/claude-code#21236](https://github.com/anthropics/claude-code/issues/21236); the fix is to run `claude` from a terminal in the project root).

## Step 0 — Branch guard (FAIL FAST)

```bash
pwd
git rev-parse --abbrev-ref HEAD
```

If the cwd contains `.claude/worktrees/`, OR the branch starts with `claude/`, OR the branch is `main`, **STOP IMMEDIATELY**. Do not read other files. Do not edit anything. Tell the user:

> ⚠️ **Branch guard tripped.** This session is on branch `<branch>` in `<pwd>`. Work happens on `odin3-tuning`; `main` mirrors upstream and must never receive commits. Fix: `git switch odin3-tuning` (if the tree is clean), or quit and run `cd "C:/Users/haith/Documents/Vibe Projects/armada-odin3" && claude` from a terminal if this is a worktree.

Any other branch (e.g. a `pr/*` branch cut from `main` for an upstream PR) is allowed — name it in the status report.

## Step 0.5 — Sync guard, two remotes (BEFORE reading a single doc)

```bash
git fetch origin --prune
git fetch upstream --prune
git status -sb
git rev-list --count HEAD..upstream/main
```

`git status` saying "up to date" without a fetch proves nothing: it compares against the local remote-tracking ref, which only moves on fetch/pull/push.

| Origin state | Action |
|---|---|
| Up to date | Proceed. |
| `[behind N]`, tree clean | `git pull --ff-only`, then proceed. Report the pull. |
| `[behind N]`, tree dirty | **STOP.** Surface both. Do not stash, do not merge. |
| `[ahead N, behind M]` (diverged) | **STOP.** Surface it. Common cause: a rebase pushed from the other machine. Never auto-merge or rebase at session start. |
| Fetch failed | Proceed, but report currency as **unverified**. |

**Upstream drift is reported at start, acted on later.** State the count (`upstream/main has N commits we don't`). Rebasing rewrites `odin3-tuning` and is pushed with `--force-with-lease`; it is Claude's call at the first quiet point (clean tree, not during `/start` or `/end`) and is always reported (`DECISIONS.md` → D-2, amended). Never rebase during session start.

## Steps 1–6 — Read state, cross-check, report

1. Read `docs/CURRENT_STATE.md` — focus on the **📍 NEXT ACTION** line.
2. Read the **open `[ ]` lines only** of `docs/SESSION_LEDGER.md` (grep `- [ ]`; closed lines are struck-through history). Count them; note any that gate the NEXT ACTION.
3. Read the last 5 lines of `docs/HANDOFF_LOG.md`.
4. **Working-tree check.** `git update-index --really-refresh > /dev/null 2>&1 || true`, then `git status` and `git log --oneline -5`. Anything still dirty after the refresh is real and means the previous `/end` did not leave a clean tree — flag it.
5. Read the **"📊 status at a glance" spine in `ROADMAP.md`** — the single source of truth for which block is ⬅ CURRENT.
6. **CROSS-CHECK (mandatory).** CURRENT_STATE's NEXT ACTION must agree with (a) the spine's CURRENT block, (b) the last HANDOFF line's "Next:", (c) recent commits, and (d) no open ledger gate. **If anything contradicts, STOP and surface it — do not pick one and proceed.**

## Step 7 — Report

- Where we are (block **name + number** from the spine)
- What was accomplished last session
- The single **NEXT ACTION** — or the flagged contradiction
- Open ledger items: N (call out gates)
- **Sync:** `origin @ <sha>` + `(pulled N)` or `(⚠️ unverified)`; **upstream:** `+N commits` or `current`
- **Device:** which overlay version `docs/DEVICE.md` says is applied on the handheld. Don't SSH at start unless the NEXT ACTION needs it.

**Trust, but verify.** CURRENT_STATE is hand-written and CAN be wrong; the ROADMAP spine wins on any block-status disagreement, and CURRENT_STATE gets fixed. Block numbers are **frozen** (a cut block stays a labeled gap; never renumber).

See [`PROTOCOL.md`](../../PROTOCOL.md) for the complete protocol.
