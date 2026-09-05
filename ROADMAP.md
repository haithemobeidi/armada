# armada-odin3 — Roadmap

Whole-OS tuning of ArmadaOS for one AYN Odin 3, one owner. Blocks are organised by subsystem. Every block opens with a **baseline measurement** and closes with a **recorded before/after**. Nothing is baked into the image until it has been stable as an `/etc` change (D-4).

**Block numbers are frozen.** Identity is the name. A cut block stays as a labeled gap.

---

## 📊 Status at a glance

| # | Block | Status | Gate to close |
|---|---|---|---|
| B0 | Protocol + device access | ⬅ CURRENT — scaffold written, SSH key installed, first snapshot taken | Hooks verified live in a fresh session; `tools/` pull works; first `/end` clean |
| B1 | Baseline instrumentation | queued | A logger that records temp / PWM / CPU+GPU freq / battery power every few seconds to a CSV, pulled to the PC; one real 30-min play session and one idle session recorded |
| B2 | Fan + thermal | queued | Fan silent at idle and light load; whine band identified by ear vs PWM; ramp/curve tuned; user signs off after a week of use |
| B3 | Power profiles + per-game performance | queued | A quiet-but-fast profile between Balanced and Performance; FPS cap / resolution / FEX preset defaults set for the owner's library; before/after temps and battery draw recorded |
| B4 | Battery + sleep | queued | Idle drain and s2idle drain measured; wake reliability confirmed; drain reduced or explained |
| B5 | Idle CPU load | queued | The ~4–5 load average seen on the Steam home screen understood and reduced or justified |
| B6 | Services + boot | queued | Every running service justified for this owner; unneeded ones masked via `/etc`; boot time measured |
| B7 | Display + input + RGB | queued | HDR/brightness/orientation verified; controller emulation chosen; RGB policy set (off by default saves power); calibration done |
| B8 | Storage decision | queued | Decide SD vs internal install with data (load times, power); if internal: own backup step, own go (D-7) |
| B9 | Upstream contributions | queued | Anything general (e.g. per-device fan curve defaults) opened as a PR from a `pr/*` branch |
| B10 | Image build | queued | Fork CI enabled, registry refs repointed, stable overlay baked, image built and flashed — only after B2–B7 are stable |

---

## B0 — Protocol + device access

Copy the session protocol from the Checkpoint / KB template, adapt it for a fork with a device (`PROTOCOL.md`), get passwordless SSH to the handheld, take a first read-only snapshot, and record everything learned in `docs/DEVICE.md` and `docs/ARMADA_CONTROL.md`.

**Done so far (2026-09-05):** protocol files, hooks, commands; SSH key installed (`armada@192.168.1.188`); snapshot taken — SoC topology, thermal zones, hwmon, devfreq, battery, running services, storage layout, bootc image. Key findings: the fan has **no tachometer** (RPM unreadable, only PWM); Armada Control ships a **Fans tab** with a curve editor that already supports fan-stop; the UI owns `power-profiles.conf` (D-4 corrected accordingly); prime cores top out at 4089.6 MHz in the kernel table, not the spec-sheet 4320.

**Remaining:** `tools/odin.py` (ssh wrapper, `pull` UI-owned configs into `device-state/`, `probe` snapshot), verify hooks fire in a fresh session, first `/end`.

## B1 — Baseline instrumentation

A read-only logger on the device (systemd user unit or a script launched over SSH) writing one CSV row every 3 s: timestamp, the daemon's own `Temperature`/`FanPwm` from D-Bus, top-3 thermal zones, per-policy `scaling_cur_freq`, GPU `cur_freq`, battery `current_now`/`voltage_now`/`status`, load average. Pull to `device-data/` (git-ignored); summarise in this section. Two recordings first: 30 min idle on the Steam home screen; 30 min of a real game the owner plays. The **pitch-vs-PWM test** belongs here too: with the daemon paused and a temperature watchdog in the script, step PWM 0→255 in quanta of 8 while the owner notes pitch and loudness per step. This decides how much B2 can do.

## B2 — Fan + thermal

