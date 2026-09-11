# armada-odin3 — Decisions

Append-only log of decisions that shape how this fork is worked on. Each entry: what was decided, why, and what would make us revisit it. Newest at the bottom. IDs are frozen.

---

## D-1 — Fork layout: `main` mirrors upstream, work lives on `odin3-tuning` (2026-09-04)

`origin` = `github.com/haithemobeidi/armada` (public — required for free ARM64 CI runners). `upstream` = `github.com/armada-os/armada`, fetch-only; its push URL is set to `DISABLED_use_origin` as a guard. `main` tracks `upstream/main` and never receives commits, so a clean upstream is always one `git switch main` away for cutting PR branches. GitHub Actions are disabled on the fork until we deliberately need a build.

**Revisit if:** we start maintaining more than one device or more than one long-lived tuning branch.

## D-2 — Keep `odin3-tuning` current by REBASE, pushed with `--force-with-lease` (2026-09-05)

**Decision:** periodically `git rebase upstream/main` on `odin3-tuning`, then `git push --force-with-lease origin odin3-tuning`. `git rerere` is enabled in the repo config so a conflict resolved once is replayed automatically. Rebasing is a **user-approved action at a quiet point in a session** — never automatic, never during `/start` or `/end`.

**Why rebase over merge:**

| | Merge upstream into our branch | Rebase our branch onto upstream |
|---|---|---|
| Push | Plain push, no history rewrite | Requires `--force-with-lease` to our own branch |
| History | Our ~dozen changes buried among hundreds of upstream commits and merge commits | Our changes always sit on top; `git log upstream/main..odin3-tuning` is exactly the delta |
| PR prep | Archaeology: dig our commits out of the merges | Cherry-pick from the top of the stack |
| Conflicts | Resolved once per merge | Same conflict can recur per rebase — `rerere` remembers the resolution |
| Second machine | `git pull` works | Must `git fetch && git reset --hard origin/odin3-tuning`; the SessionStart hook detects the "diverged" state and stops |

Upstream lands several merges a day, so the merge path would make our delta unreadable within weeks. The fork's branch has a single author, which is what makes force-with-lease safe: the lease fails if anyone else pushed.

**Amended 2026-09-05 (same day):** the user delegated repo mechanics outright — "whatever you think for the repo … I'm not a developer … go with what works best for our use case." Rebases are therefore **Claude's call at a quiet point**: clean tree, never inside `/start` or `/end`, never leaving a conflict half-resolved, and **always reported** in the status line and the handoff. `--force-with-lease` to `origin/odin3-tuning` right after a rebase remains the only permitted force push. Anything touching the device's boot path is unaffected by this delegation (D-7 still requires a per-instance go). First rebase under this rule: 2026-09-05, `33e0319 → 14230df`, five commits replayed, no conflicts.

**Revisit if:** a second person starts committing to `odin3-tuning`.

## D-3 — Session-end pushes are pre-authorized (2026-09-05)

The user pre-authorized `git push` to `origin/odin3-tuning` as part of `/end` and post-`/end` mini-wraps, so work continues from the other machine without ceremony. Covers plain pushes only. **The only sanctioned force is the post-rebase `--force-with-lease` in D-2**, and that still needs a per-instance go. A rejected push is reported, never retried destructively.

## D-4 — `/etc` overlay first; image rebuild last (2026-09-05)

Every tuning change is applied through the handheld's writable `/etc` (survives OTA on bootc) before anything is baked into the image. `/etc` changes are text edits to undo; an image change is a reflash. Rebuilding the image gets its own block on the roadmap and happens only when a set of overlay values has been stable for a while.

**Config ownership — two kinds of files.** Armada Control's UI writes to `/etc/armada/` through its privileged helper, and it owns more than first assumed. Reading the plugin source: `power.py` → `render_power` owns `[general] default_profile` and the six editable keys per `[profile.*]` (`cpu_governor`, `cpu_max`, `cpu_underclock`, `gpu_max`, `gpu_min`, `fan_curve`); `fan_curves.py` → `render_all` (the **Fans tab**, a full curve editor) owns every `[fan_curve.*]` section plus `[fan]`'s `ramp_up`, `ramp_down`, `smoothing`, and `min_pwm` — and **forces `min_pwm=0` whenever any curve's lowest point is PWM 0** ("fan-stopped"). Both writers preserve keys they don't own. What's left un-owned in that file (`max_pwm`, `pwm_quantum`, `[suspend]`, custom `[underclock.*]` tiers, per-profile `cpu_max_policyN`) is too thin to fight over. So:

- **UI-owned files** (`power-profiles.conf`, `game-tweaks.json`, anything else the plugin writes): tuned **through the UI**, exactly as a user would. The repo keeps a **record**, not a source: `tools/` pulls them into `device-state/` (committed), so every UI-side tuning change lands in git history with a commit message saying why. Never pushed device-ward.
- **Repo-owned files** (anything under `/etc` with no UI writer: sysctl drop-ins, service masks/drop-ins, udev rules, our own scripts and units): live in `device-overlay/`, pushed by `tools/`, never hand-edited on the device.
- **Why tune fans through the UI rather than a file we own:** the upstream editor already implements fan-stop, curve creation, ramp and smoothing edits, and validation — and it will keep working after every rebase. A file we owned would collide with it on the first UI save.

**What an OS update does to our work — the three layers.** (1) The **OS image** on the device is upstream's official build (`ghcr.io/armada-os/armada:testing`); an OTA replaces the read-only `/usr` wholesale and nothing in this repo affects it. (2) The device's **`/etc`** is kept across OTAs by bootc's three-way merge: keys we or the UI changed persist, keys we never touched follow upstream's new defaults. Since the UI writes only edited keys, upstream improvements to everything else flow through automatically. So an update does **not** undo `/etc` tuning. (3) **This repo** is our copy of the recipe. Rebasing keeps the copy current; it changes nothing on the device. It exists for reading the code, recording device state, upstreaming PRs, and — only if `/etc` ever can't express a change — building our own image (B10), at which point the device would switch to *our* registry and take *our* updates (built by CI from upstream + our stack). Even code changes can usually live in `/etc` (a replacement script plus a systemd drop-in overriding `ExecStart`), so B10 stays last. Upstream's commits for other devices are inert on ours (device behaviour is selected at runtime by `device-env`); we never "tear them out".

**Revisit if:** upstream changes what the plugin writes (check `EDITABLE_KEYS` in `power.py` and the ownership comment atop `fan_curves.py` after each rebase), or a tuning knob we need has no UI and no un-owned key.

## D-5 — `docs/CODEBASE_INDEX.md` is scoped to the fork delta (2026-09-05)

Indexing ~500 upstream files would be busywork that rots on every rebase. The PostToolUse hook only queues files we touch, so upstream files we never edit are never indexed; a modified upstream file's entry must say **why we diverged** — which is the seed of its eventual PR description. The index therefore doubles as the list of what this fork changes.

## D-6 — No worktrees; sessions run from a terminal in the main checkout (2026-09-05)

