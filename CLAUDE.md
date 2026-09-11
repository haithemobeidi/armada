# armada-odin3 — Project file

> A personal fork of ArmadaOS, tuned end to end for one AYN Odin 3 and one owner's use.

**This file augments the global rules** (work style + session protocol, imported from the Knowledge Base on every machine). It holds only what is different about this repo: **a fork with an active upstream**, and **a physical device that can be bricked**. The scripts' settings live in `.claude/protocol.json`.

---

## What this is

[Armada](https://armadaos.dev/) is a SteamOS-like Fedora bootc image for ARM64 gaming handhelds (Steam via FEX + Proton, Gaming Mode via gamescope, KDE Desktop Mode). This repo is Haithem's fork. The goal is to take the OS **A to Z, slowly but sure**: measure every subsystem on the actual device, tune it for this hardware and this owner, keep anything general upstreamable, and keep the device safe throughout.

The device is an **AYN Odin 3** (Snapdragon 8 Elite, SM8750), Armada installed to internal storage next to a 16 GiB Android (D-9). Hardware, access, and what is applied to it: `docs/DEVICE.md`. The plan: `ROADMAP.md`. Why: `DECISIONS.md`.

## Locked stack

| Area | Choice |
|---|---|
| Repo shape | Fork of `armada-os/armada`. `main` mirrors `upstream/main` and **never receives commits**. All work on **`odin3-tuning`**; `pr/<topic>` branches are cut from `main` for upstream PRs. (D-1) |
| Staying current | **Rebase** `odin3-tuning` onto `upstream/main`, push `--force-with-lease`. Claude's call at a quiet point, always reported. `git rerere` on. (D-2) |
| Where tuning lives | Device `/etc` first; the image rebuild is its own late block (B10). UI-owned configs are tuned in Armada Control and **recorded** in `device-state/`; repo-owned files live in `device-overlay/` and are **pushed** by `tools/odin.py`. (D-4) |
| Boot path | ABL / partitions / kernel args / image / installer: fresh verified backup + explicit per-instance go, own block. (D-7) |
| Languages | Python 3 and Bash, like upstream. No new runtimes in the delta. |
| Method | Whole OS; fan noise and battery first; **measure before every change**. (D-8) |

**Stack-specific quality rules** (the global 500/800 caps, DRY at 3, no `utils/`, comments explain why — all apply):
- **Minimal delta.** A new file or an `/etc` drop-in beats editing an upstream file; every edited upstream file is a future rebase conflict and a PR to write.
- **Shell is `shellcheck`-clean, Python compiles, every `.conf` under `device-overlay/` parses** — `tools/check-delta.sh` enforces all three at `/end` (it is the `check_command`).
- **Every device change carries its revert**, in the hand-off block and in the commit message.
- **A modified upstream file's index row says why we diverged** — that text seeds the eventual PR description (D-5).

## Where the code is

| Path | What it is | Status |
|---|---|---|
| `system_files/`, `build_files/`, `decky/` | Upstream's OS files, image recipe, and the Armada Control plugin. **The code is the documentation for this OS** — read the script rather than guess. | upstream; rarely edited |
| `device-overlay/` | Repo-owned `/etc` files (no UI writer). Pushed to the device. | ours |
| `device-state/` | UI-owned configs as last pulled from the device. A record, never pushed. | ours |
| `device-data/` | Raw pulls and CSVs from the device. git-ignored; summaries go in ROADMAP. | ours |
| `tools/` | `odin.py` (the one door to the device over SSH), `baseline-logger.sh` (runs on the device), `check-delta.sh` (`/end` check). | ours |
| `docs/DEVICE.md`, `docs/ARMADA_CONTROL.md` | Hardware facts + applied overlay version; every Armada Control setting, the file it writes, its effect on this SoC. | ours |
| `abl/` | Bootloader backup/flash script templates and the release table. Boot path — D-7. | ours |

`docs/CODEBASE_INDEX.md` is scoped to the **fork delta** (D-5): upstream files we never touch are never indexed.

## How to run and test

```
python tools/odin.py status            # is the device reachable
python tools/odin.py probe             # read-only snapshot → device-data/
python tools/odin.py pull              # UI-owned configs → device-state/
python tools/odin.py push [--yes]      # device-overlay/etc/** → /etc (dry run without --yes)
bash tools/check-delta.sh              # /end check: python syntax, bash -n, shellcheck, overlay .conf parse
```

**The user does not open a terminal on the device.** Claude does the SSH work and reports in one line; the user's instruments are ears, hands, eyes, the battery percentage, and a clock. From Git Bash, `odin.py put`/`get` need `MSYS_NO_PATHCONV=1`.

## Project rules

**Session start and end — additions to the global steps:**
- **At session start** → the hook reports the upstream drift count (`upstream_ref` in `protocol.json`); state it, plus the overlay version `docs/DEVICE.md` says the device runs. Never rebase during start or end. Don't SSH at start unless the NEXT ACTION needs it.
- **At `/end` Step 1b** → the backstop covers the whole fork delta (`git diff --name-only $(git merge-base HEAD upstream/main)`), not just `HEAD`; `check-delta.sh` prints unindexed delta files as warnings.
- **At `/end`, if `device-overlay/` or the device changed** → `docs/DEVICE.md` "Applied overlay" names the version the device runs. Repo/device disagreement is a recorded blocker in CURRENT_STATE, never silent.
- **At `/end` Step 4b** → confirm `origin/odin3-tuning == HEAD`, not `origin/main`.
- **On the other machine after a rebase** → `git fetch && git reset --hard origin/odin3-tuning`, never `git pull`; the start hook reports "diverged" and stops.

**Device work:**
- **Before any change to the device or `device-overlay/`** → baseline the signal the change targets (temperature, PWM, clocks, watts — whichever the block is about). Raw pulls to `device-data/`; the numbers that matter to the block's ROADMAP section. One variable at a time; same game or idle screen, same charge state; say the conditions.
- **The fan has no tachometer** → "PWM 96" is a fact, "3000 RPM" is a guess; write the fact. The user's perceived noise and warmth are measurements: record them as "user reports" next to the PWM and temperature at that moment.
- **Pause-points on the device** (the global pause rule, with these specifics) → always a pause when an overlay file lands on the device; a service is enabled, disabled, or masked; a measurement script runs for the first time; anything on the boot path changes; a new profile or per-game tweak becomes selectable. Hand-off shape: **What changed on the device** (paths / services, and how to revert) / **What to observe** (hear, feel, see, time — no terminal) / **What I haven't done yet**. Safety net: 3+ device-side values changed without a pause means one was missed. A read-only logger IS a change the first time it runs.
- **Anything applied to the device** → committed in `device-overlay/` the same session, and `docs/DEVICE.md` names the applied version. The two never silently differ.
- **Before touching a setting more than one surface reads or writes** (factory config, `/etc`, Armada Control UI, Steam QAM over D-Bus, per-game tweaks) → list every surface, decide who owns the file (`docs/DEVICE.md` ownership table, D-4), check parity after: UI, file, `armada-power status`.
- **Never launch a game on the device unasked** → announce first; the user may have Steam open on the desktop.
- **Before designing a mechanism** → check upstream first (`git log upstream/main --oneline -- <path>`; it merges several PRs a day), then ROCKNIX, SteamOS (`jupiter-fan-control`, vendored here as `jupiter-hw-support`), Bazzite, ChimeraOS. Cite the source in the index row.
- **Audits** → scope is the fork delta and the device's runtime state, never upstream's code style. Name the measured win first ("service X costs Y mW at idle").

**Repo:**
- **Never commit to `main`.** The start hook trips on it (`protected_branches`); a session that finds itself there runs `git switch odin3-tuning` (tree clean) before anything else.
- **Never commit a device change the user has not observed.**
- **The ledger is not for hardware facts** (`docs/DEVICE.md`) or block status (the spine).

## Overrides of global rules

| Global rule | Override here | Why | Since |
|---|---|---|---|
| Sessions run on `main` | Sessions run on `odin3-tuning`; `main` is a read-only mirror of `upstream/main` | Fork: the delta must stay a clean stack on top of upstream (D-1) | 2026-09-04 |
| Push policy `ask` | `push_policy: standing` — `/end` and mini-wraps push to `origin/odin3-tuning` | Work continues from the other machine (D-3) | 2026-09-05 |
| Force pushes need per-instance confirmation | `git push --force-with-lease origin odin3-tuning` right after a rebase is Claude's call at a quiet point, always reported. No other force push, ever. | The user delegated repo mechanics (D-2, amended) | 2026-09-05 |
| Test lists are user-clickable | Observe lists are user-hearable / touchable / readable: fan, back panel, battery %, a clock | There is no UI to click; the user never opens a terminal on the device | 2026-09-05 |
| Mock before you build | Not applicable | No UI is built here | 2026-09-05 |

## Where things live

| Thing | Where |
|---|---|
| Plan + status spine | `ROADMAP.md` (blocks B0–B10, numbers frozen; backlog at the bottom) |
| Why | `DECISIONS.md` (D-1 … D-10) |
| Hardware, SSH, sysfs, config ownership, backups, applied overlay | `docs/DEVICE.md` — read before any device work |
| Armada Control settings → files → effect on this SoC | `docs/ARMADA_CONTROL.md` — read before touching power / fan / per-game behaviour |
| Fork delta, one line per file | `docs/CODEBASE_INDEX.md` |
| Upstream issue tracker | `github.com/armada-os/armada/issues` (sleep #264 / #265 / #274; frame limiter #45 / #276 / #322) |
| Knowledge Base clone | `C:/Users/haith/Documents/Vibe Projects/Knowledge Base` (pull before writing a lesson) |

## Subagents — read-only by design

`.claude/agents/` ships the template's `planner`, `reviewer`, `explorer`. All read-only; the main session makes every edit. The `kb` agent searches the Knowledge Base.
