# Armada Control — every knob, what it writes, and what it means on this SoC

Armada Control is the Decky plugin in Steam's Quick Access Menu (`decky/armada-control/`). Its UI (`src/tabs/*.tsx`) talks to `py_modules/armada_control/*.py`, which writes config through the root helper `system_files/usr/libexec/armada/armada-control` (`write_config`, whitelisted paths only). Read this before touching power, fan, or per-game behaviour. Source read at upstream `33e0319`; re-check after a rebase.

## Power tab (`Power.tsx` → `power.py` → `/etc/armada/power-profiles.conf`)

Per profile (Eco / Balanced / Performance — the three names are hardcoded in the daemon; a fourth cannot be added):

| Setting | Key | Range | What it does on the Odin 3 |
|---|---|---|---|
| Fan Curve | `fan_curve` | any `[fan_curve.*]` name, incl. ones created in the Fans tab | Selects the temp→PWM curve `armada-powerd` interpolates. |
| CPU Governor | `cpu_governor` | `schedutil` / `performance` / … | `performance` pins every core to `scaling_max_freq`; heat and battery cost, no fan benefit. |
| CPU Underclock | `cpu_underclock` | `none` / `small` / `medium` / `large` | Applies the `[underclock.SM8750.<tier>]` caps: policy0 / policy6 = 3532.8/4089.6, 2745.6/3072, 2227.2/2246.4, 1785.6/1958.4 MHz. **This is the only "undervolt" — a frequency cap that lets DVFS pick a lower voltage point.** |
| CPU Max (%) | `cpu_max` | 35–100 | A ratio applied on top of the underclock cap (Balanced ships 0.65). |
| GPU Min (%) | `gpu_min` | 0–100 | Floor for the `simple_ondemand` devfreq governor (Performance ships 1.0 = GPU pinned at max). |
| GPU Max (%) | `gpu_max` | 35–100 | Ceiling; 0.80 ≈ 660 MHz of the 832 MHz cap. The user's 0.80 cut the whine a bit (less heat → lower PWM). A **frame-rate cap** or lower **game resolution** achieves the same heat reduction without slowing frames that are needed. |

Profile switching itself happens in Steam's QAM Performance tab (`steamos-manager` → `org.armada.Power` D-Bus). `armada-power status` shows the live state.

## Fans tab (`Fans.tsx` → `fan_curves.py` → same file)

A full curve editor: create a curve from a base, edit points (temp −40…150, PWM 0…255), fullscreen editor, shows the live temperature (average of the three hottest zones, same as the daemon). Also edits `[fan]` `ramp_up` (1–255), `ramp_down` (1–255), `smoothing` (0–0.99), `min_pwm` (0–255).

**Fan-stop rule:** if any saved curve's lowest point has PWM 0, `min_pwm` is forced to 0. So "let the fan stop" is a UI operation, not a file edit. A curve still assigned to a profile cannot be deleted. Factory curves (`relaxed`, `moderate`, `aggressive`) are only written to `/etc` if changed.

Things the tab does **not** expose (un-owned keys, thin): `max_pwm`, `pwm_quantum`, `[suspend]` (`fan_safe_above=55`, `fan_low_pwm=51`, `fan_safe_pwm=128`).

## Compatibility tab (`Compatibility.tsx` → `tweaks.py` → `/etc/armada/game-tweaks.json`, per-game + `global`)

Factory `global` defaults (`/usr/share/armada/game-tweaks.json`): `fexProfile=default`, `cores=null`, `gamescopeCores=null`, `gamescopeNice=-20`, `gamescopeRr=false`, `gamescopeVulkanRealtime=true`, `nice=0`, `scheduler=eevdf`, `wineTopology=true`, thunks Vulkan/GL/drm/WaylandClient/asound on.

| Setting | What it does |
|---|---|
| Default Proton / Apply to New Games | Which Proton build new games get (`ARMADA_PROTON_DEFAULTS` = proton-experimental-arm64, proton_11-arm64, proton-cachyos-11.0-arm64); migration when defaults change. |
| Compatibility Tool (per game) | Proton / native / … |
| Game Resolution | Per-game internal resolution — the cheapest GPU-heat lever there is. |
| FEX Preset | `Default` / `Fast` / `Compatible` / `Custom` — x86 translation accuracy vs speed (`/usr/share/fex-emu/AppConfig`). |
| CPU Cores | `all` / `big` / `prime` / `little` / custom list. On this SoC `big`=0–7, `prime`=6–7, `little` is empty. Pins the game's affinity. |
| Wine CPU Topology | Passes the pinned core list to Wine so the game sees a matching topology. |
| Nice (game) / Nice (gamescope) | −20…19 priorities. |
| CPU Realtime Scheduling | `SCHED_RR` at priority 40 for gamescope. |
| Vulkan Realtime Queue | gamescope's Vulkan queue at RT. |
| CPU Scheduler | `eevdf` (kernel default) / `cosmos` / `lavd` (`scx_*` BPF schedulers, package `scx-scheds`). LAVD is the handheld-oriented one; worth measuring in B3. |
| Advanced: custom env Name/Value | Arbitrary environment for the game. |

Runtime state: `/run/armada/perf-state.json` (what `armada-game-launch` applied); `/var/lib/armada/compat-applied.json`.

## Settings tab (`Settings.tsx` → `system.py`, `controller.py`, `calibration.py`)

| Setting | Writes | Notes |
|---|---|---|
| Controller → Emulation | InputPlumber target (`deck-uhid` default; Xbox 360, DualSense also offered) | Affects what games see and rumble/gyro support. |
| Stick / trigger calibration | `/etc/armada/input-calibration.json` | Per-axis min/center/max/deadzone/anti-deadzone. |
| System → Sleep Mode | `s2idle` ("Native") or `fake` | s2idle is the default since upstream 2026-09-03. |
| System → Enable SSH | `systemctl enable/disable --now sshd` | Our access path. |
| OS Version / ABL Version | read-only | |
| Experimental → Desktop Mode | session default | |
| Experimental → USB File Transfer | `armada-mtp.service` (uMTP responder) | Off by default. |
| Experimental → Automatic ABL Updates | `/etc/armada/abl.conf` `auto_update_enabled=1` | "Updates during shutdown." Currently **on**. Relevant to D-7: the bootloader can change under us at shutdown after an OTA — know this before blaming a boot problem on our tuning. |

## What has no UI (candidates for `device-overlay/` or upstream work)

- Per-device fan/underclock defaults (everything is global or SoC-class today) — ROADMAP B9.
- `max_pwm`, `pwm_quantum`, `[suspend]` fan values.
- Service masking, sysctl, udev rules, hostname.
- Battery charge limit (if the PMIC exposes one — check `power_supply/battery/charge_control_*` in B4).
