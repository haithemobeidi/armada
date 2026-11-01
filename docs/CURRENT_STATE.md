# armada-odin3 — Current State

**Last updated:** 2026-11-01 03:40 (session 8 /end — Lost Odyssey Recomp researched, native ARM64 on-device build planned; no device or code changes)

> This file carries only the **NEXT ACTION** + current state. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**L-26 (side project, the user's plan for 2026-11-02): build LostOdysseyRecomp natively for ARM64 on the Odin** in a Fedora 44 distrobox, no FEX. Follow `docs/LOST_ODYSSEY.md` step by step: pause A after codegen, pause B before the first launch (announce it first), pause C after a first play. Start by checking for a release newer than v1.1.0, then begin the 29.2 GB ISO copy (`C:\Users\haith\OneDrive\Desktop\LO\`) to the SD card, letting it run in parallel with the container setup. The device must be plugged in and awake. After that, **B4 L-25** resumes (go below 0.17 W in sleep; plan in ROADMAP B4; the own-kernel test is D-7: fresh backup + the user's explicit go).

**Current phase:** Side project L-26 (Lost Odyssey native build), then B4 L-25 sleep-depth work (the statusline parses this line)

**Build status:** working — `tools/check-delta.sh` OK 2026-11-01 03:36 (34 delta files).

**Remote:** `odin3-tuning` rebased onto `upstream/main` = `410bcf2` on 2026-09-28. `upstream/main` is now **324 commits ahead** (2026-11-01, latest #818 odin2-gyro). Rebase at a quiet point, not inside the L-26 build. `main` = `origin/main` (mirror, untouched). **Other machine: `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.**

---

## Device

- **Image `20260928.410bcf2`** as last verified 2026-09-28 (kernel 7.2.6, includes upstream #545 s2idle + ADSP sleep fixes). Not checked since; the user may have updated via bootc.
- **Overlay v3** = repo: only `99-armada-hide-internal-ufs.rules`. `/etc/systemd/system-sleep/` empty.
- Sleep: 43 mA ≈ 0.17 W (60 min, Eco, 80 %); Wi-Fi reconnects ~1 s after wake without the hook.
- Test scripts remain in `/var/tmp` (`sleep60.sh` tagged `-60min-newkernel-nohook`; edit the tag per run).

## Active blockers

None. Device/repo parity: overlay v3 on both (as of 2026-09-28).

## Open loops

L-26 (next), L-25, L-22 (parked), L-28 (template resync, user's call), L-27 (kbdoc), L-3, L-4, L-5, L-6, L-13, L-15, L-16 — see `docs/SESSION_LEDGER.md`.

## Owner rules and measurement notes

- Performance overlay off outside games; quit the game before sleeping; after a battery sleep > 15 min expect to press the power button twice (L-22).
- Drain figures need ≥ 60 min by `charge_counter` (`/var/tmp/sleep60.sh`); the device re-suspends on the alarm wake (L-22), so key-wake it afterwards. Launch detached: `odin.py sudo "bash -c 'setsid nohup bash /var/tmp/x.sh >/dev/null 2>&1 </dev/null &'"`; wrap SSH in `timeout` (it hangs when the device suspends under it).
- The device falls asleep a few minutes after the user stops touching it — ask them to keep it awake before any SSH read sequence.
- `odin.py push` never deletes a dropped overlay file — remove it on the device by hand.
- The % gauge lies above ~90 %; `odin.py put`/`get` from Git Bash need `MSYS_NO_PATHCONV=1`.
- The SD card is ext4 (Armada game storage). If the Android side offers to format it, decline — the Steam library lives there.
