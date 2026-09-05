# The device — AYN Odin 3 running ArmadaOS

Hardware facts, access, sysfs paths, config ownership, backups, and **what is currently applied on the handheld**. Read before any device work. Facts below were read from the live device on 2026-09-05 unless marked otherwise; re-verify anything that matters after an OTA.

## Identity

| | |
|---|---|
| Device | AYN Odin 3 (`ARMADA_DEVICE_ID=ayn-odin-3`, `ARMADA_SOC_CLASS=SM8750`) |
| SoC | Snapdragon 8 Elite, SM8750, 3 nm. 8 cores: 6× Phoenix M + 2× Phoenix L (Oryon). Adreno 830. |
| RAM / swap | 16 GB (14 963 MiB usable); zram swap 14.6 GB, `vm.swappiness=180` |
| OS | ArmadaOS `20260904.14230df` from `ghcr.io/armada-os/armada:testing` (bootc, composefs root; rollback deployment `20260903.33e0319`), Fedora 44, kernel `7.2.3`. Updated by the user 2026-09-05. |
| Hostname | `fedora` (default; avahi runs but `armada.local` does not resolve — backlog item to set a real hostname) |
| Boot | ROCKNIX ABL flashed (version in `abl/release.env`); Armada boots from the **SD card**; stock Android intact on internal UFS |
| Wi-Fi | `wlp1s0`, `ath12k_wifi7_pci` (WCN7850 family), 6 GHz ch 165 @ 160 MHz |

## Access

- **SSH:** `ssh armada@192.168.1.188` — key auth from this PC (`~/.ssh/id_ed25519.pub` installed in `/var/home/armada/.ssh/authorized_keys`). `tools/odin.py` wraps it.
- **Password** (image default, every Armada install): user `armada`, password `armada`. `sudo` needs it (only a few `systemctl`/session commands are NOPASSWD).
- **Toggle:** Armada Control → Settings → System → **Enable SSH** (runs `systemctl enable --now sshd`). Turn it off if the device leaves the home network.
- **IP is DHCP and has moved before** (was `.186`). Find it in Steam → Settings → Internet, or `arp -a` for the Atheros OUI `00-03-7f`, or scan the LAN for port 22.
- **ADB is Android-only.** Nothing on the Armada side speaks it.
- **No terminal for the user.** Claude does the SSH work; the user observes.

## CPU / GPU frequency tables (from sysfs, kernel 7.2.3)

| Policy | CPUs | Capacity | Min | Max | Available steps (MHz) |
|---|---|---|---|---|---|
| `policy0` | 0–5 (Phoenix M) | 836 | 384 | **3532.8** | 384, 556.8, 748.8, 960, 1152, 1363.2, 1555.2, 1785.6, 1996.8, 2227.2, 2400, 2745.6, 2918.4, 3072, 3321.6, 3532.8 |
| `policy6` | 6–7 (Phoenix L) | 1024 | 1017.6 | **4089.6** | 1017.6, 1209.6, 1401.6, 1689.6, 1958.4, 2246.4, 2438.4, 2649.6, 2841.6, 3072, 3283.2, 3513.6, 3801.6, 4089.6 |

Governors: `ondemand userspace performance schedutil`. The spec sheet's 4320 MHz does not exist in this kernel's table; percentages below use the real 4089.6.

| Underclock tier (`[underclock.SM8750.*]`) | policy0 | policy6 |
|---|---|---|
| none | 3532.8 (100%) | 4089.6 (100%) |
| small | 2745.6 (78%) | 3072.0 (75%) |
| medium *(Balanced default)* | 2227.2 (63%) | 2246.4 (55%) |
| large *(Eco default)* | 1785.6 (51%) | 1958.4 (48%) |

`ARMADA_BIG_CORES=0-7`, `ARMADA_PRIME_CORES=6-7`, no little cores, no IRQ core set (powerd spreads IRQs `ff`).

**GPU** (`/sys/class/devfreq/3d00000.gpu`, governor `simple_ondemand`): available 160 … 1100 MHz in 14 steps, but `max_freq` is **832 MHz** (kernel cap; the daemon reports `gpu_auto_max=832`, `manual_gpu_clock_max=1100`). **UFS** devfreq: 100 / 403 MHz.

