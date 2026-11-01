# armada-odin3 — Current State

**Last updated:** 2026-11-01 13:55 (session 9 /end — Lost Odyssey Recomp built natively on the Odin, imported, in Steam, boots; first-play report pending)

> This file carries only the **NEXT ACTION** + current state. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**L-26 Pause C: the user plays Lost Odyssey Recomp from Gaming Mode** (Library → Non-Steam) and reports FPS at the 30 cap, fan, warmth; Claude reads `fan_pwm`/`temperature` from `odin.py` at the same moments and records it in `docs/LOST_ODYSSEY.md`. Then **B4 L-25** resumes (go below 0.17 W in sleep) — **first re-baseline a 60-min sleep on the new image `20261031.8a72944`**, since the 0.17 W figure is from `20260928.410bcf2`. Upstream reports for the game are L-29 (not urgent).

**Current phase:** B4 Battery + sleep (L-25), with side project L-26 at its first-play check (the statusline parses this line)

**Build status:** working — `tools/check-delta.sh` OK 2026-11-01 13:50 (34 delta files). Game: LostOdysseyRecomp v1.1.0 aarch64 build + native DXC, `ldd` clean, boots on Vulkan (Adreno 830) 2026-11-01.

**Remote:** `odin3-tuning` rebased onto `upstream/main` = `410bcf2` on 2026-09-28; `upstream/main` is **328 commits ahead** (2026-11-01). Rebase at a quiet point. `main` = `origin/main` (mirror, untouched). **Other machine: `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.**

---

## Device

- **IP `192.168.1.189`** (DHCP moved it from `.188`; `odin.py` default updated). Find it again with a LAN scan for port 22 / Atheros OUI `00-03-7f` (`docs/DEVICE.md` → Access).
- **Image `20261031.8a72944`** (`armada:testing`, kernel 7.2.6), updated by the user via Steam; read 2026-11-01. Steam client on Beta (`publicbeta`, 2026-10-29 build) via "Preview"; known cosmetic QAM dropdown shift (upstream #802), user keeps it.
- **Overlay v3** = repo: only `99-armada-hide-internal-ufs.rules` (still present 2026-11-01). `/etc/systemd/system-sleep/` empty.
- Sleep: 43 mA ≈ 0.17 W (60 min, Eco, 80 %) on the **previous** image `20260928.410bcf2`.
- **Lost Odyssey Recomp** installed in `~/Games/LostOdysseyRecomp/` (game data, saves, settings beside the program); build tree `~/src/LostOdysseyRecomp`, DXC `~/src/DirectXShaderCompiler` + `~/src/dxc-build`, container `lo-build`, ISOs on the SD card. Revert: `docs/LOST_ODYSSEY.md`. Nothing in `/etc`, no services.
- Test scripts remain in `/var/tmp` (`sleep60.sh` tagged `-60min-newkernel-nohook`; edit the tag per run).

## Active blockers

None. Device/repo parity: overlay v3 on both (checked 2026-11-01).

## Open loops

L-26 (Pause C next), L-25, L-30 (bootloader is now OpenABL 1.2 — recovery ladder unverified), L-29 (upstream reports, game), L-22 (parked), L-28 (template resync, user's call), L-3, L-4, L-5, L-6, L-13, L-15, L-16 — see `docs/SESSION_LEDGER.md`.

## Owner rules and measurement notes

- Performance overlay off outside games; quit the game before sleeping; after a battery sleep > 15 min expect to press the power button twice (L-22).
- Drain figures need ≥ 60 min by `charge_counter` (`/var/tmp/sleep60.sh`); the device re-suspends on the alarm wake (L-22), so key-wake it afterwards. Launch detached: `odin.py sudo "bash -c 'setsid nohup bash /var/tmp/x.sh >/dev/null 2>&1 </dev/null &'"`; wrap SSH in `timeout` (it hangs when the device suspends under it).
- **No background polling loops from the PC.** Windows Terminal crashed twice (2026-11-01) while PC-side SSH watcher loops ran; cause unproven. Detach long jobs on the device with a log and check on demand — the fan dropping is the user's "done" signal.
- The device falls asleep a few minutes after the user stops touching it — ask them to keep it awake before any SSH read sequence (or hold a temporary `systemd-inhibit` as root for long jobs; release it after).
- `odin.py push` never deletes a dropped overlay file — remove it on the device by hand.
- The % gauge lies above ~90 %; `odin.py put`/`get` from Git Bash need `MSYS_NO_PATHCONV=1`.
- The SD card is ext4 (Armada game storage), mounted at `/run/media/armada/SD`. If the Android side offers to format it, decline — the Steam library lives there.
