# Session Ledger — open items that must not get lost

> **What this is:** the append-and-strike ledger for session-scoped open items —
> queued tests, gates, deferred decisions, watch items, "check on the device
> later". Anything phrased like "next session," "before the rebuild," "queued,"
> "check later," or "watch" gets a line HERE at the moment it's said.
>
> **Rules (full rationale in `PROTOCOL.md` → "Open-item ledger discipline"):**
>
> - **Append at the moment of queueing; strike at the moment of resolution.**
>   Never wait for /end — long sessions get context-compacted and end-of-session
>   recall loses early facts.
> - Never rewrite or regenerate this file. Lines are only appended, or edited
>   in place from `[ ]` to `[x]` (done — append `→ DONE <date>: <one-line
>   evidence>`) or `[-]` (dropped — append the reason).
> - Don't strike an open item you don't recognize — it may belong to a session
>   on the other machine.
> - `/end` reconciles: disposition every `[ ]`, append anything this session
>   queued but didn't capture, prune `[x]`/`[-]` lines older than 7 days
>   (their history lives in git).
> - Not for block status (ROADMAP spine) or hardware facts (`docs/DEVICE.md`).
>   One concept, one home.
> - IDs increment forever (L-1, L-2, …); never reuse a number.

<!-- Items start here. Example shapes:
- [ ] L-1 (YYYY-MM-DD) Confirm the fan restarts from a full stop (queued for the first on-device fan session)
- [x] L-1 (YYYY-MM-DD) Confirm the fan restarts … → DONE YYYY-MM-DD: restarts at pwm 40 from 0, verified 3×
- [-] L-2 (YYYY-MM-DD) Log fan RPM → dropped YYYY-MM-DD: hwmon has no fan1_input, RPM is not readable on this unit
-->

- [x] L-1 (2026-09-05) Rebase `odin3-tuning` onto `upstream/main` — 3 commits behind after the user's OTA to `20260904.14230df`; user-approved action at a quiet point (D-2), suggested before B1 work starts. → DONE 2026-09-05: rebased 33e0319→14230df, 5 commits replayed, no conflicts, force-with-lease pushed; `main` fast-forwarded and pushed. User then delegated future rebases (D-2 amended).
- [ ] L-2 (2026-09-05) B0 gate: open a fresh session after the first `/end` and confirm the SessionStart hook injects state, reports origin currency, and reports the upstream drift count.
- [ ] L-3 (2026-09-05) User: warranty / RMA check with AYN about the ~9 kHz fan tone BEFORE any physical fan work (gates the B2 hardware track).
- [ ] L-4 (2026-09-05) Put a second copy of the stock ABL backup (`C:\Users\haith\Downloads\odin3-abl-backup\`) somewhere off this PC (cloud); the device copy lives on Android's userdata and would not survive an internal install.
- [ ] L-5 (2026-09-05) Download-plateau experiment for B1: during a Steam download compare Balanced vs Eco — if the speed plateau (~120–130 Mbit/s on the first game) stays put it's the SD write ceiling, if it climbs toward 300+ it's the CPU cap; the B1 logger should record net RX vs `mmcblk0` writes so this stops being guesswork. Also the raw `dd` card benchmark once no download is running.
- [ ] L-6 (2026-09-05) User report, once, not reproduced: switching to **Performance** mid shader-compile sent the fan to max (by design: `performance` governor + `gpu_min=1.0` + aggressive curve) and the fan stayed loud ~2 min after switching back (by design: `ramp_down=6`/tick), but the **game froze** while the OS kept running; user rebooted. Previous-boot journal shows no OOM, thermal, GPU fault, or hung task. B3: try to reproduce a live profile switch during a shader compile; consider whether Performance should pin `gpu_min` at 100% at all.