Facts from the code: `armada-powerd` ticks every 3 s, reads the average of the three hottest cpu/gpu/gpuss/video/mem zones, EMA-smooths (0.5), interpolates PWM on the profile's curve, slew-limits (`ramp_up=36`, `ramp_down=6` per tick → ~18 s up, ~102 s down), clamps to `[min_pwm=51, 255]`, quantises to 8. The `moderate` curve pins 0–55 °C at 51, so the fan never stops below 55 °C. Idle CPU zones sit ~58–60 °C while plugged in on the home screen, so fan-stop needs a curve whose zero point is above the real idle temperature, not the spec's.

The first assessment's phased fan plan (Opus, 2026-09-04) is at <https://claude.ai/code/artifact/48150c05-19f5-4ca3-b267-cd4a0d91476f>; its phases 0–3 map onto B1–B3 here with the corrections noted in B0.

**User reports (instruments too):** 2026-09-05 — Balanced `gpu_max` 1.0→0.80 "reduced the high-pitched sound a bit" while gaming. Same day, during a Steam download (CPU-bound decompression) the whine was "pretty loud" on Balanced; switching to **Eco** "did help" but download speed dropped noticeably. So the tone tracks load-driven PWM and is software-movable; Eco's `large` cap (51%/48%) is too blunt for downloads — a download-oriented middle setting is a B3 candidate.

Plan: via the **Fans tab** (UI-owned, D-4) create an `odin3` curve with a 0-PWM floor up to the measured idle temperature, a steep segment through the whine band found in B1, and gentler slopes above; raise `ramp_down`; keep `[suspend]` safety values. Verify the fan restarts from a full stop (some fans need a kick). One variable per pause. Hardware track in parallel: warranty/RMA check with AYN for the ~9 kHz early-unit tone before any physical work.

## B3 — Power profiles + per-game performance

Levers that exist: `cpu_underclock` tiers (frequency caps → lower DVFS voltage; the only "undervolt" Qualcomm exposes), `cpu_max`, `gpu_min/gpu_max`, governor; per-game FEX preset, resolution, CPU core set / Wine topology, nice, RT scheduling, scheduler (`eevdf`/`cosmos`/`lavd`), gamescope nice. Goal: a Balanced that is quiet but does not leave performance on the table, plus per-game defaults for the owner's actual library. Frame-rate caps and resolution (GPU idles between frames) are preferred over blanket `gpu_max` caps. Measure: temps, PWM, battery W, and the owner's perceived smoothness.

## B4 — Battery + sleep

Measure idle drain on battery (screen on/off), s2idle drain overnight, wake reliability. Upstream defaulted every device to native s2idle on 2026-09-03; verify it's right for this unit. Check RGB, Wi-Fi power save, Bluetooth, USB gadget, tailscale, and any polling daemon as drain sources.

## B5 — Idle CPU load

The first snapshot showed load average ~4–5 and CPU pressure "some" ~12% with only Steam idle in gamescope. Find what's spinning (kworkers `ring0`/`ring2`, steamwebhelper, mangoapp?), decide what's normal for this stack vs what can be trimmed.

## B6 — Services + boot

Enumerate every enabled unit against this owner's use (no Waydroid? no MTP? no tailscale? avahi?). Mask via `/etc/systemd/system/*.service` drop-ins in `device-overlay/`. Measure boot time before/after (`systemd-analyze`).

## B7 — Display + input + RGB

HDR nits (650), orientation, brightness curve, refresh; controller emulation type; stick/trigger calibration; RGB (24 channels) — default off for battery unless the owner wants it.

## B8 — Storage decision

Currently: Armada on the SD card (`mmcblk0`, 953 GB, btrfs `/var`), stock Android intact on UFS (`sda`, 464 GB). The installer shrinks Android `userdata` (Android is factory-reset: user data wiped, system kept, dual-boot) and ABL keeps an UNINSTALL CFW fallback; `armada-installer reset` gives the space back. Reasons to stay on SD during tuning: pull-the-card recovery, Android untouched for comparisons and warranty, and nothing in B1–B7 depends on storage speed. Revisit with load-time and power measurements once tuning is stable. Requires D-7 steps.

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
