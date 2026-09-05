# armada-odin3 — Session Protocol

This is the **single source of truth** for how Claude Code sessions work in this project. `CLAUDE.md` references this file — do not duplicate session rules elsewhere.

## Why this exists

The protocol was developed on earlier projects (TrainerKit → Playmoir) and fixed three recurring problems with **automation, single source of truth, and minimum ceremony**: a codebase index that drifted because updating it relied on discipline at the worst moment; overlapping protocol docs that drifted apart; and end-session ceremony so heavy that steps got skipped.

This project adds two things those projects never had, and the protocol covers both:

1. **An active upstream.** This repo is a fork of `armada-os/armada`, which merges several PRs a day. `main` mirrors upstream; our work is a stack of commits on `odin3-tuning`.
2. **A physical device.** The AYN Odin 3 runs the OS. Its writable `/etc` can drift from the repo invisibly, and a wrong change can brick it. Device state is part of session state.

---

## Files this protocol manages

| File | Purpose | When updated |
|---|---|---|
| `docs/CODEBASE_INDEX.md` | One line per file **in the fork delta** (files we created + upstream files we modified, with why) | Whenever such a file is touched (hook-enforced) |
| `docs/CURRENT_STATE.md` | Latest project state — overwritten each session | At session end |
| `docs/HANDOFF_LOG.md` | Append-only one-line session history | At session end |
| `docs/SESSION_LEDGER.md` | Append-and-strike ledger of open session-scoped items | **At the moment** an item is queued or resolved; reconciled at `/end` |
| `docs/DEVICE.md` | Hardware facts, access, file ownership, and **which overlay version the handheld is running** | When a device fact changes or something is applied to the device |
| `device-overlay/` | Repo-owned files pushed to the handheld's `/etc` (no UI writer) | As tuning changes; pushed by `tools/` |
| `device-state/` | Committed record of the UI-owned configs as last pulled from the handheld | `tools/` pull at each pause that changed a UI setting, and at `/end` |
| `.claude/pending-index-updates.txt` | Transient queue of files needing index entries | Auto-managed by hook |

**Why no per-session snapshot files:** they pile up and nobody reads past the newest. One rolling state doc + one append-only log carries the same information without the noise.

---

## Where-are-we: one source of truth, frozen numbers

The single source of truth for **project status** is the **"📊 status at a glance" spine table in `ROADMAP.md`**. `docs/CURRENT_STATE.md` carries only the **📍 NEXT ACTION** line + this-session deltas; it does **not** keep its own copy of the block list.

**Block numbers are FROZEN.** Identity is the block **name**; the number is a permanent label. A cut or deferred block stays as a labeled gap. Never renumber.

---

## The fork model

| Ref | Role | Rule |
|---|---|---|
| `main` | Read-only mirror of `upstream/main` | **Never commit here.** Sync: `git switch main && git pull --ff-only upstream main && git push origin main`. |
| `odin3-tuning` | The working branch — our delta as a stack on top of upstream | All sessions run here. Pushed to `origin`. |
| `pr/<topic>` | A branch cut from `main` for an upstream PR | Cherry-pick the relevant commits from `odin3-tuning`. Protocol docs never ride into a PR. |

**Staying current:** `odin3-tuning` is **rebased** onto `upstream/main` (not merged), so `git log upstream/main..odin3-tuning` is always exactly our delta. A rebase rewrites history and is pushed with `git push --force-with-lease origin odin3-tuning`. It is a **user-approved action at a quiet point** — never at session start, never inside `/end`. `git rerere` is enabled so a conflict resolved once is replayed automatically next time. Full rationale: `DECISIONS.md` → D-2.

**Other machine caveat:** after a rebase, a stale clone elsewhere must `git fetch && git reset --hard origin/odin3-tuning` (not `git pull`). The SessionStart hook flags this as "diverged" and stops.

---

## The device model

