# Session Ledger — open items that must not get lost

> **What this is:** the append-and-strike ledger for session-scoped open items —
> queued tests, pre-release gates, riders, deferred decisions, watch items.
> Anything phrased like "next session," "before release," "rider," "queued,"
> or "check later" gets a line HERE at the moment it's said.
>
> **Rules** (full rationale in the global `PROTOCOL.md` → "The ledger at the moment of the event"):
>
> - **Append at the moment of queueing; strike at the moment of resolution.**
>   Never wait for /end — end-of-session recall is what loses items (long
>   sessions get context-compacted; minute-5 facts don't survive to an
>   hour-4 wrap).
> - **Worthiness — all four must hold for a line to earn an ID:** (1) an open
>   loop a future session must act on, with a concrete done-condition;
>   (2) not tracked elsewhere (bugs → the bug doc, features → the backlog,
>   status → the spine); (3) can't just be done now (under ~10 minutes ⇒ do
>   it); (4) one ID per loop — sub-facts ride the parent item.
> - **Size — HARD cap per item** (`.claude/protocol.json` → `ledger.item_max_chars`,
>   default 600): the ID line plus its continuation lines. Longer analysis
>   goes to a bug entry, a backlog entry, `docs/notes/<ID>.md`, or a DECISIONS
>   entry; the ledger line keeps the loop and a pointer. The start hook
>   truncates over-cap items and names them. Closure evidence is one line.
> - Never rewrite or regenerate this file. Lines are only appended, or edited
>   in place from `[ ]` to `[x]` (done — append `→ DONE <date>: <one line>`)
>   or `[-]` (dropped — append the reason).
> - Don't delete or strike an open item you don't recognise — it may belong
>   to a concurrent session running in this same checkout.
> - `/end` reconciles: disposition every `[ ]` you touched, append anything
>   this session queued but didn't capture, prune `[x]`/`[-]` lines older
>   than `prune_closed_after_days` (history lives in git), report the open
>   count against `open_soft_max` and list items older than `stale_after_days`
>   as route-or-close.
> - **IDs are permanent and never reused.** Single-track: `L-1, L-2, …`.
>   **Multi-track** (tracks declared in `protocol.json`): each track mints with
>   its own prefix and its own counter — `D-1, D-2, …` and `M-1, M-2, …` — so
>   two sessions can append at once without colliding. The prefix says who
>   WROTE it. A tag right after the ID says who ACTS on it: `→mobile`,
>   `→desktop`, or `→all` (`D-2 →mobile (2026-09-08) …`; also accepted after
>   the date); no tag = the writer's own track. Legacy `L-` items keep their
>   numbers forever and were tagged once at migration. If a collision ever
>   lands anyway, renumber the
>   later-referenced item and keep the alias in the surviving line.

