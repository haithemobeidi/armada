# device-overlay — repo-owned files pushed to the handheld

This tree mirrors the device's filesystem root: `device-overlay/etc/sysctl.d/90-odin3.conf` lands at `/etc/sysctl.d/90-odin3.conf`. `tools/odin.py push` copies every file here (dry-run by default, `--yes` to apply) and restarts `armada-powerd`.

## Rules (DECISIONS D-4)

1. **Only files with no Armada Control writer.** `power-profiles.conf`, `game-tweaks.json`, `input-calibration.json`, and `abl.conf` are UI-owned — tune them in the UI and let `odin.py pull` record them in `device-state/`. Pushing them from here would fight the plugin on its next save.
2. **Every file starts with a comment header**: what it changes, why (measured), the block it belongs to, and how to revert (usually "delete this file and restart X").
3. **One concern per file**, named for it (`90-odin3-<concern>.conf`), so a single change can be reverted alone.
4. **Nothing here touches the boot path** (kernel args, ABL, partitions). That is D-7 territory with its own block and its own go.
5. When a file is pushed, `docs/DEVICE.md` → "What is applied on the handheld right now" names the commit; `/end` Step 1e checks it.

**v3 (2026-09-28):** drops `20-odin3-wifi-off-in-sleep`. On upstream's s2idle fix (#545, image `20260928.410bcf2`) the kernel powers the Wi-Fi link down itself and the hook cost power: 60-min sleeps 54 mA with it vs 43 mA without (ROADMAP B4). `odin.py push` never deletes, so the file was removed on the device by hand; a dropped file always needs that step. Revert: `git show 23bc64d:device-overlay/etc/systemd/system-sleep/20-odin3-wifi-off-in-sleep` back into place and push.

**v2 (2026-09-11):** adds `etc/systemd/system-sleep/20-odin3-wifi-off-in-sleep` (rfkill Wi-Fi around suspend; 0.75 W → 0.47 W measured, ROADMAP B4). `odin.py push` installs shebang files as 0755 since this version; systemd-sleep ignores non-executable hooks.

**v1 (2026-09-06):** `etc/udev/rules.d/99-armada-hide-internal-ufs.rules`. udev files need a reload after a push, which `odin.py push` does not do: `udevadm control --reload-rules && udevadm trigger -c change --subsystem-match=block --sysname-match='sd*'` (the bare `--subsystem-match=block` trigger returned 1 and skipped the UFS devices).