- **The repo is the record; the handheld is a deployment target.** Two kinds of device config (`DECISIONS.md` → D-4): **UI-owned** files (`power-profiles.conf`, `game-tweaks.json` — written by Armada Control) are tuned through the UI and *pulled back* into `device-state/` so every change is in git with a why; **repo-owned** files (anything with no UI writer) live in `device-overlay/` and are *pushed* by `tools/`, never hand-edited on the device. `docs/DEVICE.md` has the ownership table.
- **`/etc` before image.** Every tuning change goes through the device's writable `/etc` first, where it is a text edit to undo. Baking into the image (a reflash) happens only when a block's settings are stable, in its own block, with its own gate.
- **Boot path is sacred.** ABL, partitions, kernel args, and the boot image are never touched without a fresh verified backup step and an explicit per-instance go from the user. `docs/DEVICE.md` holds the backup locations.
- **Access:** SSH as `armada` to the IP in `docs/DEVICE.md`, key-based. `sudo` needs the password (also there). Turn SSH off in Armada Control when done for the day if the device leaves the home network.

---

## Session Start Protocol

Mostly automatic — the `SessionStart` hook runs Steps 0–3 and injects the docs. Typing `/start` forces the full protocol.

0. **Branch guard.** Not in a worktree, not on `claude/*`, **not on `main`**. Otherwise STOP (see `.claude/commands/start.md`).
1. **Sync guard, two remotes.** `git fetch origin --prune && git fetch upstream --prune`, then `git status -sb`. Behind origin + clean → `git pull --ff-only`. Dirty-and-behind or diverged → STOP and surface. Upstream drift (`git rev-list --count HEAD..upstream/main`) is **reported as a number, never acted on**.
2. Read `docs/CURRENT_STATE.md` (NEXT ACTION), the open `[ ]` lines of `docs/SESSION_LEDGER.md`, the last 5 lines of `docs/HANDOFF_LOG.md`, the ROADMAP spine.
3. `git update-index --really-refresh`, `git status`, `git log --oneline -5`. Anything dirty is a protocol violation from the last `/end` — flag it.
4. **CROSS-CHECK (mandatory).** NEXT ACTION vs spine's CURRENT block vs last HANDOFF "Next:" vs recent commits vs open ledger gates. Contradiction → STOP and surface; never pick one silently.
5. **Report:** block name + number / last session's result / NEXT ACTION / open ledger count + gates / **sync line** (origin currency + upstream drift count) / **device line** (overlay version `docs/DEVICE.md` says the handheld runs). Don't SSH at start unless the NEXT ACTION needs it.

**"Up to date" is only meaningful after a fetch**, and the cross-check cannot rescue a stale checkout: stale docs agree with each other perfectly.

---

## During-Session Rules