Inherited from earlier projects: Claude Code Desktop force-creates a worktree per session and offers no setting to disable it ([anthropics/claude-code#21236](https://github.com/anthropics/claude-code/issues/21236)). Run `claude` from a terminal in the project root. The branch guard trips on worktrees, `claude/*` branches, and `main`.

## D-7 — Boot path changes need a fresh backup and an explicit go, every time (2026-09-05)

ABL, partitions, kernel args, the boot image, and any "install to internal storage" step are never part of a routine pause. Each gets its own roadmap block, a verified backup step first, and a per-instance go from the user. Backup locations are in `docs/DEVICE.md`. The internal Android install is intact on the UFS (`sda`) and stays that way until a decision says otherwise.

## D-8 — Whole-OS scope, fan noise first, measurement before every change (2026-09-05)

The user's goal is every aspect of the OS tuned for this device and their use, "A to Z, slowly but sure". The roadmap is organised as blocks by subsystem, fan/thermal first because it is the most audible. Every block opens with a baseline measurement; no change ships without the signal it targets having been recorded before and after (`CLAUDE.md` → Project rules → Device work; before 2026-09-11 in `docs/WORK_STYLE.md`).

## D-9 — Install to internal storage; Android kept at 16 GiB (2026-09-06)

The user chose internal storage over the SD card, keeping Android only as a fallback: "I won't use Android, I don't care for it." Grounds: B8's evidence that the SD write path caps Steam downloads at ~60 MB/s (UHS-I slot ceiling), plus the user's stated non-use of Android; this overrides the earlier "stay on SD during tuning" call. The per-instance go D-7 requires was given in this session. It covers exactly one thing: one run of `armada-installer install --userdata-gib 16` (CLI over SSH, or the same choice in the Desktop Mode GUI) with Armada booted from the SD card. Nothing else on the boot path is covered.

**Why 16 GiB.** The installer's floor is 8 GiB (`ANDROID_MIN_MIB`), its GUI default 32 GiB when there is room. 8 boots but leaves nothing once Android's first boot fills its caches and an AYN OTA package stages in `userdata`; 16 removes that worry for 2 % of the disk. Armada needs ~33.6 GiB minimum (512 MiB ESP + 1 GiB boot + 32 GiB root + 64 MiB) and takes everything else.

**What it does.** Deletes and recreates `userdata` at 16 GiB, zeroes its first 8 MiB (Android factory-resets on its next boot: apps and `/sdcard` gone, the Android system partitions kept), creates the three Armada partitions in the freed space, deploys the booted image, and dual-boots. The SD card stays a bootable Armada and is the recovery path until internal boot is verified with the card out. Reverts: `armada-installer reset` from the SD card, or ABL "UNINSTALL CFW & EXPAND USERDATA" — both keep the Android system and factory-reset it again.

**Revisit if:** the internal install fails to boot (stay on SD, run `reset`), or Android is ever wanted for real (reset returns the space).

## D-10 — Protocol migrated to the global Knowledge Base layer (2026-09-11)

**Decision:** the session protocol is no longer copied into this repo. The work style and the session lifecycle are imported live from `<KB>/claude-project-template/global/` via `~/.claude/CLAUDE.md`; `/start` and `/end` are the global commands; the scripts in `.claude/scripts/`, `.claude/settings.json`, and `.claude/agents/` are byte-identical to the template and checked by `check-template-drift.py`. Everything project-specific lives in two places: `CLAUDE.md` (rules, pointers, explicit overrides) and `.claude/protocol.json` (`check_command = bash tools/check-delta.sh`, `push_policy = standing`, the generated-path skip list, default ledger caps, single track).

**What moved where:** `PROTOCOL.md` → the fork model and the device model became Project rules and Overrides in `CLAUDE.md`; `docs/WORK_STYLE.md` → the device-specific line of each rule stayed in `CLAUDE.md`, the transferable part is the global work style; the old `/end` build guard (py_compile, `bash -n`, configparser on every overlay `.conf`) → `tools/check-delta.sh`, which now also runs shellcheck and warns on unindexed delta files; the ledger header → the template's (worthiness test, 600-char cap, 30 open soft max, 45-day stale, 7-day prune). One-time triage at migration: L-13 shortened to the loop + a pointer (its analysis was already in ROADMAP B4).

**What the template does not do that the old copy did — now text rules in `CLAUDE.md` instead of hooks:** the branch guard no longer trips on `main` (the template guards worktrees and `claude/*` only); the start hook fetches only `origin`, so the upstream drift count is a rule Claude runs at start; the statusline no longer shows `upstream +N`; the index hook no longer skips firmware/binary suffixes. Candidate template improvements, to be upstreamed to the KB rather than patched here: `protected_branches` and `upstream_ref` keys in `protocol.json`; `newline="\n"` when the index hook appends to `pending-index-updates.txt` (the old copy had that fix — on Windows the file otherwise gets CRLF, which bit us 2026-09-05). Also: the start hook counts the template ledger header's example lines (inside an HTML comment) as open items — this repo's header carries no examples; the hook should skip comment blocks.

**How to apply:** never edit a template-managed file here; edit `protocol.json` or `CLAUDE.md`, or improve the template in the KB and resync with `check-template-drift.py --sync`. After every KB pull, rerun `install-global.py`.
