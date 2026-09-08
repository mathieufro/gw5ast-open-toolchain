#!/usr/bin/env python3
"""Ask the oracle which VCCIO levels it accepts an `ELVDS_OBUF` at (`P3.T25`).

The ELVDS row's sweep runs at the board's own 3.3 V and is `refused` there.
The refusal names the *attribute value*, not the buffer, so on its own it
cannot say whether ELVDS is illegal on this die or illegal at that rail.
This tool puts the second question to `gw_sh` directly.

It is deliberately **not** a batch: there is no equivalence to compute and no
open half to build -- the whole measurement is whether the vendor's front end
accepts the constraint file, and its exact words when it does not.  One
`gw_sh` invocation per level, counted in the ledger like any other oracle run.

    python -m tools.probe_elvds_vccio --design-root $DATASTORE/p3t25-vccio \
        --out evidence/elvds/vccio-matrix.tsv
"""
import argparse
import os
import sys

#: Columns of the matrix, in order.  `verdict` is the §6 vocabulary
#: (`ok` | `refused`); `detail` is the vendor's own text, never a paraphrase.
COLUMNS = ("io_type", "bank", "bank_vccio", "verdict", "detail", "run_id")


def probe(vccio, design_root):
    """One level: render, run `gw_sh`, return the matrix row."""
    from fuzz.gw5ast138c.harness import gen, oracle
    from fuzz.gw5ast138c.shapes import diff_io_vccio_probe as probe_shape

    spec = probe_shape.spec_for(vccio)
    run_id = f"p3-elvds-vccio-{vccio.replace('.', 'v')}"
    design_dir = os.path.join(design_root, run_id)
    gen.run(spec, design_dir, vccio)
    result = oracle.run_oracle(design_dir, top_module=spec.top_module,
                               extra_options=gen.gwsh_options_of(spec, vccio))
    ok = result["preflight"].ok
    detail = "" if ok else (
        oracle.vendor_refusal(result.get("log_text", ""),
                              result["preflight"].returncode)
        or result["preflight"].reason)
    return {
        "io_type": spec.primitive,
        "bank": str(probe_shape.PROBED_BANK),
        "bank_vccio": vccio,
        "verdict": "ok" if ok else "refused",
        "detail": detail.replace("\t", " ").strip(),
        "run_id": run_id,
    }


def render(rows):
    lines = ["\t".join(COLUMNS)]
    lines += ["\t".join(r[c] for c in COLUMNS) for r in rows]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-root", required=True)
    parser.add_argument("--out", required=True,
                        help="the matrix TSV; existing rows are kept and the "
                             "probed levels appended")
    parser.add_argument("--levels", nargs="*", default=None,
                        help="default: every level the probe shape declares")
    args = parser.parse_args(argv)

    from fuzz.gw5ast138c.shapes import diff_io_vccio_probe as probe_shape
    levels = args.levels or list(probe_shape.LEVELS)

    rows = []
    for vccio in levels:
        row = probe(vccio, args.design_root)
        print("\t".join(row[c] for c in COLUMNS))
        rows.append(row)

    existing = []
    if os.path.isfile(args.out):
        with open(args.out) as fh:
            existing = [l.rstrip("\n") for l in fh if l.strip()][1:]
    with open(args.out, "w") as fh:
        fh.write(render(rows) if not existing else
                 "\t".join(COLUMNS) + "\n" + "\n".join(existing) + "\n"
                 + "".join("\t".join(r[c] for c in COLUMNS) + "\n" for r in rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
