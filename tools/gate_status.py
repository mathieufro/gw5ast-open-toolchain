#!/usr/bin/env python3
"""Reads the detached local-gate markers written by `.githooks/pre-push`
(C12, D94, D95) and reports one status line per gate.

`.githooks/pre-push` never blocks a push: on a push to main/dev/
integration/*/epic/* it spawns `make gate GATE_SCOPE=branch` DETACHED and
returns immediately. That background run writes, under
`<open-toolchain>/evidence/_gates/`:

    <id>.log            -- combined stdout/stderr of the gate run
    <id>.pid            -- the backgrounded shell's pid
    <id>.result         -- `PASS` or `FAIL`, written as the LAST action
    <id>.watchdog.log   -- the out-of-process stall/death watchdog's log

`<id>` is `<repo>-<safe_ref>-<short_sha>` (see pre-push for the exact
construction); this tool never needs to parse it, only glob it.

This tool is the read side: it does not run or wait on anything, it only
looks at what the hook and its watchdog have left on disk. A gate whose
`.result` hasn't appeared yet but whose `.log` has is still RUNNING; this
tool applies a 30-minute staleness rule on top of that (the watchdog
already logs WATCHDOG_STALL/WATCHDOG_DEAD on its own schedule, but this
tool does not read the watchdog log -- it just re-applies the same
30-minute bound directly from file mtimes, per fine-line CLAUDE.md
"Verification": liveness is judged from artifact evidence, never a report).

Call shape::

    python gate_status.py [--json]

No positional args. `--gates-dir` is not exposed on the CLI (the directory
is always `$OTC/evidence/_gates`, `$OTC` being this script's own
grandparent, same pattern as `tools/paths.py`); tests reach a different
directory by calling `main(gates_dir=...)` directly instead.

Exit codes: 0 if every gate is PASS or RUNNING-and-fresh (or none found at
all); 1 if any gate is FAIL, or any RUNNING gate's `.log` is older than 30
minutes (stale).
"""
import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import OTC_ROOT  # noqa: E402

#: A RUNNING gate whose `.log` mtime is older than this is considered stale
#: (the watchdog would have logged WATCHDOG_STALL/WATCHDOG_DEAD by then).
STALE_MINUTES = 30


def default_gates_dir():
    return os.path.join(OTC_ROOT, "evidence", "_gates")


def _age_minutes(mtime, now=None):
    now = time.time() if now is None else now
    return (now - mtime) / 60.0


def collect_gates(gates_dir, now=None):
    """Returns a list of dicts `{"id", "status", "age_minutes"}`, sorted by
    id. `status` is one of PASS, FAIL, RUNNING. A gate is RUNNING when its
    `.log` exists but its `.result` does not yet (the gate started but
    hasn't finished); its age is approximated from the `.log` mtime, which
    is touched at start and appended to throughout the run -- there is no
    separate "started" timestamp, so this is the best available proxy."""
    now = time.time() if now is None else now
    gates = {}

    for result_path in glob.glob(os.path.join(gates_dir, "*.result")):
        gate_id = os.path.basename(result_path)[: -len(".result")]
        status = open(result_path).read().strip()
        age = _age_minutes(os.path.getmtime(result_path), now)
        gates[gate_id] = {"id": gate_id, "status": status, "age_minutes": age}

    for log_path in glob.glob(os.path.join(gates_dir, "*.log")):
        basename = os.path.basename(log_path)
        if basename.endswith(".watchdog.log"):
            continue  # the watchdog's own log, not a second gate
        gate_id = basename[: -len(".log")]
        if gate_id in gates:
            continue  # already has a terminal .result
        age = _age_minutes(os.path.getmtime(log_path), now)
        gates[gate_id] = {"id": gate_id, "status": "RUNNING", "age_minutes": age}

    return sorted(gates.values(), key=lambda g: g["id"])


def main(gates_dir=None, json_output=False):
    gates_dir = gates_dir or default_gates_dir()

    gates = collect_gates(gates_dir)

    if not gates:
        if json_output:
            print("[]")
        else:
            print("no gates found")
        return 0

    failing = False
    for gate in gates:
        if gate["status"] == "FAIL":
            failing = True
        elif gate["status"] == "RUNNING" and gate["age_minutes"] > STALE_MINUTES:
            failing = True

    if json_output:
        print(json.dumps(gates))
    else:
        for gate in gates:
            age_str = f"{gate['age_minutes']:.0f}m"
            print(f"{gate['id']}  {gate['status']}  age={age_str}")

    return 1 if failing else 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="gate_status.py",
        description="Report PASS/FAIL/RUNNING for detached local-gate runs "
                     "under evidence/_gates/ (C12/D94/D95).")
    parser.add_argument("--json", action="store_true",
                        help="Print a JSON array of {id, status, age_minutes} "
                             "instead of text lines.")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(main(json_output=args.json))
