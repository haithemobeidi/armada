# armada-odin3 — Roadmap

Whole-OS tuning of ArmadaOS for one AYN Odin 3, one owner. Blocks are organised by subsystem. Every block opens with a **baseline measurement** and closes with a **recorded before/after**. Nothing is baked into the image until it has been stable as an `/etc` change (D-4).

**Owner's target (stated 2026-09-07):** maximum battery life at idle and while gaming, while still holding **60 fps in old or light games and 30 fps in modern titles** (reference: FF7 Crisis Core), via two or three QAM profiles retuned for exactly that. Fan noise (D-8) and battery pull the same levers — lower clocks mean less heat and less fan — so the block order stands; the difference is that every block measures **watts**, not just PWM.

**Block numbers are frozen.** Identity is the name. A cut block stays as a labeled gap.

---

## 📊 Status at a glance

| # | Block | Status | Gate to close |
|---|---|---|---|
| B0 | Protocol + device access | **done 2026-09-06** — scaffold, hooks, `tools/odin.py`; SessionStart hook verified in a fresh session (L-2) | — |
| B1 | Baseline instrumentation | ⬅ CURRENT — not started; rebase first (L-9) | A logger that records temp / PWM / CPU+GPU freq / battery power every few seconds to a CSV, pulled to the PC; one real 30-min play session and one idle session recorded |
| B2 | Fan + thermal | queued | Fan silent at idle and light load; whine band identified by ear vs PWM; ramp/curve tuned; user signs off after a week of use |
| B3 | Power profiles + per-game performance | queued | Eco / Balanced / Performance retuned as **a 30-fps "modern" profile and a 60-fps "light" profile** (the three names are hardcoded in `armada-powerd`; a fourth cannot be added), each measured in watts and °C on the owner's library; per-game resolution / FEX defaults set; the gamescope frame-limiter undershoot (upstream #45 / #276 / #322, reproduced on an Odin 3 Max) worked around or fixed before the 30-fps target counts |
| B4 | Battery + sleep | queued | Idle drain and s2idle drain measured in %/h; deep-sleep entry (`qcom_stats` aosd/cxsd) and Bluetooth power state across s2idle checked on this unit (upstream #264 / #274 / #265); wake reliability confirmed; drain reduced or explained |
| B5 | Idle CPU load | queued | The ~4–5 load average seen on the Steam home screen understood and reduced or justified |
| B6 | Services + boot | queued | Every running service justified for this owner; unneeded ones masked via `/etc`; boot time measured |
| B7 | Display + input + RGB | queued | HDR/brightness/orientation verified; controller emulation chosen; RGB policy set (off by default saves power); calibration done |
| B8 | Storage decision | **done 2026-09-06** — internal install (D-9), Android 16 GiB, boot verified over SSH, SD card reformatted as ext4 game storage, `docs/DEVICE.md` rewritten | Before/after download measurement folds into B1 (L-5 on internal) |
| B9 | Upstream contributions | queued | Anything general (e.g. per-device fan curve defaults) opened as a PR from a `pr/*` branch |
| B10 | Image build | queued | Fork CI enabled, registry refs repointed, stable overlay baked, image built and flashed — only after B2–B7 are stable |

---

## B0 — Protocol + device access

Copy the session protocol from the Checkpoint / KB template, adapt it for a fork with a device (`PROTOCOL.md`), get passwordless SSH to the handheld, take a first read-only snapshot, and record everything learned in `docs/DEVICE.md` and `docs/ARMADA_CONTROL.md`.

**Done so far (2026-09-05):** protocol files, hooks, commands; SSH key installed (`armada@192.168.1.188`); snapshot taken — SoC topology, thermal zones, hwmon, devfreq, battery, running services, storage layout, bootc image. Key findings: the fan has **no tachometer** (RPM unreadable, only PWM); Armada Control ships a **Fans tab** with a curve editor that already supports fan-stop; the UI owns `power-profiles.conf` (D-4 corrected accordingly); prime cores top out at 4089.6 MHz in the kernel table, not the spec-sheet 4320.

**Remaining:** `tools/odin.py` (ssh wrapper, `pull` UI-owned configs into `device-state/`, `probe` snapshot), verify hooks fire in a fresh session, first `/end`.

## B1 — Baseline instrumentation

A read-only logger on the device (systemd user unit or a script launched over SSH) writing one CSV row every 3 s: timestamp, the daemon's own `Temperature`/`FanPwm` from D-Bus, top-3 thermal zones, per-policy `scaling_cur_freq`, GPU `cur_freq`, battery `current_now`/`voltage_now`/`status`, load average. Pull to `device-data/` (git-ignored); summarise in this section. Two recordings first: 30 min idle on the Steam home screen; 30 min of a real game the owner plays. The **pitch-vs-PWM test** belongs here too: with the daemon paused and a temperature watchdog in the script, step PWM 0→255 in quanta of 8 while the owner notes pitch and loudness per step. This decides how much B2 can do.

**Run 1 — 2026-09-07 02:13–02:43 device time, play, Eco, unplugged, FINAL FANTASY RESONANCE DEMO (in-game frame cap, value to confirm), device already warm from earlier play:** 591 rows / 29.9 min. Battery 98 → 92 % (12.0 %/h by the gauge) but `current_now × voltage_now` averaged **6.6 W** (median 7.1, p10 4.0, p90 8.3) — the two disagree by ~1.6×; the gauge's own `time_to_empty_avg` sides with the current sensor (≈ 4.3 h at 92 %). Logger v2 records `charge_counter` to settle it. Daemon temperature mean 61.7 °C, max 69 (a `gpuss` zone was the hottest 89 % of the time); **fan PWM 51 (the floor) 78 % of the time, 56 the rest — the fan never left the floor on Eco.** GPU at 832 MHz 78 % of the time (Eco's `gpu_max 0.80` is a no-op, L-16); policy6 pinned at its 1958 MHz Eco cap 99 % of the time, policy0 at its 1785 cap 74 % — **this game is CPU-capped on Eco.** Load1 mean 5.3. Raw CSV: `device-data/play-ffresonance-eco-20260907-021340.csv` (git-ignored).

