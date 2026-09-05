# armada-odin3 — Current State

**Last updated:** 2026-09-05 (session 1 `/end` — protocol scaffold, device access, first snapshot)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**Confirm the SessionStart hook did its job in this fresh session** (state injected, origin currency + upstream drift reported, branch guard silent) — that closes ledger L-2 and B0. **Then open B1 — Baseline instrumentation:** declare pause-points, write the on-device CSV logger (temp / fan PWM / per-policy CPU freq / GPU freq / battery I·V / load / net RX / `mmcblk0` writes, every 3 s), pull it to `device-data/`, record one idle session and one real play session, and run the pitch-vs-PWM sweep with the user listening.

**Current block:** B0 — Protocol + device access

**Build status:** working (hooks fire; `tools/odin.py status|probe|pull` verified; rebased onto upstream and pushed; nothing pushed to the device yet)

**Remote:** `origin/odin3-tuning` = HEAD after this `/end`. `main` = `origin/main` = `upstream/main` = `14230df` (device runs `20260904.14230df`, built from it).

---

## Optional loose ends (NOT the next step)

Open: L-3 (user: AYN warranty check), L-4 (user: cloud copy of the ABL backup), L-5 (download-plateau experiment + card `dd` benchmark, folds into B1), L-6 (game froze on a Performance switch mid shader-compile; journal clean; B3 repro). See `docs/SESSION_LEDGER.md`.

---

## What happened this session

- Ported the Checkpoint / KB-template protocol for a fork with a device: `CLAUDE.md`, `PROTOCOL.md`, `DECISIONS.md` D-1…D-8, `ROADMAP.md` B0–B10, `docs/WORK_STYLE.md`, `/start` `/end`, five hooks (branch guard also trips on `main`; sync guard fetches origin AND upstream; index scoped to the fork delta), statusline with upstream drift, `.gitattributes` forcing LF.
- SSH to the Odin 3 (`192.168.1.188`, key installed); `tools/odin.py` (status / run / sudo / probe / pull / push dry-run).
- `docs/DEVICE.md` + `docs/ARMADA_CONTROL.md` from the live device. Corrections to the first assessment: **no fan tachometer**; prime cores top at **4089.6 MHz**; daemon averages the **3 hottest** zones; Armada Control's **Fans tab** already implements fan-stop, so `power-profiles.conf` is UI-owned and is *recorded* in `device-state/` (D-4 rewritten; three-layer explanation of how OTAs interact with `/etc` and this repo added).
- User did an OTA mid-session (device → `20260904.14230df`); rebased our stack onto it, fast-forwarded `main`, pushed both. User then delegated repo mechanics; D-2 amended: rebases are Claude's call at quiet points, always reported.
- First user observations recorded (ROADMAP B2/B8): `gpu_max` 0.80 reduced the whine; Eco during a Steam download reduced it further but slowed the download; live diagnosis showed the download is **SD-card write-bound** (~60 MB/s steady writes on a UHS-I SDR104 slot, Wi-Fi healthy, no thermal throttling), not a bug.

---

## Active blockers

None. Device/repo parity: nothing in `device-overlay/` yet (v0); `device-state/` re-pulled at this `/end`.

---

## Notes & things to watch

- **Upstream drift:** 0 at this `/end`. Upstream merges several PRs a day; expect a nonzero count next session — rebase at the first quiet point (D-2).
- **Idle load average ~4–5** on the Steam home screen (`steamwebhelper`). B5. Don't blame idle fan noise on the curve alone until understood.
- `power_supply/battery/power_now` ≈ 67.8 W vs I×V ≈ 4.7 W — unreliable until checked (B4).
- `abl.conf auto_update_enabled=1`: the bootloader can update itself at shutdown after an OTA (D-7 awareness).
- `/var` mounts with `compress=zstd:1` on the SD card — backlog measurement for install speed (B8).
- The SD card is the recovery path (pull it → Android boots). Stay on SD through tuning.