No voltage control exists anywhere (kernel, daemon, plugin). "Undervolt" on this platform = cap frequency and let DVFS pick the lower OPP.

## Thermal and fan

- **55 thermal zones.** `armada-powerd` and the Fans tab use zones whose type starts with `cpu`, `gpu`, `gpuss`, `video`, `mem` — that is 12 `cpu-*`, 4 `cpuss-*`, 8 `gpuss*`, 1 `video`. (`ddr-thermal` is **not** counted.) The fan temperature is the **average of the three hottest** of those. `read_temp_max` (suspend path) uses the single hottest.
- Cooling devices: `cpufreq-cpu0`, `cpufreq-cpu6`, `devfreq-3d00000.gpu`, `pwm-fan`, `ath12k_thermal`.
- **Fan:** `hwmon54`, name `pwmfan`, files `pwm1`, `pwm1_enable`. **There is no `fan1_input` — the fan has no tachometer.** RPM can never be read; every fan fact is a PWM fact. `FanRpm` on D-Bus is always 0.
- Daemon loop (`system_files/usr/libexec/armada/armada-powerd`): tick 3 s → temp → EMA `smoothing=0.5` → curve interpolation → slew (`ramp_up=36`, `ramp_down=6`) → clamp `[min_pwm, max_pwm]` → quantise to `pwm_quantum=8` → write `pwm1`. Factory `min_pwm=51`. Fan-stop (PWM 0) is supported by the Fans tab: saving any curve whose lowest point is 0 forces `min_pwm=0`.
- Observed 2026-09-05, plugged in, Steam home screen, Balanced: cpu zones 58–61 °C, gpuss 57–60, fan `pwm1=56`, daemon `temperature=61`. Load average 3.7–5.5 (see ROADMAP B5).

## Power and battery

