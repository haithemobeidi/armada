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
- [x] L-2 (2026-09-05) B0 gate: open a fresh session after the first `/end` and confirm the SessionStart hook injects state, reports origin currency, and reports the upstream drift count. → DONE 2026-09-06: fresh session injected CURRENT_STATE, reported origin current and 14 upstream commits, branch guard silent. B0 closed.
- [ ] L-3 (2026-09-05) User: warranty / RMA check with AYN about the ~9 kHz fan tone BEFORE any physical fan work (gates the B2 hardware track).
- [ ] L-4 (2026-09-05) Put a second copy of the stock ABL backup (`C:\Users\haith\Downloads\odin3-abl-backup\`) somewhere off this PC (cloud); the device copy lives on Android's userdata and would not survive an internal install.
- [ ] L-5 (2026-09-05) Download-plateau experiment for B1: during a Steam download compare Balanced vs Eco — if the speed plateau (~120–130 Mbit/s on the first game) stays put it's the SD write ceiling, if it climbs toward 300+ it's the CPU cap; the B1 logger should record net RX vs `mmcblk0` writes so this stops being guesswork. Also the raw `dd` card benchmark once no download is running.
- [ ] L-6 (2026-09-05) User report, once, not reproduced: switching to **Performance** mid shader-compile sent the fan to max (by design: `performance` governor + `gpu_min=1.0` + aggressive curve) and the fan stayed loud ~2 min after switching back (by design: `ramp_down=6`/tick), but the **game froze** while the OS kept running; user rebooted. Previous-boot journal shows no OOM, thermal, GPU fault, or hung task. B3: try to reproduce a live profile switch during a shader compile; consider whether Performance should pin `gpu_min` at 100% at all.
- [x] L-7 (2026-09-06) **Run the internal install (D-9):** with Armada booted from the SD card, `armada-installer install --userdata-gib 16` as root over SSH (or the Desktop Mode GUI with the slider at 16). D-7 backup step first: confirm the PC ABL backup still hashes to the SHA256 in `docs/DEVICE.md` and that L-4's off-PC copy exists. Then power off, SD card out, power on, ABL boot source = Internal, Armada boots. → DONE 2026-09-06: user ran the GUI installer at 16 GiB right after the `/end`; verified over SSH `root=sda20`, `userdata` 16 GiB, boots with the card in.
- [x] L-8 (2026-09-06) After L-7: `tools/odin.py probe`, rewrite `docs/DEVICE.md` Storage + Boot rows (new `sda` layout, `/var` device, SD card's new role), check IP/hostname unchanged, re-run the download-plateau check (L-5) on internal storage — B8's before/after. → DONE 2026-09-06 (this wrap): probe `device-data/probe-20260906-143753.txt`, DEVICE.md Storage/Boot/recovery rewritten, IP unchanged, hostname still `fedora`; the plateau re-run stays with L-5.
- [ ] L-9 (2026-09-06) Rebase `odin3-tuning` onto `upstream/main` at the first quiet point — 14 commits behind at this `/end` (D-2); do it before B1 work starts.
- [x] L-10 (2026-09-06) User: in Steam (Gaming Mode → Settings → Storage) confirm the reformatted SD card appears and pick where new installs go (internal `sda20` is the fast one; the card is bulk space). → DONE 2026-09-06: user saw the card, formatted it again from Steam's button (label `SD`), mounted at `/run/media/armada/SD`.
- [x] L-11 (2026-09-06) `docs/DEVICE.md` "UI-owned state as last pulled" is from the SD-card install; the internal deployment started from image defaults (`gpu_max` 0.80 etc. are gone). Re-pull `device-state/` at the next pause and have the user redo the Power-tab tweaks they want. → DONE 2026-09-06 14:48: re-pulled, byte-identical to the record — `gpu_max = 0.80` is on the internal install (file dated 14:24, set again or restored). Claim that the tweaks were lost was wrong; SSH state and the key were.
- [ ] L-12 (2026-09-06) Steam's Storage page lists the internal UFS chip ("MT512GAYAZ4U31, 464.5 free of 464.5") as an empty drive next to the SD card — udisks reports it `HintSystem=true`, non-removable, but Android's 17 filesystem-less partitions make Steam treat the disk as formattable. Harmless: Armada's `format-device.sh` only accepts `/dev/mmcblk*` and refuses system disks. Candidate first `device-overlay/` drop-in: a udev rule setting `UDISKS_IGNORE=1` on the internal UFS (`sda`) so Steam stops listing it — and a possible upstream PR, since every Odin 3 internal install will show this. Measure first (B7 cosmetics), don't tack it on. → applied 2026-09-06 14:50 on the user's go: overlay v1 pushed, udev DB has `UDISKS_IGNORE=1` on `sda`–`sdh` and their partitions, udisks `HintIgnore=true`, SD card untouched. Close when the user confirms Steam's Storage page no longer lists the chip (Steam may need a restart).
