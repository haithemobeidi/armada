#!/bin/bash
# baseline-logger.sh — read-only CSV logger for ROADMAP B1, run ON the device.
#
#   baseline-logger.sh OUT.csv [INTERVAL_S=3] [DURATION_S=0]   (0 = until killed)
#
# One row per interval: what the fan daemon sees (its own D-Bus Temperature /
# FanPwm), the raw fan PWM, the three hottest counted thermal zones (same zone
# set and same top-3 average as armada-powerd), CPU/GPU clocks, battery I/V/W,
# USB power presence, the fuel gauge's charge counter (uAh: the drain truth that
# depends on neither the % gauge nor the current sensor), load, and the running
# Steam appid. It never writes to
# sysfs. Stop it with: kill "$(cat OUT.csv.pid)". Pull the CSV with
# `tools/odin.py get`. Why a script and not a systemd unit: nothing to install,
# nothing to revert, and it dies with the session if forgotten.
set -uo pipefail

out=${1:?usage: baseline-logger.sh OUT.csv [INTERVAL_S] [DURATION_S]}
interval=${2:-3}
duration=${3:-0}

thermal=/sys/class/thermal
cpufreq=/sys/devices/system/cpu/cpufreq
gpu=/sys/class/devfreq/3d00000.gpu/cur_freq
bat=/sys/class/power_supply/battery
usb=/sys/class/power_supply/qcom-battmgr-usb
perf_state=/run/armada/perf-state.json

# The daemon counts zones whose type starts with cpu, gpu, video or mem
# (ddr-thermal is not counted) and averages the three hottest.
zone_files=()
zone_names=()
for z in "$thermal"/thermal_zone*; do
    [[ -r $z/type && -r $z/temp ]] || continue
    t=$(<"$z/type")
    case "$t" in
        cpu*|gpu*|video*|mem*) zone_files+=("$z/temp"); zone_names+=("$t") ;;
    esac
done

# hwmon numbering moves between deployments (was hwmon54, is not any more);
# find the fan by name every time.
pwm_file=
for h in /sys/class/hwmon/hwmon*; do
    [[ -r $h/name ]] && [[ $(<"$h/name") == pwmfan ]] && { pwm_file=$h/pwm1; break; }
done

read_or() { # file default
    if [[ -r $1 ]]; then cat "$1" 2>/dev/null || printf '%s' "$2"; else printf '%s' "$2"; fi
}

mkdir -p "$(dirname "$out")"
printf '%s\n' "$$" >"$out.pid"
{
    printf '# baseline-logger start=%s host=%s interval=%ss duration=%ss zones=%s pwm=%s\n' \
        "$(date --iso-8601=seconds)" "$(hostname)" "$interval" "$duration" "${#zone_files[@]}" "${pwm_file:-none}"
    printf 'ts,t,profile,temp_d,pwm_d,pwm_hw,z_top3_avg,z_max,z_max_name,cpu0_mhz,cpu6_mhz,gpu_mhz,bat_status,bat_pct,bat_ua,bat_uv,bat_w,bat_uah,usb_online,load1,appid\n'
} >>"$out"

start=$(date +%s)
while :; do
    now=$(date +%s)
    if (( duration > 0 && now - start >= duration )); then break; fi

    # One busctl call returns Temperature, FanPwm, Profile as three lines.
    temp_d=; pwm_d=; profile=
    { read -r _ temp_d; read -r _ pwm_d; read -r _ profile; } < <(
        busctl --system get-property org.armada.Power /org/armada/Power org.armada.Power1 \
            Temperature FanPwm Profile 2>/dev/null)
    profile=${profile//\"/}

    # Top-3 average and max over the counted zones, in the daemon's units (°C).
    z_top3_avg=; z_max=; z_max_name=
    if (( ${#zone_files[@]} )); then
        read -r z_top3_avg z_max z_max_name < <(
            cat "${zone_files[@]}" 2>/dev/null | awk -v names="${zone_names[*]}" '
                { v[NR] = $1 + 0 }
                END {
                    split(names, n, " ");
                    for (i = 1; i <= NR; i++) idx[i] = i;
                    for (i = 1; i <= NR; i++) for (j = i + 1; j <= NR; j++)
                        if (v[idx[j]] > v[idx[i]]) { tmp = idx[i]; idx[i] = idx[j]; idx[j] = tmp }
                    k = (NR < 3) ? NR : 3; s = 0;
                    for (i = 1; i <= k; i++) s += v[idx[i]];
                    printf "%.1f %.1f %s\n", s / k / 1000, v[idx[1]] / 1000, n[idx[1]]
                }')
    fi

    cpu0=$(read_or "$cpufreq/policy0/scaling_cur_freq" 0)
    cpu6=$(read_or "$cpufreq/policy6/scaling_cur_freq" 0)
    gpu_hz=$(read_or "$gpu" 0)
    bat_status=$(read_or "$bat/status" "")
    bat_pct=$(read_or "$bat/capacity" "")
    bat_ua=$(read_or "$bat/current_now" 0)
    bat_uv=$(read_or "$bat/voltage_now" 0)
    bat_uah=$(read_or "$bat/charge_counter" "")
    usb_online=$(read_or "$usb/online" "")
    load1=$(cut -d' ' -f1 /proc/loadavg)
    appid=$(sed -n 's/.*"appid": *"\{0,1\}\([0-9]*\)"\{0,1\}.*/\1/p' "$perf_state" 2>/dev/null | head -n1)

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$(date +%H:%M:%S)" "$now" "$profile" "$temp_d" "$pwm_d" "$(read_or "$pwm_file" "")" \
        "$z_top3_avg" "$z_max" "$z_max_name" \
        "$(( cpu0 / 1000 ))" "$(( cpu6 / 1000 ))" "$(( gpu_hz / 1000000 ))" \
        "$bat_status" "$bat_pct" "$bat_ua" "$bat_uv" \
        "$(awk -v i="$bat_ua" -v v="$bat_uv" 'BEGIN { printf "%.2f", i * v / 1e12 }')" \
        "$bat_uah" "$usb_online" "$load1" "$appid" >>"$out"

    sleep "$interval"
done
rm -f "$out.pid"