- `power_supply/battery`: `status`, `current_now` (µA), `voltage_now` (µV), `power_now` (reported ~67.8 W while I×V ≈ 4.7 W — **unit/scaling suspect, don't trust until checked**), `capacity`. `upower` shows no energy counters (0 Wh), rate 4.9 W while charging at 97%.
- Also present: `qcom-battmgr-usb`, `qcom-battmgr-wls` (wireless), `ucsi-source-psy-pmic_glink.ucsi.01` (USB-C PD source: 3 A).
- Sleep: `/sys/power/mem_sleep` = `[s2idle] deep`. Armada's sleep modes: `s2idle` ("Native", default since upstream 2026-09-03) or `fake`.

## Storage

| Device | Size | What |
|---|---|---|
| `mmcblk0` (SD card) | 953 GB | **Armada.** `p3` btrfs → `/sysroot` and `/var` (28 GB used). Root is composefs. |
| `sda` (internal UFS) | 464.5 GB | **Stock Android**, untouched. `sda15` 12 GB, `sda16` 16.5 GB, `sda17` 435.9 GB = `userdata`. |
| `sdb`, `sdc` | 20 MB each | UFS boot LUNs |

Internal install (ROADMAP B8, DECISIONS D-7): `armada-installer` shrinks `userdata`, **factory-resets Android** (user data wiped, system kept), dual-boots; `armada-installer reset` returns the space. Not done, deliberately.

## Config ownership (DECISIONS D-4)

| File on device | Writer | Our handling |
|---|---|---|
| `/etc/armada/power-profiles.conf` | Armada Control **Power tab** (`[general] default_profile`; per-profile `cpu_governor cpu_max cpu_underclock gpu_max gpu_min fan_curve`) and **Fans tab** (`[fan_curve.*]`; `[fan]` `ramp_up ramp_down smoothing min_pwm`) | UI-owned. Tune in the UI; `tools/odin.py pull` records it in `device-state/`. |
| `/etc/armada/game-tweaks.json` | Armada Control **Compatibility tab** | UI-owned, recorded. |
| `/etc/armada/input-calibration.json` | Armada Control **Settings → calibration** | UI-owned, recorded. |
| `/etc/armada/abl.conf` | Armada Control **Settings → Automatic ABL Updates** (`auto_update_enabled=1`) | UI-owned, recorded. |
| `/var/lib/armada/powerd.state`, `/var/lib/armada/compat-applied.json`, `/run/armada/perf-state.json` | Daemons (runtime) | Read-only; pulled into probes for context. |
| Anything else under `/etc` (sysctl, systemd drop-ins, udev, our scripts/units) | **Us** | Repo-owned: `device-overlay/`, pushed by `tools/odin.py push`. |

Factory defaults for the UI-owned files live in the image at `/usr/share/armada/` and are layered under `/etc`. A malformed `/etc` file is **silently dropped** by both the daemon and the plugin (backed up as `*.invalid-<timestamp>`) — check `journalctl -u armada-powerd` after any edit.

## What is applied on the handheld right now

- **`device-overlay/` version applied:** none (v0 — nothing pushed yet).
- **UI-owned state as last pulled:** `device-state/` (2026-09-05 02:45, after the OTA). Balanced has `gpu_max = 0.80` (set by the user in the Power tab; reduced the whine a bit), everything else factory; `abl.conf` `auto_update_enabled=1`; `game-tweaks.json` and `input-calibration.json` do not exist yet (nothing set).

Update this section at every pause that changes the device and at `/end` (Step 1e).

## Backups and recovery

- **Stock ABL** (bootloader) backup, both slots identical, SHA256 `1e732436098279c82637460b1680e05e80072b2d93a56003935e928d4f9068fd`, 1 MiB each, 236 136 non-zero bytes (real data): `C:\Users\haith\Downloads\odin3-abl-backup\` (`abl_a.img`, `abl_b.img`, `restore_backup_abl.sh`). A device copy sits at `/sdcard/rocknix_abl/SM8750/` **on Android's internal storage — an internal install would wipe it**; the PC copy is the one that counts (consider a cloud copy).
- **Flashed ABL:** `abl_signed-SM8750.elf` from the ROCKNIX ABL release pinned in `abl/release.env`; integrity was checked against its `.sha256`.
- **SD image:** `armada-20260817.img.gz` (SHA256 `586d21c2…19c6d`, matched the published hash), written with `C:\Users\haith\Downloads\flash-armada.ps1`, read back and verified byte-for-byte. The script matches the target disk on serial AND size AND USB bus AND non-system, and aborts unless exactly one disk matches — the card reader reports the same serial for every slot.
- **Recovery ladder:** (1) delete the offending `/etc` file over SSH, restart the daemon; (2) bootc rolls back to the previous deployment (`91armada-ostree-fallback` dracut module); (3) pull the SD card → device boots Android from internal; (4) ABL "UNINSTALL CFW" / restore the stock ABL from the backup.

## Gotchas learned the hard way (Android-side, from the ABL flashing session)

- On Android, `/sdcard` is **internal** storage; the physical card was `/storage/F0EE-C523`.
- Internal storage is FUSE and cannot hold the execute bit, so the on-device root-script tool showed the internal folder as empty — run scripts from the SD-card copy (byte-identical, absolute paths inside).
- `backup_abl.sh` hardcodes its output to `/sdcard/rocknix_abl/SM8750/`; the folder must exist on internal storage or `dd` silently writes nothing — this is why the first backup attempt produced no files.
- Production Android: `adbd cannot run as root`, no `su`; ADB could not help with root steps.

## Fan-noise leads (unverified, from the first assessment)

- Widely reported **~9 kHz tone** on early Odin 3 units; described as a physical characteristic of the cooling assembly. Software controls whether and how fast the fan spins, not the tone itself.
- Owner-community leads not yet read: Facebook group `9827715657247540` threads "Ayn replacement fan for odin 3 issue" and "Fixing intermittent noisy fan on Odin 3 with lubricant" (suggest a bearing fault in a subset of units); Reddit `r/OdinHandheld/comments/1u07zc3/high_pitched_fan_noise/` (Claude cannot fetch reddit; paste it in).
- No fan part number or dimensions published anywhere. Do **not** 3D-print an impeller (balance/tolerance). For an aftermarket blower the trap is static pressure, not CFM.
- **Warranty / RMA check with AYN comes before any physical work.**
