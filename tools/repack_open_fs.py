"""Rebuild the **open** bitstream of a stored run with `gowin_pack` alone.

A packer fix has to be re-diffed against the vendor bitstreams already in the
datastore, and re-running the whole open flow for that is both slower and less
honest: `yosys` and `nextpnr-himbaechel` did not change, so their outputs must
not change either.  Repacking from the run's own ``top_pnr.json`` keeps the
placement fixed and isolates the packer's contribution, and it spends **no**
oracle run.

The dual-purpose-pin flags are not guessed: `nextpnr` records the two the
packer cross-checks (``SSPI``, ``I2C``) as parameters of the ``PINCFG`` cell it
emits, and `gowin_pack.get_PINCFG_fuses` raises when the two sides disagree --
so a wrong flag set is a hard error here, never a silent mis-pack.

``--verify`` repacks with the packer as it stands and requires the result to be
byte-identical to the stored ``top.fs``.  That is the guard that makes a
re-diff meaningful: only once the unmodified packer reproduces the stored
bitstream exactly can a difference after a fix be attributed to the fix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

DEVICE = "GW5AST-138C"

#: ``PINCFG`` parameter -> the `gowin_pack` flag that must accompany it.
PINCFG_FLAGS = {"SSPI": "--sspi_as_gpio", "I2C": "--i2c_as_gpio"}


def pincfg_flags(pnr_json):
    """The dual-purpose-pin flags this placement was built with."""
    with open(pnr_json, encoding="utf-8") as handle:
        pnr = json.load(handle)
    flags = []
    for module in pnr.get("modules", {}).values():
        for cell in module.get("cells", {}).values():
            if cell.get("type") != "PINCFG":
                continue
            for parm, flag in PINCFG_FLAGS.items():
                if int(str(cell.get("parameters", {}).get(parm, "0")), 2):
                    flags.append(flag)
    return sorted(set(flags))


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def repack(design_dir, out_name, apicula, python=sys.executable):
    """Run `gowin_pack` over the run's stored placement; return the output."""
    pnr_json = os.path.join(design_dir, "top_pnr.json")
    if not os.path.exists(pnr_json):
        raise SystemExit(f"{design_dir}: no top_pnr.json to repack from")
    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join(
                   [apicula] + ([os.environ["PYTHONPATH"]]
                                if os.environ.get("PYTHONPATH") else [])))
    cmd = ([python, "-m", "apycula.gowin_pack", "-d", DEVICE]
           + pincfg_flags(pnr_json) + ["-o", out_name, "top_pnr.json"])
    log = os.path.join(design_dir, "gowin_pack-repack.log")
    with open(log, "w", encoding="utf-8") as handle:
        proc = subprocess.run(cmd, cwd=design_dir, stdout=handle,
                              stderr=subprocess.STDOUT, env=env, check=False)
    if proc.returncode != 0:
        return None
    return os.path.join(design_dir, out_name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apicula", required=True)
    parser.add_argument("--designs", nargs="+", required=True,
                        help="run directories holding top_pnr.json")
    parser.add_argument("--out-name", default="top-repack.fs")
    parser.add_argument("--verify", action="store_true",
                        help="require byte-identity with the stored top.fs")
    args = parser.parse_args(argv)

    same = diff = failed = 0
    for design_dir in args.designs:
        name = os.path.basename(design_dir.rstrip("/"))
        out = repack(design_dir, args.out_name, args.apicula)
        if out is None:
            failed += 1
            print(f"{name}: FAILED (see gowin_pack-repack.log)", flush=True)
            continue
        stored = os.path.join(design_dir, "top.fs")
        equal = os.path.exists(stored) and sha256(out) == sha256(stored)
        same, diff = same + equal, diff + (not equal)
        print(f"{name}: {'same' if equal else 'differs'}", flush=True)
    print(f"REPACK: same={same} differs={diff} failed={failed}")
    if args.verify and (diff or failed):
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
