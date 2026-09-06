# armada-odin3 — Handoff Log

Append-only one-line history of every development session. Newest entries at the bottom.

**Format:** `YYYY-MM-DD HH:MM | <Block name> | <one-line summary incl. "Next:"> | <build status>`

Summary field hard cap ~300 chars. Fact-grade detail lives in `SESSION_LEDGER.md` and `CURRENT_STATE.md`. Post-/end mini-wrap lines cover ONLY the delta since the previous line.

---

<!-- Entries appended by /end. Never edit past rows. -->
2026-09-05 03:05 | B0 Protocol + device access | Ported Checkpoint/KB protocol for a fork with a device (guards on main, 2-remote sync, delta-scoped index, device-state record); SSH + tools/odin.py; DEVICE.md + ARMADA_CONTROL.md from live device (no fan tach, Fans tab owns curves); rebased onto 14230df; first user obs recorded. Next: fresh-session hook check (L-2), then B1 logger. | working
2026-09-06 14:03 | B8 Storage decision | B0 closed (L-2 hook verified). Android-side detour: GameNative/ZENONIA 1 cloud save fixed (game hotfix moved the save folder; update + Keep local), KB article written. D-9: internal install decided, Android 16 GiB, go given, NOT run yet (root still mmcblk0p3). Next: L-7 run installer, L-8 verify + DEVICE.md, L-9 rebase (14 behind), then B1. | working
2026-09-06 14:45 | B8 Storage decision (mini-wrap) | User ran the internal install (16 GiB) right after /end; verified root=sda20, image 20260906.41d2e10; SSH re-enabled + key reinstalled (fresh deployment drops /etc+/var); SD card reformatted ext4 via format-sdcard.sh (automount is ext4-only), shows at /run/media/mmcblk0p1; DEVICE.md rewritten; B8 closed, B1 current. Next: L-9 rebase, L-11 re-pull device-state, then B1 logger. | working
