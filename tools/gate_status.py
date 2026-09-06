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

Markers are never cleaned up, so the directory accumulates every gate run
the project has ever spawned, red ones included. The question this tool
answers is "is the latest gate run in each repo green?", so only the
**newest marker per repo** is judged; the older ones are still listed, with
status `SUPERSEDED`, as the history they are. A `RUNNING` marker whose
pidfile names a process that no longer exists is `DEAD` -- the run was
killed (its agent went away), and no result will ever arrive.

Exit codes: 0 if the newest marker of every repo is PASS or
RUNNING-and-fresh (or none found at all); 1 if a newest marker is FAIL or
DEAD, or is RUNNING with a `.log` older than 30 minutes (stale).
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
        gates[gate_id] = {"id": gate_id, "status": status, "age_minutes": age,
                          "mtime": os.path.getmtime(result_path)}

    pids = {}

    for pid_path in glob.glob(os.path.join(gates_dir, "*.pid")):
        gate_id = os.path.basename(pid_path)[: -len(".pid")]
        try:
            pids[gate_id] = int(open(pid_path).read().strip())
        except (OSError, ValueError):
            pass

    for log_path in glob.glob(os.path.join(gates_dir, "*.log")):
        basename = os.path.basename(log_path)
        if basename.endswith(".watchdog.log"):
            continue  # the watchdog's own log, not a second gate
        gate_id = basename[: -len(".log")]
        if gate_id in gates:
            continue  # already has a terminal .result
        age = _age_minutes(os.path.getmtime(log_path), now)
        status = "RUNNING"
        pid = pids.get(gate_id)
        if pid is not None and not _pid_alive(pid):
            status = "DEAD"
        gates[gate_id] = {"id": gate_id, "status": status, "age_minutes": age,
                          "mtime": os.path.getmtime(log_path)}

    _mark_superseded(gates.values())

    for gate in gates.values():
        gate.pop("mtime", None)

    return sorted(gates.values(), key=lambda g: g["id"])


def _pid_alive(pid):
    """True iff a process with `pid` still exists (it may not be ours)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return True  # cannot tell: do not call a live gate dead
    return True


def repo_of(gate_id):
    """The repo a marker belongs to: the first field of `<repo>-<ref>-<sha>`."""
    return gate_id.split("-", 1)[0]


def _mark_superseded(gates):
    """All but the newest marker of each repo become `SUPERSEDED`.

    Markers are never deleted, so a red run from three phases ago would
    otherwise keep the tool red forever. History stays visible; only the
    newest run per repo carries a verdict.
    """
    newest = {}
    for gate in gates:
        repo = repo_of(gate["id"])
        best = newest.get(repo)
        if best is None or (gate["mtime"], gate["id"]) > (best["mtime"], best["id"]):
            newest[repo] = gate
    keep = {id(g) for g in newest.values()}
    for gate in gates:
        if id(gate) not in keep:
            gate["status"] = "SUPERSEDED"


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
        if gate["status"] in ("FAIL", "DEAD"):
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