**Run 2 — 2026-09-07 03:07:49 device time, same game / same in-game cap / unplugged, Balanced (in progress):** started by a watcher 15 s after the daemon reported Balanced (03:07:34). **User report at ~03:08, phone dB meter held near the device (rough):** Eco read ~30–35 dB, Balanced ~40 dB — "another 10 dB-ish". At that moment: daemon temperature 61–63 °C, **PWM 64 on Balanced vs 51 (the floor) on Eco at the same temperature** — the difference is the curve (`moderate` vs `relaxed`), not the heat. Battery 85 %, ~6.4–7.2 W, prime cores now alternating 1017 ↔ 2246 MHz (no longer pinned at the cap as on Eco).
**User report at 03:18: "it's pretty loud rn"** — at that moment PWM **64**, daemon temperature 61 °C, GPU 832 MHz, ~7–8 W, and 64 was the run's maximum so far (histogram after 10.5 min: 51×24, 56×75, 58×8, 64×105). So on this unit **PWM 64 — 25 % duty, the second-lowest level the moderate curve ever uses — already reads as "pretty loud" to the owner**, and the character is a high-pitched tone, not whoosh (user, 03:12). Anchor for the B2 target: the play-time band is 51–64; the sweep must say whether the tone is worse, same or gone above it.

## B2 — Fan + thermal

