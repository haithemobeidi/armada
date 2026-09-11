# armada-odin3 — Codebase Index (fork delta)

**Purpose:** one line per file **this fork adds or changes** relative to `upstream/main`. Upstream's ~500 files are not catalogued (DECISIONS D-5): they are documented by upstream, and rows for them would rot on every rebase. A **modified upstream file** gets a row that says what we changed and **why we diverged** — that text is the seed of its eventual PR.

**Maintenance:** enforced by the `PostToolUse` hook (`.claude/scripts/track-new-file.py`) → `.claude/pending-index-updates.txt` → `/end` Step 1. Reverse check: `validate-index.py`.

**Last updated:** 2026-09-11 (protocol migration, D-10).

---

## Repo root

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project file — what is different about this repo (fork model, device model, device-work rules, overrides of the global rules, pointers). Augments the global work style + protocol imported from the Knowledge Base (D-10). |
| `ROADMAP.md` | Status-at-a-glance spine (B0–B10, frozen numbers) + one section per block + backlog. |
| `DECISIONS.md` | D-1…D-10: fork layout, rebase-over-merge, push authorization, `/etc`-first + config ownership, index scope, no worktrees, boot-path safety, whole-OS scope, internal install, protocol migration to the global layer. |
| `.gitignore` | **Modified upstream file.** Added Claude protocol state (`pending-index-updates.txt`, `settings.local.json`, `worktrees/`) and `device-data/` (raw device pulls, regenerated). Why: protocol bookkeeping must never be committed; raw logs belong in summaries, not git. Never upstreamed. |
| `.gitattributes` | Forces LF in the working copy on every platform (`* text=auto eol=lf`) + binary markers for firmware/blobs. Why: this Windows checkout was warning "LF will be replaced by CRLF" on every file, and CRLF must never reach the device's `/etc`. Upstream has no `.gitattributes`; candidate to upstream. |

## docs/

| File | Purpose |
|---|---|
| `docs/CURRENT_STATE.md` | Rolling snapshot: NEXT ACTION, current block, build status, this-session deltas, watch list. Overwritten at `/end`. |
| `docs/HANDOFF_LOG.md` | Append-only one line per session. |
| `docs/SESSION_LEDGER.md` | Append-and-strike ledger of open session-scoped items (L-n IDs). |
| `docs/DEVICE.md` | The handheld: identity, SSH access, CPU/GPU frequency tables, thermal zones + fan (no tach), power supplies, storage layout, config ownership table, **applied overlay version**, backups + recovery ladder, Android-side gotchas, fan-noise leads. |
| `docs/ARMADA_CONTROL.md` | Every Armada Control setting by tab, the file it writes, and what it means on SM8750; what has no UI. |

## tools/

| File | Purpose |
|---|---|
| `tools/odin.py` | The one door to the device over OpenSSH: `status`, `run`, `sudo`, `probe` (→ `device-data/`), `pull` (UI-owned configs → `device-state/`), `push` (`device-overlay/etc/**` → `/etc`, dry-run unless `--yes`, mode 0755 for shebang files so sleep/udev hooks run, restarts `armada-powerd`), `put` (one file → device, LF-normalised, `+x` for scripts), `get` (one file → `device-data/`). Console forced to UTF-8 (a game title crashed `run` on cp1252, 2026-09-07); `put`/`get` refuse a non-POSIX remote path because Git Bash rewrites `/var/...` into `C:/Program Files/Git/var/...` unless `MSYS_NO_PATHCONV=1`. |
| `tools/check-delta.sh` | `/end` check (`check_command` in `protocol.json`): over every file in the fork delta vs the merge-base with `upstream/main` — Python syntax, `bash -n` + shellcheck on shell files, configparser on every `device-overlay/**.conf` (a malformed one is dropped silently by `armada-powerd`); warns on delta files missing from this index. |
| `tools/baseline-logger.sh` | B1's read-only CSV logger, run **on the device** (`put` it to `/var/tmp/armada-baseline/`, `get` the CSV). One row per 3 s: the daemon's own D-Bus `Temperature`/`FanPwm`/`Profile`, raw `pwm1` (fan found by hwmon name), top-3 average and max of the counted thermal zones (same zone set and average as `armada-powerd`), CPU policy0/policy6 and GPU MHz, battery status/%/µA/µV/W, USB `online`, load, Steam appid. Never writes sysfs; `OUT.csv.pid` holds the PID for `kill`. |

