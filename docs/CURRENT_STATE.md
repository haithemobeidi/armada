# armada-odin3 — Current State

**Last updated:** 2026-09-05 (session 1 — protocol scaffold + device access; mid-session snapshot, `/end` not yet run)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**Close B0:** run the first `/end` cleanly (index drained, ledger reconciled, tree clean, pushed), then open a fresh session and confirm the SessionStart hook injects state, reports origin currency, and reports the upstream drift count. Then **B1 — Baseline instrumentation**: write the on-device CSV logger (temp / PWM / CPU+GPU freq / battery I·V / load, every 3 s), declare pause-points, record one idle session and one real play session.

**Current block:** B0 — Protocol + device access

**Build status:** working (hooks fire, `tools/odin.py status|probe|pull` verified against the device; nothing pushed to the device yet)

**Remote:** `origin/odin3-tuning` — to be pushed at `/end`. `upstream/main` is at `14230df`, **3 commits ahead** of this branch; rebase is a user decision (D-2), suggested before B1 work starts since the device already runs `20260904.14230df`.

---

## Optional loose ends (NOT the next step)

See open items in `docs/SESSION_LEDGER.md`.

---

## What happened this session

- Read the Checkpoint protocol + the KB `claude-project-template`, ported it for a fork with a device: `CLAUDE.md`, `PROTOCOL.md`, `DECISIONS.md` (D-1…D-8), `ROADMAP.md` (B0–B10 spine), `docs/WORK_STYLE.md`, `/start` + `/end`, five hook scripts (branch guard now also trips on `main`; sync guard fetches origin AND upstream; index scoped to the fork delta), statusline with upstream drift.
- SSH: enabled by the user in Armada Control; device found at `192.168.1.188`; key installed; `tools/odin.py` written (status / run / sudo / probe / pull / push-dry-run).
- First read-only snapshot → `docs/DEVICE.md`. Corrections to the first assessment: the fan has **no tachometer**; prime cores top at **4089.6 MHz** not 4320; the daemon uses the **average of the 3 hottest** zones; Armada Control has a **Fans tab** that already implements fan-stop and curve editing, so `power-profiles.conf` is **UI-owned** (D-4 rewritten; repo records it in `device-state/`).
- `docs/ARMADA_CONTROL.md`: every knob, what file it writes, what it means on this SoC.
- User did an OTA mid-session: device now `20260904.14230df` (rollback `20260903.33e0319`). First `device-state/` pull taken after it. Balanced `gpu_max=0.80` set by the user in the UI (reduced the whine a bit) is recorded there.
- Opus `HANDOFF.md` folded into `docs/DEVICE.md` (backups, gotchas, fan leads) and `ROADMAP.md`, then deleted.

---

## Active blockers

None.

---

## Notes & things to watch

- **Idle load average ~4–5** on the Steam home screen with `steamwebhelper` busy (67% + 58% CPU right after boot). B5 exists for this; don't attribute fan noise at idle to the curve alone until it's understood.
- `power_supply/battery/power_now` reads ~67.8 W while I×V ≈ 4.7 W — treat as unreliable until checked (B4).
- `abl.conf auto_update_enabled=1`: the bootloader can update itself at shutdown after an OTA. Know this before blaming boot behaviour on our changes.
- The SD card is the recovery path (pull it → Android boots). Stay on SD through tuning; B8 decides internal install with data.