Facts from the code: `armada-powerd` ticks every 3 s, reads the average of the three hottest cpu/gpu/gpuss/video/mem zones, EMA-smooths (0.5), interpolates PWM on the profile's curve, slew-limits (`ramp_up=36`, `ramp_down=6` per tick → ~18 s up, ~102 s down), clamps to `[min_pwm=51, 255]`, quantises to 8. The `moderate` curve pins 0–55 °C at 51, so the fan never stops below 55 °C. Idle CPU zones sit ~58–60 °C while plugged in on the home screen, so fan-stop needs a curve whose zero point is above the real idle temperature, not the spec's.

The first assessment's phased fan plan (Opus, 2026-09-04) is at <https://claude.ai/code/artifact/48150c05-19f5-4ca3-b267-cd4a0d91476f>; its phases 0–3 map onto B1–B3 here with the corrections noted in B0.

**User reports (instruments too):** 2026-09-05 — Balanced `gpu_max` 1.0→0.80 "reduced the high-pitched sound a bit" while gaming. Same day, during a Steam download (CPU-bound decompression) the whine was "pretty loud" on Balanced; switching to **Eco** "did help" but download speed dropped noticeably. So the tone tracks load-driven PWM and is software-movable; Eco's `large` cap (51%/48%) is too blunt for downloads — a download-oriented middle setting is a B3 candidate. Later the same night: **Performance** during a shader compile took the fan to max and it stayed loud ~2 min after switching back — both by design (`performance` governor, `gpu_min=1.0`, aggressive curve; `ramp_down=6` per 3 s tick ≈ 102 s from 255 to 51). The user experienced the slow unwind as "the fan kept going" — that is the B2 `ramp_down` target, measured from a real event. The game froze at the same time (ledger L-6; journal clean).

Plan: via the **Fans tab** (UI-owned, D-4) create an `odin3` curve with a 0-PWM floor up to the measured idle temperature, a steep segment through the whine band found in B1, and gentler slopes above; raise `ramp_down`; keep `[suspend]` safety values. Verify the fan restarts from a full stop (some fans need a kick). One variable per pause. Hardware track in parallel: warranty/RMA check with AYN for the ~9 kHz early-unit tone before any physical work.

## B3 — Power profiles + per-game performance

Levers that exist: `cpu_underclock` tiers (frequency caps → lower DVFS voltage; the only "undervolt" Qualcomm exposes), `cpu_max`, `gpu_min/gpu_max`, governor; per-game FEX preset, resolution, CPU core set / Wine topology, nice, RT scheduling, scheduler (`eevdf`/`cosmos`/`lavd`), gamescope nice. Goal: a Balanced that is quiet but does not leave performance on the table, plus per-game defaults for the owner's actual library. Also question Performance's `gpu_min=1.0`: it pins the GPU at 832 MHz even during CPU-only work like shader compilation, which is heat and fan for nothing (observed 2026-09-05, L-6). Frame-rate caps and resolution (GPU idles between frames) are preferred over blanket `gpu_max` caps. Measure: temps, PWM, battery W, and the owner's perceived smoothness. **Finding 2026-09-07 (L-16):** `gpu_max` / `gpu_min` ratios are taken against the 1100 MHz top of the devfreq table, not the 832 MHz cap, so any `gpu_max ≥ 0.76` is uncapped on this SoC; a real 660 MHz ceiling is 0.60 (`docs/ARMADA_CONTROL.md`). Eco's factory 0.80 and the user's Balanced 0.80 were both no-ops.

**Owner's target (2026-09-07, L-14):** battery first. Two of the three profiles become the deliverable: a **30-fps profile** for modern titles (reference: FF7 Crisis Core) and a **60-fps profile** for old or light games; the third is whatever the measurements say is worth keeping. **Known blocker:** gamescope's frame limiter undershoots (a 30 cap lands at 27–28) and *lowering* the cap lowers performance further — upstream #45 / #276 / #322, reproduced on an Odin 3 Max, no fix landed as of 2026-09-07. Workarounds to measure, one at a time: the game's own limiter; a `DXVK_FRAME_RATE` env via the Compatibility tab; a `gpu_min` floor so the governor does not collapse when the cap lowers load.

