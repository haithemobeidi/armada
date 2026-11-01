# Lost Odyssey Recomp — native ARM64 build on the Odin 3

> Side project, outside the B0–B10 blocks. Researched and decided 2026-11-01; **built, imported and added to Steam on the device the same day** (see "Build log" below). Open: the first-play report (Pause C).

**What it is.** [freefrank/LostOdysseyRecomp](https://github.com/freefrank/LostOdysseyRecomp) is a static recompilation of the Xbox 360 game into a native program (GPL-3.0, no game assets). The latest release is **v1.1.0** (2026-10-26). The repo is very active: it was last pushed 2026-10-31, so check for a newer tag on the day.

**The decision.** Build it **natively on the Odin, inside a Fedora 44 distrobox, without FEX.** The user chose this over building on the PC (2026-11-01).

---

## Why a source build

Each release has five packages: `windows-x64` zip, `linux-x64` AppImage, `linux-x64` Flatpak, `macos-arm64` dmg and `android-arm64` apk. **None of them is Linux ARM64.**

| Route | Verdict |
|---|---|
| APK on the Android side | Rejected. The four discs come to ~20 GB extracted, more than the 16 GiB `userdata`. The SD card is ext4 for Armada, which Android can't read. **Never let Android format the SD card** — it holds the Steam library. |
| `linux-x64` AppImage under FEX | Works in principle (Armada registers FEX binfmt for x86-64), but every guest instruction gets translated twice, which costs FPS and battery. Kept as the fallback. |
| APK in Waydroid | Armada ships Waydroid and stages its Android Mesa (Turnip) into Waydroid's vendor overlay **for SM8750 only** (`system_files/usr/libexec/armada/waydroid-mesa-overlay`). Untested with this game. Second fallback. |
| Cross-build on the PC (WSL2 Ubuntu) | The route upstream documents. The PC (Ryzen 9 9950X3D, 16C/32T, 94 GB) compiles much faster, but it needs more setup plus a glibc/libcurl parity check against Fedora. Not chosen. |
| **Native build on the Odin** | **Chosen.** No cross sysroot, no split DXC build, and the container's Fedora 44 matches Armada's base (`Containerfile`: `fedora-bootc:44`), so the binary runs on the host and goes into Steam. |

**Upstream ARM64 status.** PR #60 (merged 2026-10-02) added an experimental Linux AArch64 path: `docs/LINUX_ARM64.md`, `tools/build_linux_arm64.sh` and `cmake/toolchains/linux-aarch64.cmake`. It was exercised on a ROCKNIX-style target. PR #165 says it "ships as is, without an ARM64 hardware validation gate". PR #246 (2026-10-06) moved ARM64 packaging past v1.0.0 into the later backlog. Since then nothing has touched it through v1.1.0 (v1.0.0 shipped 2026-10-17). Upstream's script is an **x86-64 Ubuntu cross-build**: its toolchain file hardcodes `/usr/aarch64-linux-gnu` and `--gcc-toolchain=/usr`. **We bypass it** and run the normal Linux configure natively with `-DLO_TARGET_ARCH=armv8-a`, the flag the ARM64 script passes. Nobody upstream has tried this exact path.

## Inputs

- **Discs:** `C:\Users\haith\OneDrive\Desktop\LO\` holds 4 ISOs, `Lost Odyssey (USA, Europe) (En,Ja,Fr,De,Es,It) (Disc N).iso`, 7,835,492,352 bytes each, **29.2 GB** in total. They are stored locally, not OneDrive cloud placeholders (attributes `Archive` only, checked 2026-11-01).
- **Edition: USA/Europe is supported.** Per upstream `docs/notes/xex.md`, the USA/Europe disc 1 decrypts **byte for byte** to the same image as the Asian disc 1 the code is generated from, so our `default.xex` works as the build input. There is no hash gate: `ppc_codegen.py` checks no hash, and `tools/release/fetch_build_input.py` is CI-only. Don't mix editions at import.
- **Build input = disc 1's `default.xex` only.** CI sparse-checks out just that one file. It goes to `LostOdysseyRecompLib/private/disc1/default.xex`.

## Device facts that matter here

- Fedora 44 bootc. `distrobox` and `podman` are in the image (`build_files/10-base-packages.sh`).
- 16 GB RAM plus zram 14.6 GB. Root is a 418 GB btrfs (home and container storage live here). SD card: 1 TB ext4 at `/run/media/SD`.
- SSH: `armada@192.168.1.189` (DHCP; the IP has moved before). `odin.py` uses OpenSSH, so plain `scp` works. From Git Bash, put `MSYS_NO_PATHCONV=1` in front.
- Keep it **plugged in and awake**: it sleeps a few minutes after the last touch, and SSH hangs under a suspend.

## Time — measured upstream, estimated here

- **Measured (GitHub `ubuntu-22.04` runners, 4 vCPU, `-j4`):** cold compile (ccache 0 % hits) took 17:33, 17:55 and 18:04. Warm (68 % hits) took about 3 min. The build has 1,412 ninja steps, including 246 generated `ppc_recomp.*.cpp` files. Recompiler tools build in about 10–20 s, and code generation takes about 10 s.
- **Estimated for the Odin (not measured):** 8 Oryon cores (2 × 4.32 + 6 × 3.53 GHz), but likely fewer parallel jobs to fit RAM, plus thermal throttling. Estimates per step:

| Step | Estimate |
|---|---|
| Container + packages | 5–10 min (Wi-Fi) |
| Clone + submodules | a few min |
| Recompiler tools + codegen | a few min |
| **Game compile** | **10–30 min** |
| ARM64 DXC (optional) | 20–40 min |
| Copy 29.2 GB of ISOs over Wi-Fi | 10–30 min (can run during the build) |

- The compile runs under whatever power profile is active. A capped profile makes it slower. The profile is the user's choice. Expect the fan to be loud.

## Plan

Pause-points follow `CLAUDE.md` § Device work. **Pause A**: tools and codegen done, before the long compile. **Pause B**: binary built, before the first launch (announce first — Steam may be open). **Pause C**: after the first play, to record observations.

1. **Copy the ISOs** to `/run/media/SD/LostOdyssey/iso/`. Use `scp` with `odin.py`'s options (`-o StrictHostKeyChecking=accept-new -o BatchMode=yes`) from Git Bash. Use OpenSSH, not paramiko, because paramiko is much slower. Start this first and let it run in parallel.
2. **Container:** `distrobox create --name lo-build --image registry.fedoraproject.org/fedora-toolbox:44`, then install the packages inside it. The list below is mapped from release.yml's Ubuntu list to Fedora names and is **unverified**:
   `clang lld cmake ninja-build python3 git pkgconf-pkg-config libcurl-devel vulkan-loader-devel vulkan-headers libX11-devel libXext-devel libXrandr-devel libXcursor-devel libXi-devel libXfixes-devel libXScrnSaver-devel libXtst-devel alsa-lib-devel pulseaudio-libs-devel pipewire-devel wayland-devel libxkbcommon-devel libglvnd-devel libdecor-devel dbus-devel systemd-devel gcc make`
3. **Source:** `git clone --recursive --branch v1.1.0 https://github.com/freefrank/LostOdysseyRecomp ~/src/LostOdysseyRecomp`. Apply the patches exactly as CI does, each one only if it isn't already applied (`git apply --reverse --check … || git apply …`):
   - `tools/XenonRecomp` ← `../patches/XenonRecomp-lostodyssey.patch`
   - `thirdparty/plume` ← `../../tools/patches/plume-lostodyssey.patch`
   - `thirdparty/plume` ← `../../tools/patches/plume-sdl3.patch`
4. **Get `default.xex`:** build [extract-xiso](https://github.com/XboxDev/extract-xiso) in the container, extract the disc 1 ISO to a temp folder, copy `default.xex` into `LostOdysseyRecompLib/private/disc1/`, then delete the temp folder. *Fallback:* the official Windows zip on the PC imports an ISO into `game/disc1/`, and its `default.xex` can be copied over.
5. **Tools + codegen** (CI's commands, with `clang-18` changed to `clang`):
   ```
   cmake -S tools/xexdump -B out/build/tools -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++
   cmake --build out/build/tools --target XenonRecomp XenonAnalyse xexdump
   out/build/tools/xexdump LostOdysseyRecompLib/private/disc1/default.xex LostOdysseyRecompLib/private/image_disc1.bin
   python3 tools/ppc_codegen.py generate --executable out/build/tools/XenonRecomp/XenonRecomp/XenonRecomp
   ```
   → **Pause A.**
6. **Configure + compile** natively. Skip DLSS/FSR, and skip the ARM64 DXC for now:
   ```
   cmake -S . -B out/build/linux-arm64 -G Ninja -DCMAKE_BUILD_TYPE=Release \
     -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
     -DLO_TARGET_ARCH=armv8-a -DSDL_PIPEWIRE=ON -DSDL_PIPEWIRE_SHARED=ON
   cmake --build out/build/linux-arm64 --target LostOdysseyRecomp -j 4   # raise if RAM allows
   ```
   Output: `out/build/linux-arm64/LostOdysseyRecomp/LostOdysseyRecomp`.
7. **Check on the host** (outside the container): `ldd` on the binary should show no `not found`.
8. **First launch** → **Pause B, announce first.** Run with `LO_NO_UPDATE=1` and turn off **Automatic updates** in Settings. The updater "can update itself" on the AppImage, and it must never swap our ARM64 binary for the x64 one. The importer opens: point it at the ISOs on the SD card (it checks each disc's SHA256). By default it imports to `~/.local/share/lost-odyssey-recomp/game/` on internal storage, which has plenty of room. Accept the shader-pack download. Then use Settings → System → **Add to Steam** (or `--add-to-steam` with Steam closed) to put it in Gaming Mode.
9. **Observe** → **Pause C.** In-game performance overlay FPS at a 30 and a 60 cap, PWM and temperature from `odin.py`, and the user's reports of noise and warmth. Battery drain only on a later, separate run. Note that the game caps Fast loading on battery devices.

## Build log (2026-11-01)

- v1.1.0 = commit `fcfda13` (annotated tag). Container + 32 packages in < 1 min (clang 22.1.8, CMake 4.3, Ninja 1.13); all four ISOs on the SD card at `/run/media/armada/SD/LostOdyssey/iso/` (the mount is `/run/media/armada/SD`, not `/run/media/SD`), ~100 MB/s over Wi-Fi.
- The distrobox does **not** share the host's `/var/tmp`; scripts and logs live in `~/src/lo-logs/`.
- `default.xex` from disc 1 via extract-xiso: 6,623,232 bytes, sha256 `175ae53d…640de3`. Codegen: "PPC generation: OK", 246 `ppc_recomp.*.cpp`.
- **Configure fails without a `linux-aarch64` FFmpeg config** (`thirdparty/ffmpeg.cmake`: "No FFmpeg config for linux-aarch64"); upstream ships only `android-aarch64` and `macos-aarch64`, and `docs/LINUX_ARM64.md` does not mention it, so upstream's own ARM64 path is broken at v1.1.0. Fix, per upstream's `ffmpeg-config/android-aarch64/README.md` recipe: in a throwaway copy of the pinned fork (`15ece08`), `mv config.h config.h.fork` and `./configure --cc=clang --arch=aarch64 --target-os=linux --disable-everything --disable-programs --disable-all --disable-autodetect --enable-avcodec --enable-avutil --enable-decoder=xmaframes`, then copy `config.h` to `thirdparty/ffmpeg-config/linux-aarch64/`. Script: `~/src/lo-logs/lo-ffmpeg-cfg.sh`. **Upstreamable** as a one-file PR. Re-run it after any update that moves the FFmpeg pin.
- Configure is silent about the missing ARM64 DXC.
- **Compile: 263 s** at `-j 4` on the Performance profile (1,390 ninja steps; estimate was 10–30 min). Fan PWM 255; CPU zones 85–94 °C, throttled at the 90/95 °C passive trips (hot/critical 120/125 °C) to ~2.7 GHz; battery 32 °C. Output: 97 MB aarch64 ELF, `ldd` resolves all 35 libraries on the host.
- Windows Terminal crashed twice on the PC during this session (XAML `0xc000027b`) while PC-side background SSH polling loops ran; cause not proven. Don't poll the device from background loops; check on demand.
- **Installed to `~/Games/LostOdysseyRecomp/`** (the binary + `assets/`, 1.1 MB, is all the AppImage ships besides DXC). A self-built Linux copy keeps `game/`, `save/`, `settings.ini`, `shaders/` **beside the program**, so it must not live in `out/build/` (a clean rebuild would take the saves). Updating = rebuild, then copy the binary over.
- **Import:** `--install-source` is Android-only (ignored on Linux); the importer is a gamepad/keyboard file browser starting at the program folder (Enter open, F select, Esc back). In Desktop Mode the built-in controller does **not** reach it — use a keyboard. Its folder scan **skips symlinks**, so a symlink to the SD folder finds nothing ("no supported discs"); a bind mount works (`sudo mount --bind /run/media/armada/SD/LostOdyssey/iso ~/Games/LostOdysseyRecomp/discs`, removed afterwards). Result: 4 discs, 22 GiB apparent; the offered "free disk space" dedups 27 archives with btrfs reflinks (`btrfs filesystem du`: 14.3 GiB exclusive + 1.8 GiB shared ≈ 16 GiB on disk; plain `du` can't see it). It re-offers the same 5.78 GB on every launch: `EstimateCompactGameDataBytes` counts a copy as shared only by inode (`equivalent()` / `hard_link_count`), so reflinked copies always look like duplicates — harmless. Answer **"Don't ask again"** (writes `ask_compact_game_data=0`; or set it in `settings.ini` with the game closed).
- **ARM64 DXC is required, not optional.** The portable shader pack (235 MB `portable_vk.lospv`) downloads fine, but the presentation shaders compile live at startup; without `libdxcompiler.so` beside the binary graphics init fails ("no usable backend; guest startup aborted") and the game exits cleanly. Fedora 44 has no DXC package. Built natively at upstream's revision `9efbb6c` with the target half of `tools/build_dxc_linux_arm64.sh` (same flags, clang, no cross toolchain, needs `clang-tools-extra` for `clang-format`, plus upstream's RewriteObjC source patch): **287 s** at `-j 4`, HLSL→SPIR-V smoke test passed, 31.5 MB, sha256 `7b2ec4d7…a000aa6`. Script `~/src/lo-logs/lo-dxc.sh`. Also staged at `tools/XenosRecomp/thirdparty/dxc-bin/lib/arm64/` so CMake copies it on future builds.
- **First boot:** Vulkan on Adreno 830 (Turnip), intro movie and audio play. Defaults: 1280×720 output, 720 internal, 30 fps cap, vsync on. **Add to Steam** (in-game, Settings → System) wrote a non-Steam shortcut (`Lost Odyssey Recomp`, Exe = our binary, StartDir = the game folder, artwork from the player's discs); Steam was not running in Desktop Mode.
- **In a Desktop Mode window the Settings page's bottom (its save control) is cut off** and Esc/Backspace may not leave it; the user found the save control by scrolling, and `settings.ini` then read `automatic_updates=0` (13:47:55). Closing the window afterwards is safe. Change settings in Gaming Mode (fullscreen, controller works).
- **Settings save only when you leave the Settings page.** `automatic_updates=0` also stops shader-pack auto-downloads (pack already present). FSR/DLSS/XeSS are compiled out (`LO_ENABLE_FSR` defaults OFF; upstream CI enables it with a locally prepared FidelityFX SDK) — use TAA.

## First play (Pause C), 2026-11-01, Gaming Mode, plugged in at 100 %

Same scene, LO settings `internal_resolution=1080`, `frame_rate=120`, vsync on. FPS from the user (Steam overlay); the rest read over SSH (`armada-power status`, sysfs).

| Profile | FPS (user) | GPU | CPU | SoC temp | Fan PWM | Battery |
|---|---|---|---|---|---|---|
| Performance, factory (pinned: `performance` governor, GPU min = max) | ~30 | 1100 MHz (pinned) | all cores at max; 84 % idle; game main thread ≈ 0.8 core | 89–91 °C (hottest = CPU zones) | 224–249 | 32 °C |
| Balanced, the user's (`cpu_underclock=large`, `cpu_max=0.65`, `gpu_max=0.80`) | **< 30** | 832 MHz (capped) | capped 1785 / 1958 MHz | 54–59 °C | 195 → 75 | — |
| Performance, unpinned (`schedutil`, `gpu_min_mhz=160`, no underclock) | ~30 | **1100 MHz chosen by the governor** | E-cores 3.0–3.5 GHz, prime ~1.0–1.2 GHz; 75 % idle | 82 → 77 °C | ~100 | 33 °C |

- **The GPU is the limit at 1080p internal**: unpinned, it still picks its 1100 MHz top. The CPU is not (mostly idle; native code, no FEX). Balanced's ~half CPU clocks starve the main game thread, hence < 30.
- **Pinning bought nothing**: the same FPS unpinned, with the fan at less than half and 10+ °C cooler. User reports: fan "like a jet engine" when pinned.
- Why a "360 game" is heavy here: the recomp makes the PowerPC CPU code native, but the Xenos GPU (draws, shaders, EDRAM) is still translated every frame to Vulkan on Turnip, and 1080p internal is 2.25× the 360's 720p.
- Next (L-31): internal 720 on the unpinned profile; if FPS rises clearly, build FSR (`LO_ENABLE_FSR`, FidelityFX SDK + Vulkan shaders) to upscale 720 → 1080.
- **Internal 720, unpinned Performance, open area (14:20): ~40 FPS (user), GPU 967 MHz, 70 °C, fan PWM 207 (user: "fans at 100").** GPU-bound confirmed → FSR worth building (L-31). The fan noise is the uncapped frame rate (`frame_rate=120` lets the GPU run flat out) plus the `aggressive` curve (85 °C → 204) and its slow ramp-down; a 30 cap (the 360's rate) is the quiet option.
- **Audio choppy: the SDL output queue ran dry ~47×/s** (`audio frames submitted … starved=` +~470 per 10 s, `clock_resets` +2–4) on every profile. `apu/audio.cpp` queues 4 frames (~21 ms) on desktop and 8 (~43 ms) on Android "because a phone's thermally capped CPU can run the driver thread tens of milliseconds late". Local patch: `#if LO_PLATFORM_ANDROID || defined(__aarch64__)` (saved as `~/src/lo-logs/lo-audio-queue.patch`; re-apply after any update). Incremental rebuild 33 s; installed by `cp` + `mv` (new inode, so the running game was not disturbed). Effect not yet measured — check `starved=` after the next launch. Upstreamable (L-29).

## Risks and open questions

- **Native path untested upstream.** We bypass `build_linux_arm64.sh`. Unknown: does `cmake/LoOptimization.cmake` add x86 flags on aarch64 if `LO_TARGET_ARCH` is missing? (We pass it.)
- **No ARM64 DXC.** CMake looks for `lib/arm64/libdxcompiler.so`, and it's unknown whether configure fails or warns without it. Without it, any shader missing from the downloaded portable pack (CPU-independent per `LINUX_ARM64.md`) shows up as a missing visual. The fix is to build DXC natively at revision `9efbb6c3242cbb40c1844a2589171ff1c27cf956` (upstream's tested revision) and stage it next to the binary, or point `LO_DXC_PATH` at it.
- Does the first-start shader download offer a pack to a self-built Linux ARM64 binary?
- **RAM:** 16 GB. Generated files can be heavy per clang process, so start at `-j 4`.
- **GPU:** Adreno 830 on desktop Mesa Turnip is unproven for this game. Upstream fixed Adreno 650 Turnip hangs on Android (#571).
- **Updates:** a new upstream version means `git fetch`, check out the new tag, re-apply the patches if the submodules moved, regenerate, rebuild (warm build is faster). Never use the in-game updater.

## Revert

Nothing touches `/etc`, services or the boot path. Everything lives under `/var/home/armada`:

- `distrobox rm lo-build` (podman storage under `~/.local/share/containers`)
- `rm -rf ~/src/LostOdysseyRecomp ~/src/DirectXShaderCompiler ~/src/dxc-build ~/src/extract-xiso ~/src/lo-logs`
- `rm -rf ~/Games/LostOdysseyRecomp` — **its `save/` holds the saves**; back it up first if you want to keep them
- `/var/tmp/lo-setup.sh`, `/var/tmp/lo-setup.log` (host)
- `rm -rf /run/media/SD/LostOdyssey`
- Remove the Steam shortcut.

## Sources

- Releases and API listing: <https://github.com/freefrank/LostOdysseyRecomp/releases>
- Build guides: `docs/BUILDING.md`, `docs/LINUX_ARM64.md`, `docs/INSTALLING.md`, `docs/notes/xex.md` in the upstream repo
- CI: `.github/workflows/release.yml` (Linux job). Cold-build timings from release runs 39067975899, 39065590367 and 36668147844.
- PRs #60, #165, #246; issue #571
