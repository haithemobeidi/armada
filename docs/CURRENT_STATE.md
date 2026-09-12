# armada-odin3 — Current State

**Last updated:** 2026-09-12 04:10 (session 6 mini-wrap — overnight + two 60-min sleep measurements; L-20 root-caused to Steam's idle timer; fan-off signed off by ear)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**Drain first (user's call 2026-09-12 04:30): find where the ~0.7 W in sleep goes, and what `/etc` can still take off it before the kernel route.** Measure-first, 60-min alarm sleeps by `charge_counter` (`/var/tmp/sleep60.sh`, edit the folder tag per run; key-wake afterwards because of L-22), game quit, off charger, same charge band, one variable per run: (1) **hook on / off / on / off** (L-23b) to settle whether overlay v2 stays; (2) **`deep` for 60 min** (a `pre` hook writing `/sys/power/mem_sleep`, as the 10-min `sleep10-deep.sh` did) — the 10-min A/B said "no gain over the Wi-Fi hook", which is now suspect; (3) **name the ~25-min periodic idle exit** without the wake path swamping the counters (kernel `pm_debug_messages`/wakeup-source tracing read from the `post` hook before thaw, or `/sys/kernel/debug/wakeup_sources` diffed inside the hook). Then the **SM8750 sleep-depth upstream issue** with all the numbers (the SoC never enters AOSD/CXSD; thorch regulator sleep-set patches + Odin 3 DT, ROADMAP B4) — that kernel work is the real prize (0.7 W → a fraction) and sits under D-7. L-22 (Steam re-suspend) is parked: no workaround, press twice, reports later. Game-audio sleep test and B1's idle recording stay behind these.

**Current phase:** B4 Battery + sleep — L-22 decision, L-23b hook-on/off pair, then game-audio sleep test (the statusline parses this line)

**Build status:** working (`tools/check-delta.sh` OK)

**Remote:** `origin/odin3-tuning` = HEAD after this wrap's push. Fork point = `upstream/main` = `a9a38ba`. `main` = `origin/main` = `14230df` (mirror, untouched). Device image `20260911.a9a38ba`. **Other machine after a rebase:** `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.

---

## Optional loose ends (NOT the next step)

Open: L-3 (user: AYN warranty check), L-4 (user: off-PC ABL backup copy), L-5 (download-plateau experiment), L-6 (Performance-switch freeze repro, B3), L-13 (B4: (c) warm screen side still the user's; (a)(b) answered), L-15 (B4: charge thresholds not enforced), L-16 (B3: `gpu_max` ratio no-op; B9 issue/PR). See `docs/SESSION_LEDGER.md`.

---

## What happened this session (2026-09-12, 00:30–04:10)

- **Overnight sleep read (L-19 closed):** 16:15 → 00:36, 8 h 21 min, 87 → 65 % ≈ 0.85 W by gauge, one unbroken suspend, Wi-Fi hook worked, Bluetooth off. CPU cluster outside its idle state ~2 s all night, so CPU wakes are not the drain.
- **60-min coulomb sleeps:** hook on 187 mA ≈ 0.73 W; hook off 168 mA ≈ 0.65 W. **The 10-min figures (0.47 / 0.75 W) do not scale; real sleep drain ≈ 0.7–0.85 W ≈ 40 h from full, and the Wi-Fi hook's saving is unproven at 1 h** (L-23b pending). CURRENT_STATE's old "5–6 % per 8 h" expectation was wrong (should have been ~11 %).
- **L-20 root-caused (closed):** D-Bus monitor + logind debug + Steam's log: the second suspend is Steam's battery idle-suspend (900 s) firing at wake because its idle clock counts the suspended time. Not powerbuttond, not logind. Research (web + code): unreported anywhere; SteamOS has no mitigation, it just wins the race; no URI/console command resets the timer; `IdleSuspendBatterySeconds` in `config.vdf` is the setting. Options ranked in ROADMAP B4; user pushback recorded above.
- **Fan-off curve signed off by ear (L-18 closed):** "fine when it's off"; the tone at ~30 % PWM is B2's whine-band work (recorded in ROADMAP B2).
- **Device now:** overlay v2 applied and hook **re-enabled** (0755, 04:03) after the no-hook hour; logind log level back to `info`; bus monitor killed. Test scripts and logs remain in `/var/tmp` (`sleep60.sh`, `arm-l20.sh`, `collect*.sh`, `l20-busmon.txt`, `sleep-test-*`). Battery 56 %, off charger, user was told they may plug in.

## Active blockers

None. Device/repo parity: overlay v2 = repo, hook executable again; `device-state/` unchanged since 2026-09-11 12:14.

---

## Notes & things to watch

- **Owner rules:** performance overlay off outside games; quit the game before sleeping; a forgotten screen-on device drains ~2.1 W; after a battery sleep > 15 min expect to press the power button twice until L-22 is settled.
- **Sleep measurement rule (new):** 10-min cycles are only good for A/B of large effects; drain figures need ≥ 60 min by `charge_counter` (`/var/tmp/sleep60.sh`; the device re-suspends on the alarm wake because of L-22, so it must be key-woken afterwards and Wi-Fi is only up for ~1 s at the alarm).
- **`suspend-dispatch` forces `mem_sleep=s2idle` on every suspend**; a system-sleep hook is the only `/etc` way to change the mode.
- **Launching a detached script over SSH:** `odin.py sudo "bash -c 'setsid nohup bash /var/tmp/x.sh >/dev/null 2>&1 </dev/null &'"`; a bare `nohup … &` dies with the session. The SSH call hangs when the device suspends under it — wrap in `timeout`.
- **The % battery gauge lies above ~90 %** — use `charge_counter` deltas (µAh) for drain.
- **Calling `odin.py put`/`get` from Git Bash needs `MSYS_NO_PATHCONV=1`.**
- **Upstream #403** (Pocket Fit Elite, same SoC): native sleep sometimes never wakes — still not seen here (now ~20 cycles).
- In-game frame cap for the Sep 7 runs still unknown; `power_supply/battery/power_now` unverified; fresh deployments lose `/etc` and `/var` (re-push the overlay after any installer run).