## B4 — Battery + sleep

Measure idle drain on battery (screen on/off), s2idle drain overnight, wake reliability. Upstream defaulted every device to native s2idle on 2026-09-03; verify it's right for this unit. Check RGB, Wi-Fi power save, Bluetooth, USB gadget, tailscale, and any polling daemon as drain sources.

**Plan (2026-09-07, L-13), measure first:** (1) `armada-sleep-debug prepare` → `rtcwake -m freeze -s 30` → `collect`: do the `qcom_stats` aosd/cxsd counters tick on this SM8750 (they never do on the SM8550, upstream #274: USB PHY vote + SD IRQ storm), and is Bluetooth still `Powered: yes` across s2idle (upstream #264: an Odin 2 lost 25 % in 90 min; `rfkill block bluetooth` gave ~1 %/h)? (2) One overnight with Bluetooth on, one with it blocked; the user reads the battery % before/after and touches the left side of the screen (#265, warm on an Odin 3 Max). (3) If Bluetooth is the drain: a drop-in `/etc/systemd/system-sleep/` hook that rfkill-blocks it on `pre` and unblocks on `post` — overlay file, no upstream edit, B9 PR candidate (upstream's rfkill logic exists only in the fake-suspend script and has been commented out there since `b92c959`, over Wi-Fi resume time, not Bluetooth). (4) If the counters stay at zero: check the `*.usb` / PHY `runtime_status`; a stuck PHY is a kernel patch → upstream report, not `/etc`.

## B5 — Idle CPU load

The first snapshot showed load average ~4–5 and CPU pressure "some" ~12% with only Steam idle in gamescope. Find what's spinning (kworkers `ring0`/`ring2`, steamwebhelper, mangoapp?), decide what's normal for this stack vs what can be trimmed.

## B6 — Services + boot

Enumerate every enabled unit against this owner's use (no Waydroid? no MTP? no tailscale? avahi?). Mask via `/etc/systemd/system/*.service` drop-ins in `device-overlay/`. Measure boot time before/after (`systemd-analyze`).

## B7 — Display + input + RGB

HDR nits (650), orientation, brightness curve, refresh; controller emulation type; stick/trigger calibration; RGB (24 channels) — default off for battery unless the owner wants it.

## B8 — Storage decision

Currently: Armada on the SD card (`mmcblk0`, 953 GB, btrfs `/var`), stock Android intact on UFS (`sda`, 464 GB). The installer shrinks Android `userdata` (Android is factory-reset: user data wiped, system kept, dual-boot) and ABL keeps an UNINSTALL CFW fallback; `armada-installer reset` gives the space back. Reasons to stay on SD during tuning: pull-the-card recovery, Android untouched for comparisons and warranty, and nothing in B1–B7 depends on storage speed. Revisit with load-time and power measurements once tuning is stable. Requires D-7 steps.

**Evidence so far (2026-09-05, live during a Steam download on Eco):** Wi-Fi healthy (−57 dBm, 1.7 Gbit link, `ath12k_thermal cur_state=0`, no cpufreq throttling), yet net RX ≈ 10.8 MB/s while `mmcblk0` wrote ≈ 60 MB/s and IO pressure "some" sat at 18–20%. Steam's displayed speed "trickled toward 0" because its disk-write queue backed up — the **SD card write path is the download bottleneck**, worsened by Eco's CPU cap on decompression. Downloads/installs are the one workload the SD card visibly hurts; gaming reads are far less affected. This is the strongest argument for an internal install so far; it does not change the "stay on SD during tuning" call.

**Card vs slot (read from sysfs/debugfs 2026-09-05):** the card is a SanDisk Extreme 1 TB (`SR01T`, 05/2026, U3 / V30 → guaranteed ≥30 MB/s sustained write). The slot negotiates **UHS-I SDR104 at 202 MHz, 4-bit, 1.8 V** — the fastest a UHS-I slot can do, ceiling ≈104 MB/s theoretical, ≈90 MB/s real. The card's advertised 245 MB/s needs SanDisk's proprietary QuickFlow reader and is unreachable here. Disk writes sat at a steady ~60 MB/s across two samples while net RX varied 10.8→17.5 MB/s — a ceiling signature. `/var` is btrfs with `compress=zstd:1` (CPU compression on every write, mostly wasted on already-compressed game data) + CoW; Steam preallocates then writes, so bytes written ≈ 4–5× bytes downloaded. Raw `dd` sequential write/read of the card to be measured in B1 once no download is running.

**Decision (2026-09-06, D-9): internal, Android 16 GiB.** The user's call, not a measurement: they will not use Android, and the SD write ceiling above is the only storage signal that matters to them. Procedure, read from `system_files/usr/libexec/armada/armada-installer`: a fresh install deletes and recreates `userdata` at the chosen size, zeroes its first 8 MiB (Android factory-resets on next boot, system kept), then creates ESP 512 MiB + boot 1 GiB + btrfs root in the freed space (Armada needs at least ~33.6 GiB); it refuses if any partition lies after `userdata` (this unit: `sda17` is last). Floor 8 GiB, GUI default 32 GiB, slider step 4. Reverts: `armada-installer reset` from the SD card, or ABL "UNINSTALL CFW & EXPAND USERDATA". **Executed 2026-09-06 by the user** (GUI installer, slider at 16) right after that `/end`. Verified over SSH: `root=sda20` (418.4 GB btrfs), `boot=sda19`, ESP `sda18`, Android `userdata` `sda17` = 16 GiB, image `20260906.41d2e10`. The fresh deployment came up without SSH (`--no-merge` drops the old `/etc`, `/var` is new) — re-enabled in the UI, key reinstalled with the default password. The SD card, still holding the old Armada install, did not appear in Steam because the automount only mounts ext4; reformatted with `/usr/lib/hwsupport/format-sdcard.sh` → one ext4 `casefold` partition at `/run/media/mmcblk0p1`. Block closed; the download before/after is L-5 on internal.

## B9 — Upstream contributions

Anything general goes back: per-device fan curve defaults in `ayn-odin-3.conf`, a corrected SM8750 frequency table, any bug found. Branch from `main`, cherry-pick, PR. Protocol docs never ride along.

## B10 — Image build

Enable Actions on the fork, repoint `ghcr.io/armada-os/armada` refs, confirm whether `SIGNING_SECRET` gates building or only publishing, bake the stable overlay into `system_files/`, build with `build-disk.yml` on the free ARM64 runner, flash. Reflash = risk; last.

---

## Backlog (ideas, not commitments)

- Correct the SM8750 cluster table upstream (kernel tops the prime cores at 4089.6 MHz; the repo's tiers assume 4320).
- `armada-powerd`: make `[fan_curve.*]` and `[underclock.*]` defaults device-scoped (`ayn-odin-3.conf`) instead of global — the Phase 4 idea from the first assessment.
- Investigate why `power_supply/battery/power_now` reports ~67.8 W while current×voltage gives ~4.7 W (unit or scaling bug; matters for B4 logging).
- Hostname is `fedora`; a device-specific hostname would make mDNS (`odin3.local`) usable instead of hunting IPs.
- Steam's Storage page lists the internal UFS chip as an empty 464.5 GB drive (Android's filesystem-less partitions confuse it; udisks already says `HintSystem`). A `UDISKS_IGNORE=1` udev rule for `sda` would hide it — first overlay candidate and an upstream PR for every Odin 3 internal install (L-12).
- `/var` on the SD card mounts with `compress=zstd:1`. Measure whether disabling compression for the Steam library (a `chattr +m` / nodatacow-style per-directory setting, or a mount option) speeds up installs on the SD card — game data is already compressed, so the CPU spent compressing it may be pure overhead. B8 measurement candidate.
