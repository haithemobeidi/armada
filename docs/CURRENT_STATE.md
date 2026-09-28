# armada-odin3 — Current State

**Last updated:** 2026-09-28 14:05 (session 7 /end — upstream's s2idle fix measured, Wi-Fi hook dropped, kernel sleep-depth research recorded)

> This file carries only the **NEXT ACTION** + current state. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**B4, L-25: go below 0.17 W in sleep.** First confirm the new floor overnight (quit the game, unplug, one sleep, read `charge_counter`); then, with the device awake ~5 min, the read-only holder checks (`sync_state() pending` in dmesg, `interconnect_summary` ebi/llcc, `pm_genpd_summary`, per-subsystem `qcom_stats`); then a cdsp-stop 60-min sleep. The own-kernel test without #545's PCIe `opp-suspend-1` (does SM8750 really reset without a DDR sleep vote?) is D-7: fresh backup + the user's explicit go. The user parked this 2026-09-28 ("too lazy now, later") — no rush; if they want something else first, B1's idle recording and the game-audio sleep test (now largely answered by #545's ADSP patches) are next in B4/B1.

**Current phase:** B4 Battery + sleep — L-25 sleep-depth work (the statusline parses this line)

**Build status:** working — `tools/check-delta.sh` OK 2026-09-28 14:05 (33 delta files).

**Remote:** `odin3-tuning` rebased onto `upstream/main` = `410bcf2` on 2026-09-28 and pushed (`--force-with-lease`). `main` = `origin/main` (mirror, untouched). **Other machine: `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.**

---

## Device

- **Image `20260928.410bcf2`** (kernel 7.2.6, includes upstream #545 s2idle + ADSP sleep fixes), updated by the user via bootc; `/etc` carried over.
- **Overlay v3** = repo: only `99-armada-hide-internal-ufs.rules`; the Wi-Fi sleep hook deleted 2026-09-28 11:33. `/etc/systemd/system-sleep/` empty.
- Sleep: 43 mA ≈ 0.17 W (60 min, Eco, 80 %); Wi-Fi reconnects ~1 s after wake without the hook.
- Test scripts remain in `/var/tmp` (`sleep60.sh` tagged `-60min-newkernel-nohook`; edit the tag per run).

## Active blockers

None. Device/repo parity: overlay v3 on both.

## Open loops

L-25 (next), L-22 (parked), L-3, L-4, L-5, L-6, L-13, L-15, L-16 — see `docs/SESSION_LEDGER.md`.

## Owner rules and measurement notes

- Performance overlay off outside games; quit the game before sleeping; after a battery sleep > 15 min expect to press the power button twice (L-22).
- Drain figures need ≥ 60 min by `charge_counter` (`/var/tmp/sleep60.sh`); the device re-suspends on the alarm wake (L-22), so key-wake it afterwards. Launch detached: `odin.py sudo "bash -c 'setsid nohup bash /var/tmp/x.sh >/dev/null 2>&1 </dev/null &'"`; wrap SSH in `timeout` (it hangs when the device suspends under it).
- The device falls asleep a few minutes after the user stops touching it — ask them to keep it awake before any SSH read sequence.
- `odin.py push` never deletes a dropped overlay file — remove it on the device by hand.
- The % gauge lies above ~90 %; `odin.py put`/`get` from Git Bash need `MSYS_NO_PATHCONV=1`.
