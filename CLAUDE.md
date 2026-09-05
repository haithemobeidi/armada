# armada-odin3 — Project Context for Claude

> A personal fork of ArmadaOS, tuned end to end for one AYN Odin 3 and one owner's use.

This file is auto-loaded into every Claude session. Read it first.

## What is this?

[Armada](https://armadaos.dev/) is a SteamOS-like Fedora bootc image for ARM64 gaming handhelds (Steam via FEX + Proton, Gaming Mode via gamescope, KDE Desktop Mode). This repo is **Haithem's fork**, and the goal is to take the OS **A to Z, slowly but sure**: measure every subsystem on the actual device, tune it for this hardware and this owner, keep anything general upstreamable, and keep the device safe throughout.

The device is an **AYN Odin 3** (Snapdragon 8 Elite, SM8750), currently booting Armada from a 1 TB SD card with stock Android intact on internal storage. Everything about the hardware, how to reach it, and what's applied to it is in [`docs/DEVICE.md`](./docs/DEVICE.md).

The plan and where we are: [`ROADMAP.md`](./ROADMAP.md). Why things are the way they are: [`DECISIONS.md`](./DECISIONS.md).

---

## Locked decisions (details in `DECISIONS.md`)

| Area | Choice |
|---|---|
| Repo shape | Fork of `armada-os/armada`. `main` mirrors upstream, never committed to. Work on **`odin3-tuning`**. (D-1) |
| Staying current | **Rebase** onto `upstream/main`, `--force-with-lease` to our branch. Claude's call at quiet points, always reported. `git rerere` on. (D-2) |
| Pushes | Plain push at `/end` pre-authorized. No other force pushes. (D-3) |
| Where tuning lives | Device `/etc` first; image rebuild is its own late block. UI-owned configs are tuned through Armada Control and **recorded** in `device-state/`; repo-owned files live in `device-overlay/` and are **pushed**. (D-4) |
| Codebase index | Scoped to the fork delta. A modified upstream file's entry says why we diverged. (D-5) |
| Sessions | Terminal, main checkout, no worktrees. (D-6) |
| Boot path | ABL / partitions / kernel args / image / internal install: fresh backup + explicit per-instance go, own block. (D-7) |
| Scope and method | Whole OS, fan noise first, **measure before every change**. (D-8) |
| Languages | Python 3 and Bash, like upstream. No new runtimes in the delta. |

---

## Code quality rules (non-negotiable)

1. **Minimal delta.** Prefer a new file or an `/etc` drop-in over editing an upstream file. Every edited upstream file is a future rebase conflict and a PR to write.
2. **Files do ONE thing.** Soft cap 500 lines, hard cap 800. Propose a split before crossing 500.
3. **No DRY violations.** 3+ identical uses = extract. Don't extract at 2 when the abstraction might be wrong.
4. **No `utils/` dumping grounds.** Group by purpose (`tools/`, `device-overlay/etc/...`).
5. **Shell is `shellcheck`-clean; Python compiles.** `/end` runs both on changed files.
6. **Comments explain WHY, not WHAT.** For a modified upstream file, the why also goes in the index entry.
7. **Every device change carries its revert**, in the hand-off block and in the commit message.
8. **Per-file documentation lives in [`docs/CODEBASE_INDEX.md`](./docs/CODEBASE_INDEX.md)**, hook-enforced (see `PROTOCOL.md`).

---

## Navigation docs — read on demand, never auto-load

| Doc | Purpose | When to read |
|---|---|---|
| `CLAUDE.md` (this) | Rules + pointers | Auto-loaded. |
| `docs/DEVICE.md` | Hardware facts, SSH access, sysfs paths, config ownership, backups, **applied overlay version** | Before any device work. |
| `docs/ARMADA_CONTROL.md` | Every setting Armada Control exposes, which file it writes, and what it does on this SoC | Before touching power/fan/per-game behaviour. |
| `ROADMAP.md` | Status spine + block plan + backlog | Session start (hook injects the spine); before scoping a block. |
| `docs/CODEBASE_INDEX.md` | One line per file in the fork delta | When locating our changes. |
| `docs/WORK_STYLE.md` | Long-form work-style rules | When a rule's trigger applies (table below). |
| `DECISIONS.md` | Why | When about to question or change a locked decision. |
| Upstream source | `system_files/` (what's on the device), `build_files/` (how the image is made), `decky/` (Armada Control plugin) | The code is the documentation for this OS; the docs site is thin. Read the relevant script rather than guessing. |

---

## Work style — long-form rules in `docs/WORK_STYLE.md`

| Rule | Read it when |
|---|---|
| **Measure before you change** | Before any change to the device or `device-overlay/`. Baseline the signal first; one variable at a time; same conditions. |
| **Pause at device-observable milestones** | Before starting any sub-phase. Declare 2–4 pause-points; stop at each; every hand-off names the revert and asks the user only for things they can hear, feel, see, or time. |
| **Don't reinvent the wheel** | Before designing a mechanism — check upstream first (it moves daily), then ROCKNIX / SteamOS / Bazzite / ChimeraOS. |
| **Grounded pushback + grounded agreement** | Any time you have an opinion on the user's idea — evidence both ways, subjective calls flagged. |
| **One source of truth — data AND behavior** | Before changing anything with multiple writers (factory config, `/etc`, Armada Control UI, Steam QAM, per-game tweaks). |
| **Methodical pacing** | Always. "Slowly but sure" is the instruction. |
| **Audits target real optimization** | Before a cleanup pass — name the measured win. |
| **`*kbdoc`** | When a lesson would be true in a different project — say so in-chat at once. |

**The user is not a Linux terminal user on the device.** Claude does the SSH work and reports in one line. The user's job at a pause is to play, listen, touch the back panel, and read the battery percentage.

---

## Session protocol

**See [`PROTOCOL.md`](./PROTOCOL.md)** for the full lifecycle (start / during / end), the fork model, the device model, hooks, and slash commands. Single source of truth — do not duplicate session rules here.

## Subagents

None configured. Don't spawn writer agents; the main session is the single source of changes. Read-only research agents are fine when a question is adjacent to the current task.
