# armada-odin3 — Current State

**Last updated:** 2026-09-11 15:25 (session 5 `/end` — rebase, idle CPU solved, fan-off curve, sleep measured + overlay v2; overnight check L-19 queued)

> This file carries only the **NEXT ACTION** + this-session deltas. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**First, read the overnight result (L-19):** the user slept the device ~15:30 on 2026-09-11 with the game quit, overlay v2 live and the fan-off curve; ~7 h later they report battery % at wake, Wi-Fi state, Steam reconnect time, fan noise at idle. Expected ~5–6 % per 8 h at 0.47 W; a much bigger drop means something (audio path? Bluetooth? a self-wake) is different overnight — pull `journalctl` for the sleep window and `charge_counter` deltas first. Then **B4, sleep with a game open (1.65 W vs 0.47 W).** One 10-min sleep with the game **muted / its audio device closed** (user parks it in a menu, says ready; `/var/tmp/gamesleep10.sh` on the device does the cycle), then one with the GPU forced to its floor via the Power tab — one variable each, `charge_counter` deltas. Then: the **idle-to-sleep timeout** (awake idle is 2.1 W screen-on; Steam's setting), an **upstream issue** for SM8750 sleep depth with today's numbers (ROADMAP B4, `device-data/sleep-test-20260911-122117/`), and the L-18 fan sign-off by ear. Ask the user for last night's battery % before/after sleep (hook v2 live since 14:23). B1's idle recording + pitch sweep stay paused behind B4.

**Current phase:** B4 Battery + sleep — game-sleep audio test, idle timeout, upstream issue (the statusline parses this line)

**Build status:** working (`tools/check-delta.sh` OK on all 34 delta files)

**Remote:** `origin/odin3-tuning` = HEAD after this wrap's push. Fork point = `upstream/main` = `a9a38ba` (rebased 2026-09-11, 25 commits replayed clean). `main` = `origin/main` = `14230df` (mirror, untouched). Device image `20260911.a9a38ba`. **Other machine after a rebase:** `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.

---

## Optional loose ends (NOT the next step)

Open: L-3 (user: AYN warranty check), L-4 (user: off-PC ABL backup copy), L-5 (download-plateau experiment), L-6 (Performance-switch freeze repro, B3), L-13 (B4 sleep checks), L-15 (B4: charge thresholds not enforced), L-16 (B3: `gpu_max` ratio no-op; B9 issue/PR), L-17 (protocol migration gate — closes itself when the next fresh session's start→`/end` cycle passes). See `docs/SESSION_LEDGER.md`.

---

## What happened this session

- **Rebase** `odin3-tuning` onto `upstream/main` `a9a38ba` (50 commits, none sleep-related), pushed `--force-with-lease`.
- **Idle CPU (B5) solved:** the "30 % in the library" was Steam's performance overlay — 33 % / GPU 832 MHz with the FPS counter on, 3 % / 160 MHz off. Owner rule: overlay only in game.
- **Fan-off at idle (B2):** the user's Relaxed curve never went below 51; set by direct edit on the user's ask to `0:0,50:0,51:51,65:51,76:77,82:102,88:153,98:255` + `min_pwm=0` (same path + reload the app uses; backups on the device). PWM 0 at 40–45 °C all afternoon. L-18 watch.
- **Sleep (B4) measured, 14 cycles:** SoC never enters AOSD/CXSD/DDR low-power in s2idle *or* deep; CPU cluster does sleep; suspend/wake reliable (all wakes = RTC alarm or power key). 10-min watts: s2idle 0.75, deep 0.49, Wi-Fi off 0.47, deep+Wi-Fi off 0.47, game open 1.65. Bisection cleared Wi-Fi radio, Wi-Fi card, gamepad UART; PCIe RC can't unbind. History: upstream gave the Odin 3 deep sleep on 07-12 and switched everything to s2idle on 09-03 (the user's 09-06 image; death on 09-07).
- **Overlay v2 pushed 14:23:** `etc/systemd/system-sleep/20-odin3-wifi-off-in-sleep` (rfkill around suspend). Verified on a plain cycle and two game cycles; the game survives sleep and is responsive.
- **Kernel research:** Armada's kernel lacks thorch's RPMh regulator sleep-set patches (every rail stays at full power in sleep on mainline) and the Odin 3 DT has the same WAKE# polarity bug thorch fixed on the Odin 2 (gpio104 idles high, DT says active-high). Plan and sources in ROADMAP B4.
- **Tools:** `odin.py push` installs shebang files 0755 and only restarts `armada-powerd` when an `/etc/armada` file was pushed. Raw sleep data in `device-data/sleep-test-*/` (git-ignored).

## Active blockers

None. Device/repo parity: **overlay v2** applied 2026-09-11 14:23 = repo; `device-state/` re-pulled 12:14 after the fan-curve edit = device.

---

## Notes & things to watch

- **Owner rules from today:** performance overlay off outside games; quit the game before sleeping (1.65 W vs 0.47 W); a forgotten screen-on device drains ~2.1 W (14 h).
- **Sleep floor from `/etc` is ~0.47 W ≈ 70 h.** Below that = kernel work under D-7 (ROADMAP B4 plan): thorch `0218`/`0219` + an Odin 3 DT patch (state-mem rails, WAKE# polarity) on `armada-os/armada-packages`.
- **`suspend-dispatch` forces `mem_sleep=s2idle` on every suspend**; a system-sleep hook is the only `/etc` way to change the mode (deep gains nothing over the Wi-Fi hook, so none is installed).
- **Test scripts live on the device in `/var/tmp/`** (`gamesleep10.sh`, `sleep10*.sh`, `bisect.sh`, …; DEVICE.md lists them). All detach with `nohup`, set an RTC alarm, and write `log.txt` in `/var/tmp/sleep-test-<ts>-<tag>/`; fetch after the alarm with `odin.py run cat`. `odin.py sudo` elevates only the first command of a compound string — use a script file. Script output via `odin.py run bash file` came back empty several times; `bash -x file 2>/dev/null` always worked.
- **The % battery gauge lies above ~90 %** — use `charge_counter` deltas (µAh) for drain; consistent to ±1 mAh over 10 min.
- **Calling `odin.py put`/`get` from Git Bash needs `MSYS_NO_PATHCONV=1`.**
- **Upstream #403** (Pocket Fit Elite, same SoC): native sleep sometimes never wakes — not seen here in 14 cycles, watch it.
- In-game frame cap for the Sep 7 runs still unknown; `power_supply/battery/power_now` unverified; fresh deployments lose `/etc` and `/var` (re-push the overlay after any installer run).
