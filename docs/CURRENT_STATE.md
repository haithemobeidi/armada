# armada-odin3 — Current State

**Last updated:** 2026-09-06 (session 2 `/end` — B0 closed; storage decision made (D-9); Android-side save fix)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**Run the internal install (ledger L-7, decision D-9):** Armada booted from the SD card → verify the PC ABL backup hash → `armada-installer install --userdata-gib 16` as root over SSH (or the GUI, slider at 16) → power off, SD card out, boot from internal. Then L-8 (probe, rewrite `docs/DEVICE.md` Storage + Boot) and L-9 (rebase, 14 behind). **Then open B1 — Baseline instrumentation.**

**Current block:** B8 — Storage decision

**Build status:** working (hooks verified in a fresh session; `tools/odin.py` used all session; `/end` build-guard glob fixed so `bash -n` no longer runs on `tools/*.py`)

**Remote:** `origin/odin3-tuning` = HEAD after this `/end`. `main` = `origin/main` = `14230df`; `upstream/main` is 14 commits ahead (L-9).

---

## Optional loose ends (NOT the next step)

Open: L-3 (user: AYN warranty check), L-4 (user: off-PC copy of the ABL backup — **more urgent now**: the device-side copy dies with Android's `userdata` in L-7), L-5 (download-plateau experiment; re-run on internal per L-8), L-6 (game froze on a Performance switch mid shader-compile; B3 repro). See `docs/SESSION_LEDGER.md`.

---

## What happened this session

- **B0 closed:** the SessionStart hook did its job in this fresh session (L-2).
- **Android-side detour (not Armada):** GameNative 1.2.0's ZENONIA 1 save was not exporting or reaching Steam Cloud. Root cause: the game's Sep-3 hotfix (v1.0.1) added Steam Cloud rules and a per-SteamID save folder; the launch-day build saved one folder up, so GameNative (which only looks where Steam's rules point) found nothing. Fix: updated the game in GameNative, it migrated the save, then "Keep local" on the launch-time conflict uploaded it. Verified by the user on the desktop. Reach-the-device notes are in Claude's memory, not this repo; the general lessons went to the KB.
- **Storage decision (D-9):** internal install, Android kept at 16 GiB. Numbers from the installer source: floor 8 GiB, GUI default 32, Armada reserve ~33.6 GiB, revert via `reset` / ABL UNINSTALL CFW. Go given; **not executed** — device still boots `root=mmcblk0p3` (checked live at this `/end`).
- Protocol: `/end` build guard's `bash -n` glob narrowed to `tools/*.sh` (it was choking on `tools/odin.py`).

---

## Active blockers

None. Device/repo parity: nothing in `device-overlay/` yet (v0); `device-state/` not re-pulled (no device config changed this session).

---

## Notes & things to watch

- **Upstream drift: 14 commits** at this `/end` (latest `c68b36a`, bottom-screen brightness persistence) — L-9, rebase at the first quiet point.
- **Internal install caveats (L-7):** the installer refuses if a partition lies after `userdata` (this unit: `sda17` is last, should pass). After the install the SD card is still a full Armada; decide its role in L-8.
- `abl.conf auto_update_enabled=1`: the bootloader can update itself at shutdown after an OTA (D-7 awareness).
- **Idle load average ~4–5** on the Steam home screen (`steamwebhelper`). B5.
- `power_supply/battery/power_now` ≈ 67.8 W vs I×V ≈ 4.7 W — unreliable until checked (B4).
- The wireless-ADB / GameNative notes for the Android side live in Claude's memory; they become moot after L-7.
