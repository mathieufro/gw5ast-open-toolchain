#!/usr/bin/env python3
"""Derive the `AE350_SOC` port map of record, from the shipped chipdb.

Two earlier generations of this map are in the phase's history and they
disagree, so the artefact this writes is generated from the chipdb the router
actually loads -- never from prose -- and carries three things that settle the
disagreement:

* the **direction convention**, and the per-bit evidence for it. A tap's
  direction is decided against the vendor's own routing, not against the wire
  name: `tests/data/ae350-pip-roles-138c.json` says which row-0 wires the
  vendor ends a pip on and which it starts one from, and a bit is called an
  input only where the fabric is seen to drive its wire.
* the **arithmetic between the two generations**, recomputed from the earlier
  artefact in git rather than quoted.
* every **unmapped** bit, by port, bit index, reason and sentinel wire.

Usage::

    python3 tools/derive_ae350_portmap_reconciled.py           # rewrite
    python3 tools/derive_ae350_portmap_reconciled.py --check   # fail if stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import paths  # noqa: E402

DEVICE = "GW5AST-138C"
PRIMITIVE = "AE350_SOC"
ANCHOR = (0, 159)

#: The generation this artefact supersedes, and the commit that flipped it.
PREVIOUS_GENERATION = "153954b"
FLIP_COMMIT = "6e58e8b"

#: The wire classes a fabric tap can name. A port bound to anything else is
#: not on the fabric at all -- `CORE_CLK` takes a dedicated PLL hop -- and the
#: routing graph has nothing to say about its direction.
TAP_WIRE = re.compile(r"(?:A|B|C|D|F|Q|OF|CE|CLK|LSR)\d+\Z")

_OTC = Path(paths.OTC_ROOT)
EVIDENCE = _OTC / "evidence" / "ae350"
OUT_JSON = EVIDENCE / "portmap-reconciled-138c.json"
PIP_ROLES_RELPATH = Path("tests") / "data" / "ae350-pip-roles-138c.json"
PREVIOUS_ARTEFACT = "evidence/ae350/wire-map-138c.json"


def apicula() -> Path:
    root = paths.apicula_root()
    if root is None:
        raise SystemExit("apicula checkout not found; set $FL_APICULA")
    return Path(root)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wire_class(wire: str) -> str:
    return re.match(r"[A-Z]+", wire).group()


def live_portmap(chipdb_path: Path):
    """`(ins, outs, unmapped)` read from the chipdb the router loads.

    A port's stored value is either a bare wire name -- the tap is in the
    anchor cell -- or the Himbaechel alias `AE350_SOC<port><wire>`, whose node
    carries the cell the tap really lives in. Resolving through the node is
    what makes this the map as nextpnr sees it, rather than a re-derivation.
    """
    from apycula import chipdb as chipdb_mod

    db = chipdb_mod.load_chipdb(str(chipdb_path))
    block = db.extra_func[ANCHOR]["ae350"]

    def resolve(value):
        if value.startswith(chipdb_mod._AE350_UNMAPPED_PREFIX):
            return None
        node = db.nodes.get(f"X{ANCHOR[1]}Y{ANCHOR[0]}/{value}")
        if node is None:
            return (ANCHOR[0], ANCHOR[1], value)
        elsewhere = [loc for loc in node[1] if loc[2] != value]
        if len(elsewhere) != 1:
            raise SystemExit(f"ambiguous node for {value}: {node!r}")
        return tuple(elsewhere[0])

    ins = {port: resolve(value) for port, value in block["ins"].items()}
    outs = {port: resolve(value) for port, value in block["outs"].items()}
    return ins, outs, dict(block["unmapped"])


def pip_roles(path: Path):
    """`{(row, col): (destinations, sources)}` from the banked fixture."""
    payload = json.loads(Path(path).read_text())
    roles = {}
    for key, entry in payload["tiles"].items():
        row, col = (int(part) for part in key.split(","))
        roles[(row, col)] = (set(entry.get("ae350_dest", ())),
                             set(entry.get("ae350_src", ())))
    return payload, roles


def evidence_for(tap, roles):
    """What the vendor's routing says about one tap's direction."""
    if tap is None:
        return None
    row, col, wire = tap
    if not TAP_WIRE.fullmatch(wire):
        return "not-a-fabric-tap"
    tile = roles.get((row, col))
    if tile is None:
        return "no-pip-in-tile"
    dest, src = tile
    if wire in dest and wire in src:
        return "both"
    if wire in dest:
        return "pip-destination"
    if wire in src:
        return "pip-source"
    return "wire-not-in-any-pip"


def class_invariant(roles):
    """Per wire class, how often the vendor's row-0 routing uses it each way.

    This is what makes a direction sound for a bit the vehicle never exercises:
    a class with sources and no destinations across every decoded row-0 tile
    can only be driven from outside the fabric.
    """
    counts = {}
    for dest, src in roles.values():
        for wire in dest:
            counts.setdefault(wire_class(wire), Counter())["as_destination"] += 1
        for wire in src:
            counts.setdefault(wire_class(wire), Counter())["as_source"] += 1
    return {cls: dict(seen) for cls, seen in sorted(counts.items())}


def previous_generation(rev=PREVIOUS_GENERATION):
    """The 867/44 generation's bound set, keyed `(direction, bit)`.

    That artefact is keyed by `.dat` table, and the reading it records binds
    `Ae350SocIns` to the inputs and `Ae350SocOuts` to the outputs, so the table
    name *is* the direction there.
    """
    blob = subprocess.run(
        ["git", "-C", str(_OTC), "show", f"{rev}:{PREVIOUS_ARTEFACT}"],
        check=True, capture_output=True, text=True).stdout
    payload = json.loads(blob)
    return {"ins": {e["bit"]: e for e in payload["bits"]["Ae350SocIns"]},
            "outs": {e["bit"]: e for e in payload["bits"]["Ae350SocOuts"]}}


def build():
    root = apicula()
    chipdb_path = root / "apycula" / f"{DEVICE}.msgpack.xz"
    fixture_path = root / PIP_ROLES_RELPATH
    ins, outs, unmapped = live_portmap(chipdb_path)
    fixture, roles = pip_roles(fixture_path)

    current = json.loads((EVIDENCE / "wire-map-138c.json").read_text())
    slot_of = {
        "ins": {e["port"]: (e["table"], e["slot"], e["bit"])
                for e in current["bits"]["inputs"]},
        "outs": {e["port"]: (e["table"], e["slot"], e["bit"])
                 for e in current["bits"]["outputs"]},
    }

    bits = {}
    agreement = {}
    for half, portmap, expected in (("inputs", ins, "pip-destination"),
                                    ("outputs", outs, "pip-source")):
        key = "ins" if half == "inputs" else "outs"
        rows = []
        for port, tap in sorted(portmap.items(), key=lambda kv: slot_of[key][kv[0]][2]):
            table, slot, bit = slot_of[key][port]
            record = {"bit": bit, "port": port, "table": table, "slot": slot}
            if tap is None:
                record.update(row=None, col=None, wire=None,
                              direction_evidence="unmapped",
                              provisional=False)
            else:
                row, col, wire = tap
                seen = evidence_for(tap, roles)
                cls = (wire_class(wire) if TAP_WIRE.fullmatch(wire)
                       else "not-a-fabric-tap")
                record.update(row=row, col=col, wire=wire,
                              wire_class=cls,
                              direction_evidence=seen,
                              provisional=seen not in (expected,
                                                       "not-a-fabric-tap"))
                agreement.setdefault(half, {}).setdefault(cls, Counter())[seen] += 1
            rows.append(record)
        bits[half] = rows

    previous = previous_generation()
    delta = {}
    for half, key in (("inputs", "ins"), ("outputs", "outs")):
        old = {e["bit"] for e in previous[key].values() if e["wire"]}
        new = {r["bit"] for r in bits[half] if r["wire"]}
        delta[half] = {
            "previous_bound": len(old),
            "current_bound": len(new),
            "bound_now_only": sorted(new - old),
            "bound_previously_only": sorted(old - new),
            "bound_in_both_on_a_different_wire": sum(
                1 for r in bits[half]
                if r["wire"] and r["bit"] in old
                and (previous[key][r["bit"]]["row"],
                     previous[key][r["bit"]]["col"],
                     previous[key][r["bit"]]["wire"]) != (r["row"], r["col"], r["wire"])),
        }

    unmapped_rows = []
    for port, reason in sorted(unmapped.items()):
        half = "ins" if port in ins else "outs"
        table, slot, bit = slot_of[half][port]
        unmapped_rows.append({
            "port": port,
            "direction": "input" if half == "ins" else "output",
            "bit": bit,
            "table": table,
            "slot": slot,
            "reason": reason,
            "sentinel_wire": f"AE350_UNMAPPED_{port}",
        })

    return {
        "device": DEVICE,
        "primitive": PRIMITIVE,
        "anchor": list(ANCHOR),
        "generated_from": {
            "chipdb": str(PIP_ROLES_RELPATH.parent.parent.parent),
            "chipdb_sha256": sha256(chipdb_path),
            "pip_roles_fixture": str(PIP_ROLES_RELPATH),
            "pip_roles_sha256": sha256(fixture_path),
            "vendor_runs": fixture["runs"],
        },
        "direction_convention": (
            "die row 0 carries no bels, so a tap is an ordinary local wire and "
            "its direction is its role in the routing graph: the fabric ends a "
            "pip on A/B/C/D/CE/CLK/LSR, so those are the block's INPUTS; only "
            "the block can drive F/Q/OF, which the fabric starts a pip from, so "
            "those are its OUTPUTS. Neither .dat table is one direction"),
        "direction_evidence_legend": {
            "pip-destination": "the vendor's routing ends a pip on this wire",
            "pip-source": "the vendor's routing starts a pip from this wire",
            "wire-not-in-any-pip": ("the vehicle exercises no pip on this wire; "
                                    "direction rests on the class, which the "
                                    "same run decides with no counterexample"),
            "no-pip-in-tile": ("the tile is absent from the vendor bitmap, so "
                               "the run says nothing about this bit"),
            "not-a-fabric-tap": ("the port is not bound to a fabric wire at "
                                 "all: `CORE_CLK` takes the dedicated PLL hop "
                                 "measured in evidence/ae350/core-clock.md, so "
                                 "the routing graph does not decide it"),
        },
        "class_invariant": class_invariant(roles),
        "pip_agreement": {half: {cls: dict(counts)
                                 for cls, counts in sorted(classes.items())}
                          for half, classes in agreement.items()},
        "generations": {
            "previous": {"rev": PREVIOUS_GENERATION, "bound": 867, "unbound": 44},
            "current": {"bound": sum(1 for half in bits for r in bits[half]
                                     if r["wire"]),
                        "unmapped": len(unmapped_rows)},
            "flip_commit": FLIP_COMMIT,
            "delta": delta,
        },
        "unmapped": unmapped_rows,
        "bits": bits,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed artefact has drifted")
    args = parser.parse_args(argv)
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT_JSON.is_file() or OUT_JSON.read_text() != text:
            print(f"STALE {OUT_JSON}", file=sys.stderr)
            return 1
        print(f"OK {OUT_JSON}")
        return 0
    OUT_JSON.write_text(text)
    print(f"wrote {OUT_JSON} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
