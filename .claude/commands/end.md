# /end — Session End Protocol

Wrap up the development session cleanly. **Execute every step in order. Do not skip.**

> Sessions run in the main checkout on **`odin3-tuning`**. `main` mirrors upstream and never receives commits. Worktrees and `claude/*` branches are forbidden.

## Step 0a — Branch guard (FAIL FAST)

```bash
pwd
git rev-parse --abbrev-ref HEAD
```

If the cwd contains `.claude/worktrees/`, OR the branch starts with `claude/`, OR the branch is `main`, **STOP**. Do not `/end` from here. Tell the user which guard tripped and that work on disk is preserved; they should resolve the branch (`git switch odin3-tuning`) or restart from a terminal in the project root, then `/end` there. Never commit to `main`.

## Step 0b — Clear phantom-dirty files

```bash
git update-index --really-refresh > /dev/null 2>&1 || true
```

## Step 0c — Build guard (FAIL FAST)

This repo has no compiler; the guard is syntax + the repo's own tests, scoped to what changed:

```bash
# Diff against the FORK POINT, not upstream's tip: when we're behind upstream,
# `git diff upstream/main` would list upstream's own new commits as "our" changes.
BASE=$(git merge-base HEAD upstream/main)
git diff --name-only "$BASE" -- '*.py' | xargs -r python -m py_compile
git diff --name-only "$BASE" -- '*.sh' 'system_files/usr/libexec/armada/*' 'tools/*' | xargs -r -I{} bash -n {}
# run the repo test(s) whose subject you touched, if any (tests/*-test.sh are bash + python)
```

Also: `python -c "import configparser; c=configparser.ConfigParser(); c.read('device-overlay/etc/armada/power-profiles.conf')"` for every `.conf` in `device-overlay/` — a malformed overlay makes `armada-powerd` drop the file and revert to factory defaults **silently** (it keeps a `.invalid-<timestamp>` backup and logs to stderr). If anything FAILS, **STOP** — fix or get an explicit override before continuing. Do not commit a tree that fails this guard.

## Step 1 — Verify pending index updates

Read `.claude/pending-index-updates.txt`. If non-empty: for each path, add a one-line entry to `docs/CODEBASE_INDEX.md`. **For a modified upstream file** the entry must say what we changed AND why we diverged (that text is the seed of the eventual PR description). Then empty the pending file. **Do not proceed until done.**

## Step 1b — Backstop: diff-based index check

```bash
git diff --name-only "$(git merge-base HEAD upstream/main)"
git ls-files --others --exclude-standard
```

Read `.claude/pending-index-updates.txt` with `tr -d '\r'` — the file is written on Windows.

Ignore protocol bookkeeping (`.claude/`, `CODEBASE_INDEX.md`, `CURRENT_STATE.md`, `HANDOFF_LOG.md`, `SESSION_LEDGER.md`), `output/`, `_build*`, `__pycache__/`, `device-data/`, and binary blobs. Every remaining path must appear verbatim in `docs/CODEBASE_INDEX.md`. If any are missing: report that the hook may have failed, add the entries, and note it in CURRENT_STATE's "things to watch".

## Step 1c — Phantom-row check

```bash
python .claude/scripts/validate-index.py
```

Remove any reported phantom rows. (A rebase that deleted an upstream file we had annotated shows up here.)

## Step 1d — Reconcile `docs/SESSION_LEDGER.md`

Read the ledger **from disk**. Disposition every `[ ]` this session touched (`[x]` + `→ DONE <date>: <evidence>`, or `[-]` + reason). Append `[ ]` lines for anything queued this session that isn't captured ("next session", "before rebuild", "check later", "queued", "watch"). Prune struck lines older than 7 days. Never strike an item you don't recognize. Do this BEFORE writing CURRENT_STATE.

## Step 1e — Device parity check

If this session changed anything under `device-overlay/` OR applied anything to the handheld:

1. `docs/DEVICE.md` → "Applied overlay" must name the commit/version of `device-overlay/` the handheld is currently running. Update it.
2. If the repo overlay and the device disagree (repo edited, not pushed to device — or a live edit on the device not yet copied back), say so in CURRENT_STATE's blockers. The repo is the source of truth; the device is a deployment target. Never leave the two silently different.

## Step 2 — Reconcile the ROADMAP spine, then overwrite `docs/CURRENT_STATE.md`

If this session completed/started a block or changed scope, update the **"📊 status at a glance" spine in `ROADMAP.md`** first. Spine cells stay short: a status marker, the gate that holds the block open, at most a pointer. **Never renumber blocks.**

Then re-read `docs/CURRENT_STATE.md` from disk and replace it entirely:

- **📍 NEXT ACTION** — ONE unambiguous line matching the spine's ⬅ CURRENT block.
- **Current block:** `B<n> — <name>` (the statusline parses this line).
- **Build status:** working / broken / untested (the statusline parses the first word).
- Optional loose ends — POINT at open ledger IDs; no separate prose list. Marked NOT the next step.
- Last things accomplished this session.
- Active blockers + things to watch (device/repo overlay parity goes here if broken).

Do NOT keep a copy of the block list here — point at the spine.

## Step 3 — Append one line to `docs/HANDOFF_LOG.md`

Get the time with `date '+%Y-%m-%d %H:%M'`. Append:

```
YYYY-MM-DD HH:MM | <Block name> | <one-line summary incl. "Next:"> | <build status>
```

Summary field hard cap ~300 chars. A post-/end **mini-wrap** line covers ONLY the delta since the previous wrap.

## Step 4 — Git commit and push

`git status`, then stage the bookkeeping (`docs/CURRENT_STATE.md`, `docs/HANDOFF_LOG.md`, `docs/SESSION_LEDGER.md`, `docs/CODEBASE_INDEX.md`, `docs/DEVICE.md` if touched) plus any work the user confirmed. Commit: `Session: <one-line summary>`. Then `git push`.

Pushes to `origin/odin3-tuning` at `/end` are pre-authorized (`DECISIONS.md` → D-3). **`--force` of any kind is NOT covered by that** — the only sanctioned force is `git push --force-with-lease origin odin3-tuning` immediately after a user-approved rebase (D-2). If a plain push is rejected, report it and let the user decide; do not retry destructively.

### Step 4a — Clean-tree guarantee (non-negotiable)

`git status --porcelain` MUST print nothing. For each remaining entry: (1) real in-scope work → second commit `Session followup: <summary>` + push; (2) out-of-scope or unreviewed → STOP and ask commit/stash/discard; (3) unsure → treat as (2).

### Step 4b — Confirm origin matches

```bash
git fetch origin odin3-tuning
git rev-parse HEAD; git rev-parse origin/odin3-tuning   # must match
```

If they differ, the push didn't land — report, don't force.

## Step 5 — Report

1. What was accomplished this session
2. What's next
3. Anything to watch for next session (incl. upstream drift count, device overlay parity)
4. Open ledger items: N (IDs; call out gates)

Then: **"Session is done. Clear context (`/clear`) and open a new session when you're ready to work again."**

## After /end — mini-wrap rule

Work that continues after a completed `/end` MUST close with a mini-wrap: ledger lines → ONE delta-only HANDOFF line → CURRENT_STATE only if NEXT ACTION or build status changed → `Session followup:` commit + push → clean tree. No improvised whole-session re-summaries.

See [`PROTOCOL.md`](../../PROTOCOL.md) for the complete protocol.
