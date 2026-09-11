#!/usr/bin/env bash
# /end check for this fork — wired as `check_command` in .claude/protocol.json.
#
# Why a script and not a compiler: this repo has none. The guard is syntax on
# everything the fork delta touches, plus a parse of every .conf under
# device-overlay/ — armada-powerd silently drops a malformed
# power-profiles.conf and reverts to factory defaults, so a typo would undo
# tuning without an error anywhere.
#
# The diff base is the FORK POINT (merge-base with upstream/main), not
# upstream's tip: when we're behind upstream, `git diff upstream/main` would
# list upstream's own new commits as "our" changes.
#
# Exit 1 only on a syntax/parse failure. Unindexed delta files are printed as
# warnings for /end Step 1b (the global backstop diffs HEAD only, which misses
# a file edited via the shell in an earlier commit).
set -u
cd "$(dirname "$0")/.." || exit 1

fail=0
base=$(git merge-base HEAD upstream/main 2>/dev/null) || {
  echo "check-delta: cannot find upstream/main — run: git fetch upstream"
  exit 1
}

mapfile -t files < <({ git diff --name-only --diff-filter=d "$base"; git ls-files --others --exclude-standard; } | sort -u)

have_shellcheck=0
command -v shellcheck >/dev/null 2>&1 && have_shellcheck=1

is_shell() {
  case "$1" in
    *.sh) return 0 ;;
  esac
  head -c 100 "$1" 2>/dev/null | head -n 1 | grep -q -E '^#!.*\b(ba)?sh\b'
}

for f in "${files[@]}"; do
  [ -f "$f" ] || continue
  case "$f" in
    *.py)
      python -c 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")' "$f" \
        || { echo "FAIL python syntax: $f"; fail=1; }
      ;;
    device-overlay/*.conf)
      python -c 'import configparser, sys; c = configparser.ConfigParser(); c.read(sys.argv[1], encoding="utf-8") or sys.exit(1)' "$f" \
        || { echo "FAIL overlay .conf does not parse (armada-powerd would drop it silently): $f"; fail=1; }
      ;;
  esac
  if is_shell "$f"; then
    bash -n "$f" || { echo "FAIL bash -n: $f"; fail=1; }
    if [ "$have_shellcheck" = 1 ]; then
      shellcheck "$f" || { echo "FAIL shellcheck: $f"; fail=1; }
    fi
  fi
done
[ "$have_shellcheck" = 1 ] || echo "note: shellcheck not on PATH — shell files were syntax-checked only"

# Index backstop over the whole fork delta (warnings only).
for f in "${files[@]}"; do
  [ -f "$f" ] || continue
  case "$f" in
    .claude/*|output/*|_build*|*/__pycache__/*|device-data/*|*.pyc) continue ;;
    docs/CODEBASE_INDEX.md|docs/CURRENT_STATE.md|docs/HANDOFF_LOG.md|docs/SESSION_LEDGER.md) continue ;;
  esac
  grep -qF -- "\`$f\`" docs/CODEBASE_INDEX.md || echo "WARN not in docs/CODEBASE_INDEX.md: $f"
done

if [ "$fail" = 1 ]; then
  echo "check-delta: FAILED (${#files[@]} delta files checked)"
  exit 1
fi
echo "check-delta: OK (${#files[@]} delta files checked)"
