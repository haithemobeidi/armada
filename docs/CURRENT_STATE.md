# armada-odin3 — Current State

**Last updated:** 2026-09-07 (session 3 `/end` — B1 opened; rebase done; two play runs recorded)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**Finish B1:** (a) the **30-min idle recording** — Steam home screen, unplugged, screen on; `tools/baseline-logger.sh` is already on the device at `/var/tmp/armada-baseline/` (start it with `odin.py run`, pull with `odin.py get`); (b) the **pitch-vs-PWM sweep** with the user listening — declare pause-points first, daemon paused, temperature watchdog, PWM 0 → 255 in steps of 8, the user calls pitch/loudness per step (this is the test that splits physical from curve; see ROADMAP B1 run 2 notes); then write the B1 summary and close the block. Ask the user for the **in-game frame cap value** used in runs 1–2 (never confirmed).

**Current block:** B1 — Baseline instrumentation

**Build status:** working (`tools/odin.py` gained `put`/`get`, UTF-8 console, POSIX remote-path guard; `tools/baseline-logger.sh` v2 shellcheck-clean and smoke-tested on the device; `/end` guards all passed)

**Remote:** `origin/odin3-tuning` = HEAD after this `/end` push. Fork point = `upstream/main` = `04dbfc9` at the 2026-09-07 rebase (L-9; the hook reports fresh drift at start). `main` = `origin/main` = `14230df` (mirror, untouched). Device image `20260906.41d2e10`. **Other machine after the rebase:** `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.

---

## Optional loose ends (NOT the next step)

Open: L-3 (user: AYN warranty check), L-4 (user: off-PC ABL backup copy), L-5 (download-plateau experiment), L-6 (Performance-switch freeze repro, B3), L-13 (B4 sleep checks: Bluetooth across s2idle, `qcom_stats`, left-side warmth), L-15 (B4: `charge_control_*_threshold` reads 70/80 but is not enforced), L-16 (B3: `gpu_max` ratio is against 1100 MHz, so 0.80 is a no-op; B9 issue/PR). See `docs/SESSION_LEDGER.md`.

---

## What happened this session

- **Survey before starting:** upstream's 111 open issues read. Sleep history (Odin 3 #13 → s2idle default #365; still open: #264 Bluetooth drain — the rfkill fix exists only in the fake-suspend path and is commented out there; #265 warmth; #274 SM8550 never reaches deep sleep) and the gamescope frame-limiter undershoot (#45/#276/#322) recorded in ROADMAP B3/B4 and the ledger (L-13, L-14).
- **Owner's target stated and recorded** (ROADMAP intro + memory): battery first; 60 fps light / 30 fps modern (FF7 Crisis Core); 2–3 retuned profiles. B3/B4 gates reworded (L-14).
- **Rebase done (L-9, D-2):** `14230df → 04dbfc9`, 14 commits replayed, no conflicts, delta = 28 added files; pushed `--force-with-lease`.
- **B1 opened:** `tools/baseline-logger.sh` (read-only, one CSV row / 3 s, fan by hwmon name, 29 counted zones, coulomb counter) written, pushed, smoke-tested. `tools/odin.py`: `put`/`get`, UTF-8 console (a game title crashed `run`), POSIX-path guard (Git Bash rewrote `/var/tmp` into `C:/Program Files/Git/var/tmp` and the first `put` made a junk `~/C:` tree on the device — removed the same minute).
- **Run 1 (Eco, 30 min) and run 2 (Balanced, 16 min, stopped by the user), FINAL FANTASY RESONANCE DEMO, unplugged, in-game cap:** both ≈ 5 h of play per charge (coulomb counter and current sensor agree within 10 %; the % gauge is compressed above ~90 %). Balanced: +6 % power, prime cores unstarved (44 % at cap vs 99 %), a degree cooler, but the moderate curve sits on PWM 64 half the time and **64 is already "pretty loud" (high-pitched) to the owner**; Eco's relaxed curve held 51 at the same 61–63 °C. GPU pinned at 832 MHz > 80 % of the time on both. Full tables in ROADMAP B1.
- **Findings:** (1) `gpu_max` is a ratio of the 1100 MHz devfreq top, not the 832 MHz cap → the user's Balanced 0.80 and Eco's factory 0.80 are no-ops; 0.60 = 660 MHz (L-16; `docs/ARMADA_CONTROL.md` corrected). (2) Fan PWM carrier is 25.4 kHz (inaudible) — the tone is not the chopping frequency. (3) "Fan stays up" is not a bug: no hysteresis, 64 → 51 in ≤ 9 s; the *temperature* stays up because the GPU never leaves max clock. (4) The fan hunts 56 ↔ 64 every 6–12 s at a steady temperature (quantisation straddling a curve point) — a B2 lever. (5) The battery exposes `charge_control_{start,end}_threshold` (reads 70/80, not enforced, L-15); `charge_counter` ≈ 8.16 Ah full.
- DEVICE.md corrected: fan is `hwmon57` now (find by name), 16 `cpu-*` zones (29 counted), USB `online` flag, battery counters, PWM facts, `/var/tmp/armada-baseline` noted.

---

## Active blockers

None. Device/repo parity: **overlay v1** unchanged and applied; nothing under `/etc` touched this session. `/var/tmp/armada-baseline/` on the device = repo `tools/baseline-logger.sh` v2 + two CSVs (pulled to `device-data/`), nothing running.

---

## Notes & things to watch

- **Upstream drift:** 0 at the rebase (`04dbfc9`); the hook reports the new count at start. Rebase again at a quiet point if it grows (D-2).
- **Calling `odin.py put`/`get` from Git Bash needs `MSYS_NO_PATHCONV=1`** (the guard refuses a rewritten path rather than creating junk). `run` needs no special care now that the console is UTF-8.
- **In-game frame cap value for runs 1–2 is unknown** — ask; it decides whether the GPU-at-832 finding means "cap unreachable".
- **The % battery gauge lies above ~90 %** (98 → 92 read 12 %/h while the sensors said ~1.6 A). Use `bat_uah` deltas, not `%`, for drain.
- `power_supply/battery/power_now` still unverified (B4).
- Idle load average ~4–5 on the Steam home screen (B5) — 5.3–5.5 during play too.
- **Fresh deployments lose `/etc` and `/var`** (SSH, key, Power-tab tweaks, and now `/var/tmp/armada-baseline`). Re-`put` the logger after any installer run.