## device-overlay/ (repo-owned, pushed to the device)

| File | Purpose |
|---|---|
| `device-overlay/README.md` | Layout rules: mirrors `/etc`; only files with no Armada Control writer; every file's header says what it does and how to revert. v1 since 2026-09-06. |
| `device-overlay/etc/udev/rules.d/99-armada-hide-internal-ufs.rules` | udev rule: `UDISKS_IGNORE=1` on every block device under the SoC's UFS host (`KERNELS=="*.ufs"`), so udisks flags the internal chip `HintIgnore` and Steam's Storage page stops listing it as an empty 464.5 GB drive (L-12). Header carries the apply/revert commands. Upstream candidate: matches by parent chain, not drive letter. |
| `device-overlay/etc/systemd/system-sleep/20-odin3-wifi-off-in-sleep` | systemd-sleep hook: `rfkill block wifi` on `pre`, `unblock` on `post`. Why we diverge: upstream only lets NetworkManager disconnect at suspend; the WCN7860 stays powered and costs ~0.28 W all night on this unit (10-min sleeps: 0.75 W → 0.47 W, ROADMAP B4, 2026-09-11). Revert: delete the file; `rfkill unblock wifi` if a wake ever leaves it off. Pushed 2026-09-11 14:23 (overlay v2). |

## device-state/ (UI-owned configs as last pulled — a record, never pushed)

| File | Purpose |
|---|---|
| `device-state/PULLED_AT.txt` | Timestamp + host of the last `odin.py pull`. |
| `device-state/etc__armada__power-profiles.conf` | Armada Control's `/etc` overrides (Power + Fans tabs). Currently: Balanced `gpu_max=0.80`. |
| `device-state/etc__armada__abl.conf` | `auto_update_enabled=1` — bootloader auto-update at shutdown is on. |
| `device-state/var__lib__armada__powerd.state` | Daemon's persisted profile / GPU level / manual clock. |

## .claude/ (template-managed unless noted — never hand-edit; `check-template-drift.py` compares against the KB template)

| File | Purpose |
|---|---|
| `.claude/protocol.json` | **Project-owned.** The scripts' settings: `check_command = bash tools/check-delta.sh`, `push_policy = standing` (D-3), `protected_branches = ["main"]` (D-1), `upstream_ref = "upstream/main"` (D-2), generated-path skip list for the index hook, ledger caps, single track. |
| `.claude/settings.json` | Hook wiring (SessionStart / PostToolUse / Stop) + statusline + read-only Bash allowlist. |
| `.claude/agents/planner.md` | Read-only planner subagent — implementation plans with declared pause-points. |
| `.claude/agents/reviewer.md` | Read-only reviewer subagent — independent diff review against the rules. |
| `.claude/agents/explorer.md` | Read-only explorer subagent — adjacent questions with `file:line` citations. |
| `.claude/scripts/protocol_config.py` | Shared loader for `protocol.json` + template-drift helpers; imported by every script. |
| `.claude/scripts/session-start-context.py` | SessionStart hook — worktree guard, global-install check, fetch origin + stale refusal, trips on `main` (`protected_branches`), fetches upstream and reports the drift count (`upstream_ref`), injects CURRENT_STATE + open ledger (capped, comment blocks skipped) + spine + handoff lines + drift note + cross-check directive. |
| `.claude/scripts/track-new-file.py` | PostToolUse hook — queues unindexed paths to `pending-index-updates.txt` (skip prefixes from `protocol.json`). |
| `.claude/scripts/stop-clean-tree-check.py` | Stop hook — blocks a stop when a Session commit just landed and the tree is still dirty. |
| `.claude/scripts/validate-index.py` | `/end` Step 1c — flags index rows pointing at deleted files (a rebase that removed an annotated upstream file shows up here). |
| `.claude/scripts/scan-secrets.py` | `/end` Step 0c — content-based secret scan of everything heading for a commit; `--history` audits everything pushable. |
| `.claude/scripts/check-template-drift.py` | Compares this project's protocol machinery against the Knowledge Base template; `--sync` resyncs. |
| `.claude/scripts/statusline.py` | Statusline — phase + build status from CURRENT_STATE, branch + dirty count from git, `upstream +N` against the local `upstream/main` ref (fresh as of the last fetch). |
