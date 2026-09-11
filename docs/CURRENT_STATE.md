# armada-odin3 — Current State

**Last updated:** 2026-09-11 (session 4 `/end` — protocol migrated to the global KB layer; no device work)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**Rebase first, then finish B1.** (1) `odin3-tuning` is 50+ commits behind `upstream/main` — rebase at the start of the session (clean tree, D-2), push `--force-with-lease`, report. (2) Then B1: (a) the **30-min idle recording** — Steam home screen, unplugged, screen on; `tools/baseline-logger.sh` is on the device at `/var/tmp/armada-baseline/` (start with `odin.py run`, pull with `odin.py get`); (b) the **pitch-vs-PWM sweep** with the user listening — declare pause-points first, daemon paused, temperature watchdog, PWM 0 → 255 in steps of 8, the user calls pitch/loudness per step (see ROADMAP B1 run 2 notes); then write the B1 summary and close the block. Ask the user for the **in-game frame cap value** used in runs 1–2 (never confirmed).

**Current phase:** B1 Baseline instrumentation — idle recording + pitch-vs-PWM sweep pending (the statusline parses this line)

**Build status:** working (`tools/check-delta.sh` OK on all 33 delta files; secret scan clean; template drift check up to date)

**Remote:** `origin/odin3-tuning` = HEAD after this `/end` push. Fork point = `upstream/main` = `04dbfc9` at the 2026-09-07 rebase. `main` = `origin/main` = `14230df` (mirror, untouched). Device image `20260906.41d2e10`. **Other machine after a rebase:** `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.

---

## Optional loose ends (NOT the next step)

Open: L-3 (user: AYN warranty check), L-4 (user: off-PC ABL backup copy), L-5 (download-plateau experiment), L-6 (Performance-switch freeze repro, B3), L-13 (B4 sleep checks), L-15 (B4: charge thresholds not enforced), L-16 (B3: `gpu_max` ratio no-op; B9 issue/PR), L-17 (protocol migration gate — closes itself when the next fresh session's start→`/end` cycle passes). See `docs/SESSION_LEDGER.md`.

---

## What happened this session

- **Protocol migrated to the global Knowledge Base layer (D-10).** `PROTOCOL.md`, `docs/WORK_STYLE.md`, and the project `/start` + `/end` commands are gone; the global layer imported from `~/.claude/CLAUDE.md` took over. `CLAUDE.md` rewritten to the template outline (106 lines: fork model, device model, device-work rules, five explicit overrides). `.claude/protocol.json` carries the settings: `check_command = bash tools/check-delta.sh`, `push_policy = standing`, `protected_branches = ["main"]`, `upstream_ref = "upstream/main"`, generated-path skip list.
- **`tools/check-delta.sh`** replaces the old `/end` build guard: Python syntax, `bash -n` + shellcheck, configparser on every overlay `.conf`, unindexed-delta warnings.
- **Three template fixes upstreamed to the KB** (commit 9b5cc5e) and resynced here: `protected_branches` / `upstream_ref` for forks; the index queue written LF-only on Windows; the ledger reader skips the header's comment block (its example items used to be injected as open loops). Verified: guard trips on `main`, start hook reports upstream +50, statusline shows it.
- Ledger header replaced with the template's; L-13 cut to the loop + a pointer (analysis already in ROADMAP B4); L-17 queued.
- No device work. Nothing under `/etc` or `/var/tmp/armada-baseline/` touched.

---

## Active blockers

None. Device/repo parity: **overlay v1** unchanged and applied; `device-state/` unchanged.

---

## Notes & things to watch

- **Upstream drift: 50 at this `/end`.** The start hook reports the fresh count; rebase is the first thing next session (D-2).
- **Other projects on the template** will report "template drift" at their next start; a one-command resync (`check-template-drift.py --sync`) + commit fixes it. Their `protected_branches` stays empty — only this repo refuses `main`. The other machine needs a KB pull + `install-global.py`.
- **First fresh session on the new layer = L-17's test.** If the start hook injects nothing, check `python --version` inside Claude Code's shell and `CLAUDE_PROJECT_DIR` (template README → Troubleshooting).
- **Calling `odin.py put`/`get` from Git Bash needs `MSYS_NO_PATHCONV=1`.**
- **In-game frame cap value for runs 1–2 is unknown** — ask.
- **The % battery gauge lies above ~90 %** — use `bat_uah` deltas, not `%`, for drain.
- `power_supply/battery/power_now` still unverified (B4). Idle load average ~4–5 on the Steam home screen (B5).
- **Fresh deployments lose `/etc` and `/var`** — re-`put` the logger after any installer run.
