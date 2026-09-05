# Work Style — read on demand, not auto-loaded

Long-form work-style rules for this project, extracted from `CLAUDE.md` so the auto-loaded context stays lean. `CLAUDE.md` names the trigger for each rule; read the matching section here when the trigger applies.

- **Before changing anything on the device or in `device-overlay/`** → "Measure before you change".
- **Before starting a sub-phase (any block milestone)** → "Pause at device-observable milestones".
- **Before designing any non-trivial mechanism** → "Don't reinvent the wheel".
- **Any time you push back on or agree with the user** → "Grounded pushback + grounded agreement".
- **Before touching a setting that more than one surface reads or writes** → "One source of truth — data AND behavior".
- **Always** → "Methodical pacing".
- **Before an audit or cleanup pass** → "Audits target real optimization".
- **When something transferable is learned** → "Capture transferable lessons — `*kbdoc`".

---

## Measure before you change

This project tunes a physical device. Every claim about "quieter", "cooler", "longer battery", or "faster" is a measurement claim, and the failure mode is changing a value, hearing what you expect, and moving on.

1. **Baseline first.** Before any tuning change in a block, capture the relevant signals with the change NOT applied: temperatures, fan PWM, CPU/GPU frequencies, battery power draw, whichever the block is about. Raw pulls go in `device-data/` (git-ignored); the summary and the numbers that matter go in the block's section of `ROADMAP.md` or `docs/DEVICE.md`.
2. **One variable at a time.** A change that alters the fan floor AND the ramp AND the curve teaches you nothing when it's better. Ship one, measure, ship the next.
3. **Same conditions.** Compare like with like: same game or same idle screen, same ambient, same charge state (plugged vs battery changes the SoC's thermal envelope). Say what the conditions were.
4. **What the device can't tell you, say so.** This unit's fan has no tachometer: RPM is never readable, so "the fan is at PWM 96" is a fact and "the fan is at 3000 RPM" is a guess. Write the fact.
5. **The user's ears and hands are instruments too.** Perceived noise and perceived warmth are legitimate measurements — record them as "user reports", with the PWM/temperature at that moment, so they can be correlated.

---

## Pause at device-observable milestones

Claude must not apply a stack of changes to the handheld and hand back "try it now". Each change that alters something the user can hear, feel, see, or time is its own pause.

### Mandatory steps

1. **Declare pause-points BEFORE doing any work for a sub-phase.** First message of the sub-phase contains a numbered list under `**Pause-points for this milestone:**`. Each entry is a one-line "observe moment": `Pause A: overlay applied, fan should be silent on the Steam home screen after ~2 minutes; note whether it is`. Default 2–4 per sub-phase.

2. **Triggers that always count**, even if not pre-declared:
   - A new overlay file lands on the device (fan, power, sysctl, service mask, udev rule)
   - A service is enabled, disabled, or masked on the device
   - A measurement script runs for the first time and produces a file
   - Anything that changes the boot path (kernel args, ABL, image)
   - The first time a new profile or per-game tweak is selectable in the UI

3. **STOP-and-handoff after each pause-point** with this exact shape:

   ```
   ## 🛑 Pause N — <name>

   **What changed on the device:** <bullets — file paths / services, and how to revert>
   **What to observe:** <bullets — things the user hears, feels, sees, or times; no terminal>
   **What I haven't done yet:** <bullets>
   ```

   Then wait. Do not continue to the next pause-point until the user reports back or says keep going.

   **"What to observe" is user-doable only.** The user is not going to open a terminal on the device, read sysfs, or run scripts. If backend verification is needed, Claude does it over SSH and reports it in one line. Good items: "is the fan audible on the home screen after two minutes", "does the fan spin up when you launch X", "how warm is the back panel after 15 minutes", "battery percentage at start and after 30 minutes of Y".

4. **Safety net.** If Claude has changed 3+ device-side values or written 300+ lines without a pause, a pause was missed. Stop and hand off.

5. **Every device change carries its revert.** The hand-off block states how to undo it (delete the overlay file and `systemctl restart armada-powerd`, `systemctl unmask X`, etc.). `/etc` changes never require a reflash to undo; if a change would, it does not belong in a pause — it belongs in the image-build block with its own gate.

6. **Skip only for invisible work.** Protocol docs, repo tooling, scripts that only read. A read-only logger running on the device IS a change (it costs CPU and writes files) and gets a pause the first time.

### What counts as a sub-phase

Each numbered milestone in `ROADMAP.md`; any change touching more than ~2 files or ~100 lines; any change to what the device boots or runs at startup. One-line fixes and copy edits don't need the rule.

---

## Don't reinvent the wheel

For any non-trivial problem, search for prior art before designing from scratch. The bar is "look first", not "search exhaustively".

1. **Check upstream first.** `armada-os/armada` moves fast (several merges a day). Before building a tuning knob, check whether a newer upstream commit already added it; `git log upstream/main --oneline -- <path>` is cheap.
2. **Check the sibling distros.** ROCKNIX (Armada's device-support source), SteamOS/holo, Bazzite, and ChimeraOS have solved fan curves, power profiles, and handheld quirks for years. The Steam Deck's `jupiter-fan-control` is the reference for a userspace fan daemon and is already vendored in this tree as `jupiter-hw-support`.
3. **Check the user's reference repos** under `C:\Users\haith\Documents\Vibe Projects\` when relevant.
4. **Improve, don't blind-copy.** Note when the prior art targets different hardware and say what changes.
5. **Cite the source** in a comment or in `docs/CODEBASE_INDEX.md`.

---

## Grounded pushback + grounded agreement

Disagreement and agreement both require evidence — the same bar in both directions.

Pushback cites: code in the repo that already handles it, a measurement, an upstream decision or commit, prior art that went another way, a specific failure mode. Agreement cites the same kinds of things. "That might cause issues" and "sounds good" are both hedging. Subjective calls (naming, scope, what "quiet enough" means) are flagged as subjective: *"This is your call — I'd lean X because Y."* No performative devil's-advocate.

---

## One source of truth — data AND behavior

A setting in this OS often has several writers: the factory config in the image, the `/etc` overlay, Armada Control's UI (which writes to that same `/etc` file), Steam's Quick Access Menu (which drives `armada-powerd` over D-Bus), and per-game tweaks. Before changing how any value is read or written:

1. **List every surface** that reads or writes it.
2. **Decide who owns the file.** Repo-owned files are pushed device-ward and never hand-edited on the device; UI-owned files are pulled back into the repo as a record, never pushed over. Write the ownership down in `docs/DEVICE.md`.
3. **Check parity** after a change: does the UI show what the file says? Does `armada-power status` agree with both?
4. **Schema changes sweep all surfaces in one commit.**

---

## Methodical pacing

This is a months-long personal project with a device that can be bricked. The user said "A to Z, slowly but sure" — that is the pacing instruction. More pause-points, not fewer. No "apply five things and see". Anything touching the bootloader, partitions, or the boot image gets its own block, its own backup step, and its own explicit go from the user.

---

## Audits target real optimization

Before any audit or cleanup pass, name the measurable win. "This service is running and costs X% CPU / Y mW at idle" is a win. "This could be leaner" is not. Prefer one measured change over a sweep of unmeasured ones. Audit scope is the fork delta and the device's runtime state, not upstream's code style.

---

## Capture transferable lessons — `*kbdoc`

The Knowledge Base is its own git repo, `github.com/haithemobeidi/knowledge-base`, cloned at `C:\Users\haith\Documents\Vibe Projects\Knowledge Base\` on this machine (locate it, don't assume: the folder name varies per machine). It holds standalone Markdown lessons reusable across projects.

**The rule:** when a piece of work produces a lesson that would still be true in a *different* project, say so in-chat immediately with the marker `*kbdoc` and a one-line summary. At `/end` the wrap only **tags** which lessons are KB-viable; the article is written after `/end` when the user asks, or on the spot if they ask mid-session.

A lesson qualifies when all three hold: **transferable** (true beyond this fork), **non-obvious** (cost real time or the obvious approach was wrong), **durable** (structural, not a bug upstream fixes next week). **Dead ends count** and are often the most valuable — write what was *measured* not to work and what would make it worth revisiting.

**Before writing: `git pull --ff-only` the KB — always.** The clone is stale by default; check coverage after pulling, extend an existing article over writing a second one on an adjacent topic. Commit and push the KB in its own repo; it never rides a commit here.

Anti-patterns: flagging `*kbdoc` on everything (if most sessions produce one, the bar is too low); dumping session narrative into an article; writing while the fix is unverified.