<!-- Items start here. Shape: `- [ ] L-N (YYYY-MM-DD) <loop, done-condition>`; closed: `[x] … → DONE <date>: <one line>` or `[-] … → dropped <date>: <reason>`. No example items in this comment: the start hook counts every line that begins with "- [" as an item, comments included. -->
- [ ] L-3 (2026-09-05) User: warranty / RMA check with AYN about the ~9 kHz fan tone BEFORE any physical fan work (gates the B2 hardware track).
- [ ] L-4 (2026-09-05) Put a second copy of the stock ABL backup (`C:\Users\haith\Downloads\odin3-abl-backup\`) somewhere off this PC (cloud); the device copy lives on Android's userdata and would not survive an internal install.
- [ ] L-5 (2026-09-05) Download-plateau experiment for B1: during a Steam download compare Balanced vs Eco — if the speed plateau (~120–130 Mbit/s on the first game) stays put it's the SD write ceiling, if it climbs toward 300+ it's the CPU cap; the B1 logger should record net RX vs `mmcblk0` writes so this stops being guesswork. Also the raw `dd` card benchmark once no download is running.
- [ ] L-6 (2026-09-05) User report, once, not reproduced: switching to **Performance** mid shader-compile sent the fan to max (by design: `performance` governor + `gpu_min=1.0` + aggressive curve) and the fan stayed loud ~2 min after switching back (by design: `ramp_down=6`/tick), but the **game froze** while the OS kept running; user rebooted. Previous-boot journal shows no OOM, thermal, GPU fault, or hung task. B3: try to reproduce a live profile switch during a shader compile; consider whether Performance should pin `gpu_min` at 100% at all.
- [ ] L-13 (2026-09-07) B4 sleep checks — plan and rationale in ROADMAP → B4 "Plan (2026-09-07, L-13)": (a) Bluetooth `Powered` state across s2idle on this unit (upstream #264); (b) `qcom_stats` aosd/cxsd tick on SM8750 via `armada-sleep-debug` + `rtcwake` (#274); (c) user: left side of the screen warm in sleep (#265). Done when all three are measured on this unit and recorded in B4. (Shortened 2026-09-11 at the protocol migration; the analysis moved to ROADMAP.)
- [ ] L-15 (2026-09-07) B4: the battery exposes `charge_control_start_threshold` / `charge_control_end_threshold` (seen 2026-09-07 in `/sys/class/power_supply/battery/`) — the 80 % charge-limit knob upstream #363 asks for. Read the current values, test whether a write sticks and whether the PMIC honours it (charge to the cap, stop), then decide overlay (udev/tmpfiles) vs B9 PR. Also seen: `time_to_empty_avg`, `charge_counter`, `charge_full` — candidates for the B1 logger v2.
- [ ] L-16 (2026-09-07) B3: `gpu_max` is a ratio of the 1100 MHz devfreq table top, not the 832 MHz cap (`armada-powerd` `choose_at_most(freqs, int(freqs[-1]*gpu_max))`) — the user's Balanced 0.80 and Eco's factory 0.80 are no-ops (run 1: Eco at 832 MHz 78 % of the time). B3: test a real cap (0.60 → 660 MHz) as its own variable, via the Power tab (UI-owned, D-4). B9: issue or PR — ratio against the usable max, or show the resulting MHz in the UI.


- [ ] L-22 (2026-09-12) B4/B9: Steam re-suspends the device ~1.3 s after any wake from a battery sleep longer than its idle-suspend timeout (900 s) — root cause in ROADMAP B4 (L-20). Decide the fix with the user: Steam Power setting "Suspend after" on battery = Never (simplest, loses screen-on-idle protection) vs a resume hook that makes the wake count as activity; then file the upstream issue with the Steam log excerpt. Done when a long battery sleep wakes and stays awake, and the issue is filed.
  Update 2026-09-12: parked by the user (costs < 1 %/night; press twice). Reports (Valve, Armada) queued.
- [-] L-23 (2026-09-12) B4: 60-min comparison sleeps to pin the real hook saving and the 10-min→60-min gap: (a) hook disabled (`chmod -x /etc/systemd/system-sleep/20-odin3-wifi-off-in-sleep`, restore after), (b) hook on again, same charge band, off charger, same script `/var/tmp/sleep60.sh`. Also try to name the ~25–30-min periodic idle exit (a kernel trace or `/sys/kernel/debug/wakeup_sources` diff taken *before* the wake path runs). Done when both mA figures are in ROADMAP B4. → DROPPED 2026-09-28: superseded by L-24 on the new kernel (hook removed).
  Update 2026-09-12 04:05: (a) run — hook off 168 mA ≈ 0.65 W vs hook on 187 mA ≈ 0.73 W over 60 min; no visible hook benefit at 1 h. Remaining: the alternating repeat pair (2× on, 2× off, same charge band) before deciding whether overlay v2 stays; the periodic waker is still unnamed.
- [x] L-24 (2026-09-28) B4: re-baseline sleep on upstream's s2idle fix (#545, image `20260928.410bcf2`, kernel 7.2.6): 60-min `sleep60.sh` run started 09:16, hook on, Eco, 81 %, off charger, ~2 min after boot — read `/var/tmp/sleep-test-*-60min-newkernel-hook/log.txt` after ~10:17, then the hook-off hour (started 10:19, hook `chmod -x`, Eco, 80 %; revert `chmod +x`) (supersedes L-23's pair on the old kernel). Also note `aosd`/`cxsd`/`ddr` counts (still 0 before the run). Done when both figures are in ROADMAP B4. → DONE 2026-09-28: hook on 54 mA ≈ 0.22 W, off 43 mA ≈ 0.17 W; hook dropped (overlay v3); aosd/cxsd/ddr still 0.
- [ ] L-25 (2026-09-28) B4: go below 0.17 W — find what holds DDR/CX awake in s2idle on the new kernel (plan + research in ROADMAP B4). Steps: overnight sleep on overlay v3 to confirm ~43 mA; read-only `sync_state() pending` / `interconnect_summary` / `pm_genpd_summary` / per-subsystem `qcom_stats` (device awake 5 min); cdsp stop + 60-min sleep; then, with a backup and the user's go (D-7), an own-kernel test without the PCIe `opp-suspend-1` to see whether SM8750 really resets. Done when the floor is explained or lowered.
