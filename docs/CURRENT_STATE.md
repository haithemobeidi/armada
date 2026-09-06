# armada-odin3 — Current State

**Last updated:** 2026-09-06 (session 2 `/end` + follow-up — B0 and B8 closed; device now on internal storage)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**Rebase `odin3-tuning` onto `upstream/main` (L-9, D-2)** — 14+ commits behind, and the device now runs `20260906.41d2e10`, newer than our fork point. Then **open B1 — Baseline instrumentation:** declare pause-points, write the on-device CSV logger, record one idle and one play session, run the pitch-vs-PWM sweep with the user listening. Confirm with the user that Steam's Storage page no longer lists the internal chip, then close L-12.

**Current block:** B1 — Baseline instrumentation

**Build status:** working (hooks verified in a fresh session; `tools/odin.py` used all session; `/end` build-guard glob fixed so `bash -n` no longer runs on `tools/*.py`; overlay v1 pushed and applied)

**Remote:** `origin/odin3-tuning` = HEAD after the follow-up commit. `main` = `origin/main` = `14230df`; `upstream/main` is 14+ commits ahead (L-9). Device image: `20260906.41d2e10`.

---

## Optional loose ends (NOT the next step)

Open: L-3 (user: AYN warranty check), L-4 (user: off-PC copy of the ABL backup — the device-side copy is gone), L-5 (download-plateau experiment, now on internal storage), L-6 (game froze on a Performance switch mid shader-compile; B3 repro), L-12 (udev hide rule applied — user confirms in Steam, then close). See `docs/SESSION_LEDGER.md`.

---

## What happened this session

- **B0 closed:** the SessionStart hook did its job in this fresh session (L-2).
- **Android-side detour (not Armada):** GameNative 1.2.0's ZENONIA 1 save was not exporting or reaching Steam Cloud. Root cause: the game's Sep-3 hotfix (v1.0.1) added Steam Cloud rules and a per-SteamID save folder; the launch-day build saved one folder up, so GameNative (which only looks where Steam's rules point) found nothing. Fix: updated the game in GameNative, it migrated the save, then "Keep local" on the launch-time conflict uploaded it. Verified by the user on the desktop. Reach-the-device notes are in Claude's memory, not this repo; the general lessons went to the KB.
- **Storage decision (D-9) — and executed:** internal install, Android kept at 16 GiB. The user ran the GUI installer right after the `/end`. Follow-up verified `root=sda20` / `boot=sda19` / ESP `sda18`, Android `userdata` `sda17` 16 GiB, image `20260906.41d2e10`; re-enabled SSH and reinstalled the key (fresh deployment drops both); reformatted the SD card as ext4 game storage with Armada's own `format-sdcard.sh` because the automount only mounts ext4 and the old Armada partitions never showed in Steam. `docs/DEVICE.md` Storage / Boot / recovery ladder rewritten; **B8 closed**.
- Protocol: `/end` build guard's `bash -n` glob narrowed to `tools/*.sh` (it was choking on `tools/odin.py`).

---

## Active blockers

None. Device/repo parity: **overlay v1** (`99-armada-hide-internal-ufs.rules`) pushed 2026-09-06 14:48, reloaded, identical to the repo. `device-state/` re-pulled 2026-09-06 14:48 — identical to the record (Balanced `gpu_max = 0.80` is on the device).

---

## Notes & things to watch

- **Upstream drift: 14 commits** at this `/end` (latest `c68b36a`, bottom-screen brightness persistence) — L-9, rebase at the first quiet point.
- **Fresh deployments lose `/etc` and `/var`:** SSH off, key gone. The Power-tab `gpu_max = 0.80` was nevertheless present at 14:24 (set again or restored by Armada Control) — worth understanding before B10, when the same question returns. Not an issue after ordinary OTAs (three-way `/etc` merge, D-4).
- **udev overlay files need a reload after `odin.py push`** (README in `device-overlay/` has the command); consider teaching `push` to do it when it sees `udev/rules.d`.
- **No SD-card rescue any more:** the card is game storage. A rescue means re-flashing a card from the PC (`flash-armada.ps1`) and switching the ABL boot source.
- `abl.conf auto_update_enabled=1`: the bootloader can update itself at shutdown after an OTA (D-7 awareness).
- **Idle load average ~4–5** on the Steam home screen (`steamwebhelper`). B5.
- `power_supply/battery/power_now` ≈ 67.8 W vs I×V ≈ 4.7 W — unreliable until checked (B4).
- Android was factory-reset by the install: GameNative, its games, the Download folder backups and the ADB pairing are gone. Claude's memory notes for that side are marked historical.
