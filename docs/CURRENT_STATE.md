# armada-odin3 — Current State

**Last updated:** 2026-11-17 (session 12 — Cemu + Wind Waker HD set up on the Odin, audio fixed and user-verified; FF Resonance 4x mod v1.0.5 installed 2026-11-06; image `20261106.d5f0724`; NEXT ACTION is still L-25)

> This file carries only the **NEXT ACTION** + current state. It does **NOT** keep a copy of the block list — that lives in the "📊 Status at a glance" spine in `ROADMAP.md`.

---

## 📍 NEXT ACTION

**B4 L-25: re-baseline a 60-min sleep on the current image**, then go below 0.17 W.
- Image is `20261106.d5f0724` (read 2026-11-06); the 0.17 W figure was measured on `20260928.410bcf2`.
- If the user applies a newer daily build first, baseline on that one and name it.

B3 has its first data point: pinned Performance costs ~10 °C and half the fan for no FPS gain. Upstream reports for LO: L-29.

**Current phase:** B4 Battery + sleep (L-25) (the statusline parses this line)

**Build status:** working
- `tools/check-delta.sh` OK and secret scan clean, 2026-11-02 23:58 (35 delta files). This session changed docs only.
- Games on the Odin: LostOdysseyRecomp v1.1.0 aarch64 (FSR 3.1, local audio-queue patch, native DXC) — user plays it at the 30 cap and reports it fine (2026-11-02); per-mode cost and `starved=` unmeasured. FF Resonance with the 4x sprite mod v1.0.5 (installed 2026-11-06, not yet checked in game; v1.0.4 was reported fine on 2026-11-03).

**Remote:**
- `odin3-tuning` was rebased onto `upstream/main` = `410bcf2` on 2026-09-28. `upstream/main` = `d4f6880` is **355 commits ahead** (2026-11-02); rebase at a quiet point.
- `main` = `origin/main` (mirror, untouched).
- **Other machine: `git fetch && git reset --hard origin/odin3-tuning`, not `git pull`.**

---

## Device