### Code quality (also in CLAUDE.md)
- Python and Bash only in our delta (that's what upstream uses). Files: 500-line soft cap, 800 hard. `shellcheck`-clean shell; `python -m py_compile`-clean Python.
- No DRY violations. 3+ uses = extract. No `utils/` dumping grounds.
- Comments explain *why*, not *what*. For a modified upstream file, the *why we diverged* also goes in `docs/CODEBASE_INDEX.md`.
- **Minimal delta.** Prefer overlay files and new files over editing upstream files; every edited upstream file is a future rebase conflict and a PR to write.

### Git
- Commit working changes incrementally. Never commit without the user confirming the change works (for device changes: they observed it).
- Never push outside `/end` unless asked. Never force-push except the sanctioned post-rebase `--force-with-lease` (D-2).
- Never commit to `main`.

### Device
- **Measure before you change** (`docs/WORK_STYLE.md`). No tuning change without a baseline of the signal it targets.
- **One variable at a time**, one pause per device-visible change, revert instructions in every hand-off.
- Anything applied to the device is committed in `device-overlay/` in the same session, and `docs/DEVICE.md` names the applied version. The two never silently differ.
- The user does not open a terminal on the device. Claude does the SSH work and reports results in one line; the user observes with ears, hands, eyes, and a clock.

### Index discipline (hook-enforced)
- Touching any file not yet in `docs/CODEBASE_INDEX.md` queues it. `/end` cannot complete while the queue is non-empty. Upstream files we never touch are never queued — the index is the fork delta by construction.

### Ledger discipline (moment-of-event rule)
- The moment work is queued or deferred in conversation — "next session," "before the rebuild," "check on the device later," "watch this" — append a `[ ]` line to `docs/SESSION_LEDGER.md` **right then**. The moment it resolves, strike it right then. Long sessions get context-compacted; end-of-session recall provably loses early facts.
- Not for block status (spine), hardware facts (`docs/DEVICE.md`), or roadmap ideas (ROADMAP backlog). One concept, one home. IDs never reused.

### `*kbdoc` rule
- When a lesson would still be true in a different project, say `*kbdoc` in-chat immediately with a one-liner. Articles are written after `/end` on request (`docs/WORK_STYLE.md`).

### Check stale messages before re-changing
- After a fix lands, confirm the issue is still current before changing again — the user may have queued a message before observing the fix.

---

## Session End Protocol

`.claude/commands/end.md` has the executable steps. Summary:

0. Branch guard → phantom-dirty refresh → **build guard** (py_compile + `bash -n` on changed files; configparser-parse every `.conf` in `device-overlay/` — a malformed overlay is silently dropped by `armada-powerd`).
1. Index: drain the pending queue → diff-based backstop against `upstream/main` → phantom-row check → ledger reconcile → **device parity check** (`docs/DEVICE.md` names the overlay version the handheld runs; repo/device disagreement is a recorded blocker, never silent).
2. Reconcile the ROADMAP spine, then overwrite `docs/CURRENT_STATE.md` (NEXT ACTION first; `**Current block:**` and `**Build status:**` lines are parsed by the statusline).
3. Append one HANDOFF line (≤300-char summary).
4. Commit `Session: …`, `git push` (pre-authorized, D-3), **clean-tree guarantee**, confirm `origin/odin3-tuning == HEAD`.
5. Report: accomplished / next / watch (incl. upstream drift + device parity) / open ledger items.

**Mini-wrap rule:** work after a completed `/end` closes with ledger lines → one delta-only HANDOFF line → CURRENT_STATE only if NEXT ACTION or build status changed → `Session followup:` commit + push → clean tree.

---

## Hooks Reference (`.claude/settings.json`)

| Hook | Trigger | Action |
|---|---|---|
| `SessionStart` (`startup\|resume\|clear`) | Session start | `session-start-context.py`: branch guard (worktree / `claude/*` / **`main`**), fetch **origin and upstream**, refuse to inject docs if behind origin, report upstream drift count, inject CURRENT_STATE + open ledger items + ROADMAP spine + last 5 HANDOFF lines + the cross-check directive. |
| `PostToolUse` (`Write\|Edit`) | After a file write/edit | `track-new-file.py`: queue the path if absent from the index; skips protocol bookkeeping, build output, caches, firmware blobs. |
| `Stop` | Turn end | `stop-clean-tree-check.py`: blocks the stop only if a `Session:` commit landed <5 min ago and the tree is dirty. |

Not a hook: `statusline.py` (`statusLine` key) shows `block | build | branch | dirty | upstream +N`. `validate-index.py` is the `/end` Step 1c phantom-row check.

---

## Slash Commands

| Command | What it does |
|---|---|
| `/start` | Session Start Protocol (forces the full version; the hook covers the normal case) |
| `/end` | Session End Protocol |

---

## Why this protocol is short

If a protocol is 300 lines, agents skim it and miss steps. Under ~200 lines with numbered steps and one source of truth per fact, agents follow it. Brevity is a feature.
