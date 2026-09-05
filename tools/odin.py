#!/usr/bin/env python3
"""
odin.py — the one door to the handheld.

Wraps OpenSSH (key auth already installed; see docs/DEVICE.md) so every
device interaction goes through a single, logged, reviewable path.

  python tools/odin.py status              live power/fan/temp one-liner
  python tools/odin.py run  <cmd...>       run a command as armada
  python tools/odin.py sudo <cmd...>       run a command as root (password from ODIN_SUDO_PASS, default image pw)
  python tools/odin.py probe               read-only snapshot -> device-data/probe-<ts>.txt (git-ignored)
  python tools/odin.py pull                copy UI-owned configs -> device-state/ (committed) and show the git diff
  python tools/odin.py push [--yes]        copy device-overlay/etc/** -> /etc (dry-run unless --yes), then reload the daemon

Host: --host or ODIN_HOST (default below). The IP is DHCP and has moved before.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import subprocess
import sys

DEFAULT_HOST = "192.168.1.188"
USER = "armada"
REPO = pathlib.Path(__file__).resolve().parent.parent
DEVICE_STATE = REPO / "device-state"
DEVICE_DATA = REPO / "device-data"
OVERLAY = REPO / "device-overlay"

# UI-owned files (DECISIONS D-4): recorded in git, never pushed.
PULL_FILES = (
    "/etc/armada/power-profiles.conf",
    "/etc/armada/game-tweaks.json",
    "/etc/armada/input-calibration.json",
    "/etc/armada/abl.conf",
    "/var/lib/armada/powerd.state",
)

SSH_OPTS = ["-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes"]


def host() -> str:
    return os.environ.get("ODIN_HOST", DEFAULT_HOST)


def ssh(cmd: str, check: bool = True, capture: bool = True, stdin: str | None = None) -> str:
    proc = subprocess.run(
        ["ssh", *SSH_OPTS, f"{USER}@{host()}", cmd],
        input=stdin, text=True, encoding="utf-8", errors="replace",
        capture_output=capture,
    )
    if check and proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        raise SystemExit(f"ssh failed ({proc.returncode}): {cmd}")
    return (proc.stdout or "") if capture else ""


def sudo(cmd: str, check: bool = True) -> str:
    pw = os.environ.get("ODIN_SUDO_PASS", "armada")
    # -S reads the password from stdin; -p '' keeps the prompt out of stdout.
    return ssh(f"sudo -S -p '' {cmd}", check=check, stdin=pw + "\n")


def scp_from(remote: str, local: pathlib.Path) -> bool:
    local.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["scp", *SSH_OPTS, f"{USER}@{host()}:{remote}", str(local)],
                          capture_output=True, text=True)
    return proc.returncode == 0


def cmd_status(_: argparse.Namespace) -> None:
    out = ssh(
        "armada-power status 2>/dev/null | grep -E '^(profile|cpu_underclock|gpu_level|fan_pwm|temperature)=' | tr '\\n' ' '; "
        "echo; for h in /sys/class/hwmon/hwmon*; do [ \"$(cat $h/name)\" = pwmfan ] && echo \"pwm1=$(cat $h/pwm1) enable=$(cat $h/pwm1_enable)\"; done; "
        "echo \"load=$(cut -d' ' -f1-3 /proc/loadavg)\"; "
        "b=/sys/class/power_supply/battery; echo \"battery=$(cat $b/capacity)% $(cat $b/status) I=$(cat $b/current_now)uA V=$(cat $b/voltage_now)uV\""
    )
    print(out.strip())


def cmd_run(args: argparse.Namespace) -> None:
    print(ssh(" ".join(args.cmd), check=False).rstrip())


def cmd_sudo(args: argparse.Namespace) -> None:
    print(sudo(" ".join(args.cmd), check=False).rstrip())


PROBE_SECTIONS = {
    "identity": "hostname; uname -r; cat /usr/lib/armada/version; uptime -p",
    "powerd": "armada-power status 2>/dev/null",
    "cpufreq": "for p in /sys/devices/system/cpu/cpufreq/policy*; do echo \"$(basename $p) cpus=$(cat $p/related_cpus) cur=$(cat $p/scaling_cur_freq) smax=$(cat $p/scaling_max_freq) gov=$(cat $p/scaling_governor)\"; done",
    "gpu": "d=/sys/class/devfreq/3d00000.gpu; echo \"cur=$(cat $d/cur_freq) min=$(cat $d/min_freq) max=$(cat $d/max_freq) gov=$(cat $d/governor)\"",
    "thermal_top": "for z in /sys/class/thermal/thermal_zone*; do echo \"$(cat $z/temp) $(cat $z/type)\"; done | sort -rn | head -8",
    "fan": "for h in /sys/class/hwmon/hwmon*; do [ \"$(cat $h/name)\" = pwmfan ] && echo \"$h pwm1=$(cat $h/pwm1) enable=$(cat $h/pwm1_enable)\"; done",
    "battery": "b=/sys/class/power_supply/battery; for f in status capacity current_now voltage_now power_now temp; do echo \"$f=$(cat $b/$f 2>/dev/null)\"; done",
    "load": "cat /proc/loadavg; cat /proc/pressure/cpu",
    "top": "ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head -12",
    "etc_armada": "ls -la --time-style=long-iso /etc/armada/; for f in /etc/armada/*; do echo \"--- $f\"; cat $f; done",
    "perf_state": "cat /run/armada/perf-state.json 2>/dev/null",
    "services_running": "systemctl list-units --type=service --state=running --no-pager --no-legend | awk '{print $1}' | tr '\\n' ' '",
    "services_failed": "systemctl list-units --type=service --state=failed --no-pager --no-legend",
    "sleep": "cat /sys/power/mem_sleep",
    "powerd_journal": "journalctl -b -u armada-powerd --no-pager -q | tail -10",
}


def cmd_probe(_: argparse.Namespace) -> None:
    DEVICE_DATA.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = DEVICE_DATA / f"probe-{stamp}.txt"
    script = "; ".join(f"echo '### {name}'; {cmd}" for name, cmd in PROBE_SECTIONS.items())
    out = ssh(script, check=False)
    out_path.write_text(out, encoding="utf-8")
    print(out)
    print(f"\nsaved -> {out_path.relative_to(REPO)}")


def cmd_pull(_: argparse.Namespace) -> None:
    DEVICE_STATE.mkdir(exist_ok=True)
    got, missing = [], []
    for remote in PULL_FILES:
        local = DEVICE_STATE / remote.lstrip("/").replace("/", "__")
        if scp_from(remote, local):
            got.append(local.name)
        else:
            missing.append(remote)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    (DEVICE_STATE / "PULLED_AT.txt").write_text(f"{stamp} from {host()}\n", encoding="utf-8")
    print("pulled:", ", ".join(got) or "(nothing)")
    if missing:
        print("absent on device (fine if never set):", ", ".join(missing))
    diff = subprocess.run(["git", "-C", str(REPO), "status", "--short", "--", "device-state"],
                          capture_output=True, text=True).stdout
    print("\ngit status device-state/:\n" + (diff or "  (no change vs HEAD)"))


def cmd_push(args: argparse.Namespace) -> None:
    files = sorted(p for p in (OVERLAY / "etc").rglob("*") if p.is_file()) if (OVERLAY / "etc").exists() else []
    if not files:
        print("device-overlay/etc/ is empty — nothing to push.")
        return
    for local in files:
        remote = "/" + local.relative_to(OVERLAY).as_posix()
        print(f"{'PUSH' if args.yes else 'would push'}  {local.relative_to(REPO)}  ->  {remote}")
        if args.yes:
            # Two-step keeps the file content out of the command line and out of sudo's stdin.
            ssh("cat > /tmp/odin-push.tmp", stdin=local.read_text(encoding="utf-8"))
            sudo(f"install -D -m 0644 /tmp/odin-push.tmp {remote} && rm -f /tmp/odin-push.tmp")
    if args.yes:
        if any("armada/power-profiles.conf" in p.as_posix() for p in files):
            print("NOTE: power-profiles.conf is UI-owned (D-4); pushing it will fight Armada Control.")
        print(sudo("systemctl restart armada-powerd && sleep 2 && journalctl -b -u armada-powerd --no-pager -q | tail -3", check=False))
    else:
        print("\nDry run. Re-run with --yes to apply.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", help="override device IP (or set ODIN_HOST)")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("run"); p.add_argument("cmd", nargs=argparse.REMAINDER); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("sudo"); p.add_argument("cmd", nargs=argparse.REMAINDER); p.set_defaults(fn=cmd_sudo)
    sub.add_parser("probe").set_defaults(fn=cmd_probe)
    sub.add_parser("pull").set_defaults(fn=cmd_pull)
    p = sub.add_parser("push"); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_push)
    args = ap.parse_args()
    if args.host:
        os.environ["ODIN_HOST"] = args.host
    args.fn(args)


if __name__ == "__main__":
    main()
