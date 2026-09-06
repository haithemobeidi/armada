# armada-odin3 — Codebase Index (fork delta)

**Purpose:** one line per file **this fork adds or changes** relative to `upstream/main`. Upstream's ~500 files are not catalogued (DECISIONS D-5): they are documented by upstream, and rows for them would rot on every rebase. A **modified upstream file** gets a row that says what we changed and **why we diverged** — that text is the seed of its eventual PR.

**Maintenance:** enforced by the `PostToolUse` hook (`.claude/scripts/track-new-file.py`) → `.claude/pending-index-updates.txt` → `/end` Step 1. Reverse check: `validate-index.py`.

**Last updated:** 2026-09-05 (session 1).

---

## Repo root

| File | Purpose |
|---|---|
| `CLAUDE.md` | Auto-loaded project context: what this fork is, locked decisions table, code rules, navigation docs, work-style triggers. |
| `PROTOCOL.md` | Single source of truth for the session lifecycle, the fork model (main mirrors upstream, rebase policy), the device model (repo is the record, `/etc` first), hooks, commands. |
| `ROADMAP.md` | Status-at-a-glance spine (B0–B10, frozen numbers) + one section per block + backlog. |
| `DECISIONS.md` | D-1…D-8: fork layout, rebase-over-merge, push authorization, `/etc`-first + config ownership, index scope, no worktrees, boot-path safety, whole-OS scope. |
| `.gitignore` | **Modified upstream file.** Added Claude protocol state (`pending-index-updates.txt`, `settings.local.json`, `worktrees/`) and `device-data/` (raw device pulls, regenerated). Why: protocol bookkeeping must never be committed; raw logs belong in summaries, not git. Never upstreamed. |
| `.gitattributes` | Forces LF in the working copy on every platform (`* text=auto eol=lf`) + binary markers for firmware/blobs. Why: this Windows checkout was warning "LF will be replaced by CRLF" on every file, and CRLF must never reach the device's `/etc`. Upstream has no `.gitattributes`; candidate to upstream. |

## docs/

| File | Purpose |
|---|---|
| `docs/CURRENT_STATE.md` | Rolling snapshot: NEXT ACTION, current block, build status, this-session deltas, watch list. Overwritten at `/end`. |
| `docs/HANDOFF_LOG.md` | Append-only one line per session. |
| `docs/SESSION_LEDGER.md` | Append-and-strike ledger of open session-scoped items (L-n IDs). |
| `docs/WORK_STYLE.md` | Long-form rules: measure-before-change, device-observable pause-points, don't-reinvent, grounded pushback, one source of truth, pacing, audits, `*kbdoc`. |
| `docs/DEVICE.md` | The handheld: identity, SSH access, CPU/GPU frequency tables, thermal zones + fan (no tach), power supplies, storage layout, config ownership table, **applied overlay version**, backups + recovery ladder, Android-side gotchas, fan-noise leads. |
| `docs/ARMADA_CONTROL.md` | Every Armada Control setting by tab, the file it writes, and what it means on SM8750; what has no UI. |

## tools/

| File | Purpose |
|---|---|
| `tools/odin.py` | The one door to the device over OpenSSH: `status`, `run`, `sudo`, `probe` (→ `device-data/`), `pull` (UI-owned configs → `device-state/`), `push` (`device-overlay/etc/**` → `/etc`, dry-run unless `--yes`, restarts `armada-powerd`). |

## device-overlay/ (repo-owned, pushed to the device)

| File | Purpose |
|---|---|
| `device-overlay/README.md` | Layout rules: mirrors `/etc`; only files with no Armada Control writer; every file's header says what it does and how to revert. v1 since 2026-09-06. |
| `device-overlay/etc/udev/rules.d/99-armada-hide-internal-ufs.rules` | udev rule: `UDISKS_IGNORE=1` on every block device under the SoC's UFS host (`KERNELS=="*.ufs"`), so udisks flags the internal chip `HintIgnore` and Steam's Storage page stops listing it as an empty 464.5 GB drive (L-12). Header carries the apply/revert commands. Upstream candidate: matches by parent chain, not drive letter. |

## device-state/ (UI-owned configs as last pulled — a record, never pushed)

| File | Purpose |
|---|---|
| `device-state/PULLED_AT.txt` | Timestamp + host of the last `odin.py pull`. |
| `device-state/etc__armada__power-profiles.conf` | Armada Control's `/etc` overrides (Power + Fans tabs). Currently: Balanced `gpu_max=0.80`. |
| `device-state/etc__armada__abl.conf` | `auto_update_enabled=1` — bootloader auto-update at shutdown is on. |
| `device-state/var__lib__armada__powerd.state` | Daemon's persisted profile / GPU level / manual clock. |

## .claude/

| File | Purpose |
|---|---|
| `.claude/settings.json` | Statusline + hooks wiring (SessionStart / PostToolUse / Stop). |
| `.claude/commands/start.md` | `/start`: branch guard (worktree, `claude/*`, `main`), two-remote sync guard, read state, cross-check, report incl. upstream drift + device line. |
| `.claude/commands/end.md` | `/end`: guards, build guard (py_compile / bash -n / configparser on overlays), index drain + backstop vs `upstream/main` + phantom rows, ledger reconcile, **device parity check**, spine + CURRENT_STATE, handoff line, commit + push + clean tree. |
| `.claude/scripts/session-start-context.py` | SessionStart hook: branch guard, fetch origin + upstream, refuse stale injection, upstream drift count, inject CURRENT_STATE + open ledger + spine + last 5 handoff lines + cross-check directive. |
| `.claude/scripts/track-new-file.py` | PostToolUse hook: queue any touched file absent from this index; skips bookkeeping, `.claude/`, build output, caches, firmware/binary suffixes. |
| `.claude/scripts/stop-clean-tree-check.py` | Stop hook: block the stop only if a `Session:` commit landed <5 min ago and the tree is dirty. |
| `.claude/scripts/validate-index.py` | Reverse index check: rows pointing at files that no longer exist. |
| `.claude/scripts/statusline.py` | `block | build | branch | dirty | upstream +N` from CURRENT_STATE + local git refs. |
