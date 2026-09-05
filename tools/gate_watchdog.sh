#!/bin/sh
# Detached stall/death/completion watchdog for one background gate run
# (C12, D95; fine-line CLAUDE.md "Long-running work"). Judges liveness only
# from artifact evidence -- the gate's own pid and its log's mtime -- never
# from anything the gate says about itself. Fires exactly one terminal line
# (WATCHDOG_COMPLETE or WATCHDOG_DEAD), plus WATCHDOG_STALL if it goes quiet.
#
# Usage: gate_watchdog.sh <id> <log> <watchdog_log> <pidfile> [stall_min] [poll_s]
set -u
id=$1; log=$2; wdlog=$3; pidfile=$4
stall=${5:-5}; poll=${6:-30}
ts() { date +%H:%M:%S; }
done_marker() { grep -q "^BATCH_COMPLETE $id\$" "$log" 2>/dev/null; }
echo "$(ts) WATCHDOG_ARMED gate=$id stall=${stall}min poll=${poll}s" >> "$wdlog"
pid=""
i=0
while [ "$i" -lt 20 ]; do
    [ -s "$pidfile" ] && pid=$(cat "$pidfile") && break
    sleep 1; i=$((i + 1))
done
if [ -z "$pid" ]; then
    echo "$(ts) WATCHDOG_DEAD gate=$id pid never appeared in $pidfile" >> "$wdlog"
    exit 0
fi
while kill -0 "$pid" 2>/dev/null; do
    if done_marker; then
        echo "$(ts) WATCHDOG_COMPLETE gate=$id" >> "$wdlog"; exit 0
    fi
    age=$(( $(date +%s) - $(stat -f %m "$log" 2>/dev/null || stat -c %Y "$log" 2>/dev/null || echo 0) ))
    if [ "$age" -gt $((stall * 60)) ]; then
        echo "$(ts) WATCHDOG_STALL gate=$id age=$((age / 60))min pid=$pid ALIVE but producing nothing" >> "$wdlog"
    fi
    sleep "$poll"
done
if done_marker; then
    echo "$(ts) WATCHDOG_COMPLETE gate=$id" >> "$wdlog"
else
    echo "$(ts) WATCHDOG_DEAD gate=$id pid $pid exited without BATCH_COMPLETE" >> "$wdlog"
fi