- **IP `192.168.1.189`** (DHCP moved it from `.188`; `odin.py` default updated). To find it again, scan the LAN for port 22 / Atheros OUI `00-03-7f` (`docs/DEVICE.md` → Access).
- **Image `20261106.d5f0724`** (`armada:testing`, kernel 7.2.6), updated by the user via Steam; rollback `20261106.931dd27`, nothing staged (`bootc status`, 2026-11-06). The daily "Apply" is a new `testing` build each day, not a failed apply.
  - Steam client is on Beta (`publicbeta`, 2026-10-29 build) via "Preview".
  - Known cosmetic QAM dropdown shift (upstream #802); the user keeps it.
- **Bootloader: OpenABL 1.2** since 2026-10-25 (Armada auto-update). The recovery ladder is unverified on it (L-30).
- **Overlay v3** = repo: only `99-armada-hide-internal-ufs.rules` (still present 2026-11-01). `/etc/systemd/system-sleep/` is empty.
- **Sleep:** 43 mA ≈ 0.17 W (60 min, Eco, 80 %), measured on the **previous** image `20260928.410bcf2`.
- **Lost Odyssey Recomp** is installed in `~/Games/LostOdysseyRecomp/`, with game data, saves and settings beside the program.
  - The binary includes FSR 3.1 and the local audio-queue patch. Re-apply `~/src/lo-logs/lo-audio-queue.patch` after any update.
  - Build tree `~/src/LostOdysseyRecomp`; DXC in `~/src/DirectXShaderCompiler` + `~/src/dxc-build`; container `lo-build`; ISOs on the SD card.
  - Revert: `docs/LOST_ODYSSEY.md`. Nothing in `/etc`, no services.
- **LocalSend 1.18.2** (Flathub `org.localsend.localsend_app`, aarch64, system install, 2026-11-01).
  - User override `--filesystem=~/Games`; the sandbox otherwise sees only Downloads.
  - firewalld is inactive (port 53317 open).
  - The save-sync choice is open: the user now leans toward Syncthing (ROADMAP backlog), so LocalSend may go.
  - Revert: `flatpak override --user --reset org.localsend.localsend_app; sudo flatpak uninstall org.localsend.localsend_app; sudo flatpak uninstall --unused`.
- **Final Fantasy Resonance** (Steam 3259780, build 24250053, internal storage, Proton) carries the mod **FFRS HD Sprite Remaster 4x v1.0.5** (Nexus mod 191, by Pompoko). v1.0.3 went in on 2026-11-02 (2x first, then replaced by 4x at the user's request). It was overwritten by v1.0.4 on 2026-11-03 and by v1.0.5 on 2026-11-06: same file names, and the README says to overwrite.
  - The 3 files `FFRS_HD4x_5_P.{pak,ucas,utoc}` (23.4 GB) sit in `…/common/FINAL FANTASY RESONANCE/FFRS/Content/Paks/` beside the stock paks.
  - Tested by its author on build 24250053. A game update may break it; re-check after one. Never install the 2x edition next to it.
  - 4x textures load more VRAM/RAM than 2x; if the game stutters or the fan rises, re-download the 2x edition. The user deleted the 2x zips on 2026-11-03; the 4x v1.0.4 and v1.0.5 zips are in the PC's Downloads.
  - Update recipe (2026-11-03): scp the zip to a staging folder on the same btrfs mount (`steamapps/ffrs-104/`), unzip there (CRC-checked), check the game isn't running, `mv` the 3 files over the old ones, and delete the staging folder. Hold a root `systemd-run --unit=ffrs-inhibit systemd-inhibit …` for the duration. `df` reads ~24 GB high until a `btrfs filesystem sync`; that is lazy freeing, not a leak.
  - Revert: delete those 3 files. Nothing in `/etc`, no services.
- **Cemu** (Armada Store AppImage `~/Applications/Cemu.AppImage`, pkgforge-dev nightly, SDL3, has the AArch64 recompiler; store-made Steam shortcut "Cemu") configured 2026-11-17; the user has run it and, after the audio fix below, hears sound:
  - ROM: `~/ROMs/wiiu/The Legend of Zelda - The Wind Waker HD.wua` (USA, title `0005000010143500` v0, no update). That is also ES-DE's default ROM path; ES-DE is installed but has never been run.
  - `~/.config/Cemu/settings.xml` (hand-written, so the first-run wizard is skipped): Vulkan, async shaders, fullscreen, game path above, no update check, no Discord, no Feral gamemode. Cemu ran once (12:26) and rewrote the file with every key.
  - Graphic packs: community release `Github991` ("Cemu Graphic Packs: v991", 180 packs) unpacked into `~/.local/share/Cemu/graphicPacks/downloadedGraphicPacks/` with `version.txt`, the same layout as Cemu's in-app downloader. Only `WindWakerHD_Resolution` is enabled, preset `1920x1080 (Default)` = the panel's resolution (user's ask, 2026-11-17). Revert: `~/.config/Cemu/settings.xml.pre-1080p`, or set `<GraphicPack/>` again.
  - 60 fps: not possible in Cemu (game locked to 30, no community pack). The native port [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp) has interpolated 60 fps and a linux-aarch64 AppImage. Offered on 2026-11-17; the user chose Cemu at 30 fps. Don't re-pitch unless asked.
  - Controller: `controllerProfiles/controller0.xml` = GamePad (global default), `Odin3-Pro.xml` = Pro Controller. Both are Cemu's own generic SDL default mapping (positional: the right face button is Wii U A), bound to uuid `0_030079f6de280000ff11000001000000`. That is the SDL3 GUID of Steam's "Steam Virtual Gamepad" (evdev `Microsoft X-Box 360 pad 0`, 28de:11ff), which SDL shows only with `SDL_GAMECONTROLLER_ALLOW_STEAM_VIRTUAL_GAMEPAD=1` (Steam sets it). InputPlumber exposes the Odin pad as a "Generic Steam Controller" (28de:12f0).
  - `gameProfiles/0005000010143500.ini`: `controller1 = Odin3-Pro`. The game supports the Pro Controller (manual), which puts the Item and Map screens on the main screen. Cemu's shipped profile for this title is empty, so nothing is lost.
  - Steam shortcut "The Legend of Zelda: The Wind Waker HD" (appid 3116933788), added via `SteamClient.Apps.AddShortcut` over the CEF debugger (127.0.0.1:8080), the same call Armada Store makes. Launch options `/usr/libexec/armada/armada-game-launch %command% -f -g "<rom>"`.
  - Audio fix (2026-11-17, user-verified "it works"): the hand-written/rewritten `settings.xml` had `<Audio><api>0</api>` (DirectSound, absent on Linux) and an empty `<TVDevice>`, so Cemu opened no stream. Now `<api>3</api>` (Cubeb → PipeWire) and `<TVDevice>default</TVDevice>`; TV volume is Cemu's 20, the speaker sink 0.15. Revert: `~/.config/Cemu/settings.xml.pre-audio` (api only) or `.pre-tvdevice`. Edit the file only while Cemu is closed; it rewrites it on exit.
  - No savestates in Cemu (not a feature); the game's own save is the only one. The menu bar needs a mouse, so changes go through `settings.xml` from here; a Steam Input stick-as-mouse layout is the offered fallback, not built.
  - Revert: remove the shortcut in Steam, then `rm -rf ~/.config/Cemu ~/ROMs/wiiu`. After a first run, also `~/.local/share/Cemu` (mlc01, saves) and `~/.cache/Cemu` (shaders). Nothing in `/etc`, no services.
- Test scripts remain in `/var/tmp`: `sleep60.sh` is tagged `-60min-newkernel-nohook`; edit the tag per run.

## Active blockers

None. Device/repo parity: overlay v3 on both (checked 2026-11-01).

## Open loops

L-25, L-30 (OpenABL recovery ladder), L-29 (upstream reports, game), L-22 (parked), L-28 (template resync, user's call), L-3, L-4, L-5, L-6, L-13, L-15, L-16 — see `docs/SESSION_LEDGER.md`.

## Owner rules and measurement notes

- Performance overlay off outside games; quit the game before sleeping. After a battery sleep longer than 15 min, expect to press the power button twice (L-22).
- **30 fps cap for games on the Odin** (user, 2026-11-01): uncapped, the fan gets loud. Fan noise is a hard constraint.
- **Drain figures** need ≥ 60 min by `charge_counter` (`/var/tmp/sleep60.sh`).
  - The device re-suspends on the alarm wake (L-22), so key-wake it afterwards.
  - Launch detached: `odin.py sudo "bash -c 'setsid nohup bash /var/tmp/x.sh >/dev/null 2>&1 </dev/null &'"`.
  - Wrap SSH in `timeout`; it hangs when the device suspends under it.
- **No background polling loops from the PC.** Windows Terminal crashed twice (2026-11-01) while PC-side SSH watcher loops ran; the cause is unproven. Detach long jobs on the device with a log and check on demand. The fan dropping is the user's "done" signal.
- The device falls asleep a few minutes after the user stops touching it. Ask them to keep it awake before any SSH read sequence, or hold a temporary `systemd-inhibit` as root for long jobs and release it after.
- `odin.py push` never deletes a dropped overlay file — remove it on the device by hand.
- The % gauge is unreliable above ~90 %. From Git Bash, `odin.py put`/`get` need `MSYS_NO_PATHCONV=1`, and then the local path must be Windows-style (`C:/…`), not `/c/…`.
- `odin.py put` is text-only. Binaries go by plain `scp` with the `SSH_OPTS` from `odin.py` (~90 MB/s on the LAN, 2026-11-02); unpack archives on the device.
- "Is the game running" guards match the game's `.exe` (`pgrep -af 'FFRS[^ ]*\.exe'`), never a bare title token that a helper's command line can carry.
- OS updates: the user applies Preview builds at their own pace, not daily. What a build changes = `git log <booted-hash>..<offered-hash>` on `upstream/main` (the hash is the version suffix).
- The SD card is ext4 (Armada game storage), mounted at `/run/media/armada/SD`. If the Android side offers to format it, decline — the Steam library lives there.
