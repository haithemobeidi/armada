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
- [x] L-1 (2026-09-05) Rebase `odin3-tuning` onto `upstream/main` — 3 commits behind after the user's OTA to `20260904.14230df`; user-approved action at a quiet point (D-2), suggested before B1 work starts. → DONE 2026-09-05: rebased 33e0319→14230df, 5 commits replayed, no conflicts, force-with-lease pushed; `main` fast-forwarded and pushed. User then delegated future rebases (D-2 amended).
- [x] L-2 (2026-09-05) B0 gate: open a fresh session after the first `/end` and confirm the SessionStart hook injects state, reports origin currency, and reports the upstream drift count. → DONE 2026-09-06: fresh session injected CURRENT_STATE, reported origin current and 14 upstream commits, branch guard silent. B0 closed.
- [ ] L-3 (2026-09-05) User: warranty / RMA check with AYN about the ~9 kHz fan tone BEFORE any physical fan work (gates the B2 hardware track).
- [ ] L-4 (2026-09-05) Put a second copy of the stock ABL backup (`C:\Users\haith\Downloads\odin3-abl-backup\`) somewhere off this PC (cloud); the device copy lives on Android's userdata and would not survive an internal install.
- [ ] L-5 (2026-09-05) Download-plateau experiment for B1: during a Steam download compare Balanced vs Eco — if the speed plateau (~120–130 Mbit/s on the first game) stays put it's the SD write ceiling, if it climbs toward 300+ it's the CPU cap; the B1 logger should record net RX vs `mmcblk0` writes so this stops being guesswork. Also the raw `dd` card benchmark once no download is running.
- [ ] L-6 (2026-09-05) User report, once, not reproduced: switching to **Performance** mid shader-compile sent the fan to max (by design: `performance` governor + `gpu_min=1.0` + aggressive curve) and the fan stayed loud ~2 min after switching back (by design: `ramp_down=6`/tick), but the **game froze** while the OS kept running; user rebooted. Previous-boot journal shows no OOM, thermal, GPU fault, or hung task. B3: try to reproduce a live profile switch during a shader compile; consider whether Performance should pin `gpu_min` at 100% at all.
- [x] L-7 (2026-09-06) **Run the internal install (D-9):** with Armada booted from the SD card, `armada-installer install --userdata-gib 16` as root over SSH (or the Desktop Mode GUI with the slider at 16). D-7 backup step first: confirm the PC ABL backup still hashes to the SHA256 in `docs/DEVICE.md` and that L-4's off-PC copy exists. Then power off, SD card out, power on, ABL boot source = Internal, Armada boots. → DONE 2026-09-06: user ran the GUI installer at 16 GiB right after the `/end`; verified over SSH `root=sda20`, `userdata` 16 GiB, boots with the card in.
- [x] L-8 (2026-09-06) After L-7: `tools/odin.py probe`, rewrite `docs/DEVICE.md` Storage + Boot rows (new `sda` layout, `/var` device, SD card's new role), check IP/hostname unchanged, re-run the download-plateau check (L-5) on internal storage — B8's before/after. → DONE 2026-09-06 (this wrap): probe `device-data/probe-20260906-143753.txt`, DEVICE.md Storage/Boot/recovery rewritten, IP unchanged, hostname still `fedora`; the plateau re-run stays with L-5.
- [x] L-9 (2026-09-06) Rebase `odin3-tuning` onto `upstream/main` at the first quiet point — 14 commits behind at this `/end` (D-2); do it before B1 work starts. → DONE 2026-09-07: `git rebase upstream/main` 14230df → 04dbfc9, 14 commits replayed, no conflicts, delta still 28 files; pushed --force-with-lease (D-2).
- [x] L-10 (2026-09-06) User: in Steam (Gaming Mode → Settings → Storage) confirm the reformatted SD card appears and pick where new installs go (internal `sda20` is the fast one; the card is bulk space). → DONE 2026-09-06: user saw the card, formatted it again from Steam's button (label `SD`), mounted at `/run/media/armada/SD`.
- [x] L-11 (2026-09-06) `docs/DEVICE.md` "UI-owned state as last pulled" is from the SD-card install; the internal deployment started from image defaults (`gpu_max` 0.80 etc. are gone). Re-pull `device-state/` at the next pause and have the user redo the Power-tab tweaks they want. → DONE 2026-09-06 14:48: re-pulled, byte-identical to the record only because the user had already set `gpu_max = 0.80` again by hand at 14:24 — the fresh deployment had reset the Power tab to factory (user confirmed). Nothing left to redo; the lesson stands: installer runs and reflashes lose UI tweaks.
- [x] L-12 (2026-09-06) Steam's Storage page lists the internal UFS chip ("MT512GAYAZ4U31, 464.5 free of 464.5") as an empty drive next to the SD card — udisks reports it `HintSystem=true`, non-removable, but Android's 17 filesystem-less partitions make Steam treat the disk as formattable. Harmless: Armada's `format-device.sh` only accepts `/dev/mmcblk*` and refuses system disks. Candidate first `device-overlay/` drop-in: a udev rule setting `UDISKS_IGNORE=1` on the internal UFS (`sda`) so Steam stops listing it — and a possible upstream PR, since every Odin 3 internal install will show this. Measure first (B7 cosmetics), don't tack it on. → applied 2026-09-06 14:50 on the user's go: overlay v1 pushed, udev DB has `UDISKS_IGNORE=1` on `sda`–`sdh` and their partitions, udisks `HintIgnore=true`, SD card untouched. Close when the user confirms Steam's Storage page no longer lists the chip (Steam may need a restart). → DONE 2026-09-06: user restarted Steam and the internal chip is gone from Settings → Storage. Overlay v1 does the job; upstream-PR candidate stands (B9).
- [ ] L-13 (2026-09-07) B4 sleep checks — plan and rationale in ROADMAP → B4 "Plan (2026-09-07, L-13)": (a) Bluetooth `Powered` state across s2idle on this unit (upstream #264); (b) `qcom_stats` aosd/cxsd tick on SM8750 via `armada-sleep-debug` + `rtcwake` (#274); (c) user: left side of the screen warm in sleep (#265). Done when all three are measured on this unit and recorded in B4. (Shortened 2026-09-11 at the protocol migration; the analysis moved to ROADMAP.)
- [x] L-14 (2026-09-07) Goal refinement from the user (battery first; 60 fps light / 30 fps modern; 2–3 retuned profiles): reword the B3 and B4 gates in ROADMAP.md accordingly on the user's go, and treat the gamescope frame-limiter undershoot/perf-drop (upstream #45, #276, #322 — reproduced on Odin 3 Max, no fix landed) as a B3 blocker: test in-game limiter / DXVK_FRAME_RATE env / gpu_min floor as workarounds. → DONE 2026-09-07: ROADMAP intro (owner's target) + B3/B4 spine gates and block sections reworded on the user's go ("agreed with all").
- [ ] L-15 (2026-09-07) B4: the battery exposes `charge_control_start_threshold` / `charge_control_end_threshold` (seen 2026-09-07 in `/sys/class/power_supply/battery/`) — the 80 % charge-limit knob upstream #363 asks for. Read the current values, test whether a write sticks and whether the PMIC honours it (charge to the cap, stop), then decide overlay (udev/tmpfiles) vs B9 PR. Also seen: `time_to_empty_avg`, `charge_counter`, `charge_full` — candidates for the B1 logger v2.
- [ ] L-16 (2026-09-07) B3: `gpu_max` is a ratio of the 1100 MHz devfreq table top, not the 832 MHz cap (`armada-powerd` `choose_at_most(freqs, int(freqs[-1]*gpu_max))`) — the user's Balanced 0.80 and Eco's factory 0.80 are no-ops (run 1: Eco at 832 MHz 78 % of the time). B3: test a real cap (0.60 → 660 MHz) as its own variable, via the Power tab (UI-owned, D-4). B9: issue or PR — ratio against the usable max, or show the resulting MHz in the UI.
- [x] L-17 (2026-09-11) Protocol migration gate: in the next fresh session confirm the template SessionStart hook injects CURRENT_STATE + open ledger + spine + handoff lines with no template-drift note, the statusline shows the phase, and `/end` runs `tools/check-delta.sh` + the secret scan. Done when one full start→`/end` cycle passes on the global layer. → DONE 2026-09-11: session 5 start hook injected CURRENT_STATE + ledger + spine + handoff with no drift note, statusline showed the phase, `/end` ran check-delta + the secret scan clean.
- [ ] L-18 (2026-09-11) B2 watch: the user's Relaxed curve (Eco) is now 0:0,45:0,60:51,… with min_pwm=0 — fan off below 45 °C confirmed (PWM 0 at 45 °C). The 45→60 °C slope interpolates through PWM 8–48 (quantum 8), a band where this fan may not spin or may tick; no hysteresis in the daemon. Done when the user has lived with it a few days and reports either fine, or tick/cycling near 46–55 °C → move the 60:51 point to 46:51 (Fans tab, UI-owned) and re-pull.
  Update 12:02: curve set by direct file edit on the user's request (same path + `armada-power reload` the Fans tab uses; backup `/var/tmp/power-profiles.conf.bak-20260911`) to 0:0,45:0,46:51,65:51,76:77,82:102,88:153,98:255 — the low-PWM band is gone; remaining watch: on/off cycling around 45–46 °C.
  Update 12:14: fan-off point moved to 50 °C on the user's ask (0:0,50:0,51:51,65:51,…); second backup `/var/tmp/power-profiles.conf.bak-20260911-2`. Watch band is now 50–51 °C.
  Update 2026-09-11 (session 5): (b) answered — `qcom_stats` aosd/cxsd/ddr stay 0 on SM8750 across s2idle *and* deep (ROADMAP B4 2026-09-11); (a) Bluetooth is powered off on this unit (bluetoothctl Powered: no), so the s2idle BT drain is moot until the user turns it on; (c) still the user's.
- [ ] L-19 (2026-09-11) Overnight sleep check, overlay v2 (Wi-Fi off in sleep) + fan-off curve: the user quits the game, notes the battery %, sleeps the device with the power button (~15:30 on 2026-09-11) and reports ~7 h later: battery % at wake, whether Wi-Fi was on, how long Steam took to come back, any fan noise heard at idle before sleep. Expected at 0.47 W: ~5–6 % per 8 h. Done when the numbers are in ROADMAP B4 (and L-18 gets its by-ear sign-off from the same report).
- [ ] L-20 (2026-09-11) Wake-then-resuspend bug (B4/B9): twice today (14:19:24→:25, 16:12:15→:16) the power-key wake was followed ~1 s later by `systemd-logind: The system will suspend now!` with no `armada-powerbuttond: short press` line — the daemon had just re-exec'd for the resume (`watching /dev/input/event0`) and its 2.5 s rebound guard (upstream 9de7cbc) never saw a press, so the request came from elsewhere (logind's own HandleSuspendKey=suspend while the block inhibitor is held? Steam?). Not reproduced on the 14 alarm wakes; only on key wakes. Done when the requester is identified from `journalctl -o json` (_PID/_COMM of the suspend request) and an upstream issue is filed with the two excerpts.
