"""`P1.T41` -- fit and check the GW5AST-138C `PLL` charge pump.

Reads back the four attributes the vendor *derives* from the operating point
(`FLDCOUNT`, `KVCO`, `A_ICP_SEL`, `A_LPF_RES_SEL`; `A_LPF_CAP_SEL` is read too
and is never written) out of every vendor bitstream of the three campaigns,
solves for the two free coefficients of the model, and asserts that
`apycula.gw5ast138c_pll_pump` reproduces every measured point exactly.

    p1-pll-sweep-a   20 runs   IDIV / FBDIV axes                (P1.T23)
    p1-pll-sweep-b   20 runs   ODIV0 / ODIV1 / MDIV axes        (P1.T41)
    p1-pll-pump      10 runs   the (Fpfd, Ndiv) wedge's corners (P1.T41)

Three of the pump points carry `MDIV_SEL 1`, for which the vendor writes its
own default `A_MDIV_SEL 8` and a charge pump consistent with neither divider;
they are excluded from the fit and reported separately, which is the
measurement `gw5ast138c_pll_pump.MDIV_SEL_MIN` records.  Three more were
refused outright by the vendor (`PA2078` at `FCLKIN` 650 MHz) and produced no
bitstream at all.

Usage:
    python gen_pump_138c.py <runs.jsonl> [<out.json>]
"""
import json
import sys
from pathlib import Path

from apycula import gw5ast138c_pll_pump as pump

import decode_pll_attrs_138c as decode

#: The vendor rewrites this divider, so its points cannot constrain the fit.
UNSUPPORTED_MDIV = 1


def operating_point(row):
    """`(fclkin, idiv, fbdiv, mdiv)` out of one evidence row's `sweep` map.

    Sweep rows carry only the swept parameter, so the rest of the operating
    point comes from the shape the row names -- the single source of it.
    """
    sweep = row["sweep"]
    shape = row["shape"]
    if shape == "clocking_pll_pump":
        from fuzz.gw5ast138c.shapes import clocking_pll_pump as mod
        return mod.operating_point(sweep["point"])
    from fuzz.gw5ast138c.shapes import clocking_pll as mod
    for axis in mod.AXES.values():
        if axis.name != sweep["axis"] or axis.param not in sweep:
            continue
        parms = axis.params(sweep[axis.param])
        return (float(parms["FCLKIN"].strip('"')), int(parms["IDIV_SEL"]),
                int(parms["FBDIV_SEL"]), int(parms["MDIV_SEL"]))
    raise SystemExit(f"{row['run_id']}: sweep {sweep} matches no axis")


def coefficient_interval(points):
    """The `Ic`-per-`Ndiv` interval every point of one resistor allows.

    `A_ICP_SEL = round(a * Ndiv) * 10`, so each point pins `a` to an interval
    of width `1/Ndiv`; the fit is their intersection.  An empty intersection
    would mean the one-coefficient-per-resistor model is wrong, so it is
    returned rather than averaged away.
    """
    low, high = 0.0, float("inf")
    for point in points:
        ndiv, icp = point["ndiv"], point["icp"] // 10
        low = max(low, (icp - 0.5) / ndiv)
        high = min(high, (icp + 0.5) / ndiv)
    return low, high


def main(argv):
    runs_path = Path(argv[1])
    out_path = Path(argv[2]) if len(argv) > 2 else None

    measured, refused, unsupported = [], [], []
    for line in runs_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        # Only the two campaign shapes carry a full, machine-readable
        # operating point; `P1.T19`'s site trace and `P1.T22`'s attrmap sweep
        # name their points differently and are read by their own analysers.
        if row.get("shape") not in ("clocking_pll", "clocking_pll_pump"):
            continue
        if "axis" not in row.get("sweep", {}):
            continue
        fclkin, idiv, fbdiv, mdiv = operating_point(row)
        entry = {
            "run_id": row["run_id"], "shape": row["shape"],
            "fclkin": fclkin, "idiv": idiv, "fbdiv": fbdiv, "mdiv": mdiv,
            "fref": fclkin / idiv, "ndiv": fbdiv * mdiv,
            "fvco": fclkin * fbdiv * mdiv / idiv,
        }
        if not row.get("vendor_fs"):
            refused.append(entry)
            continue
        entry.update(decode.decode(row["vendor_fs"][0]["path"]))
        entry["icp"] = entry.pop("A_ICP_SEL")
        entry["r_value"] = entry.pop("A_LPF_RES_SEL")
        (unsupported if mdiv == UNSUPPORTED_MDIV else measured).append(entry)

    by_r = {}
    for entry in measured:
        by_r.setdefault(entry["r_value"], []).append(entry)
    fit = {}
    for r_value, points in sorted(by_r.items()):
        low, high = coefficient_interval(points)
        # `A_LPF_RES_SEL` is written as the symbolic `R<n>`; `pll_attrvals`
        # numbers `R1` .. `R7` as 23 .. 29.
        fit[r_value - 22] = {
            "r_value": r_value, "points": len(points),
            "interval": [low, high], "fitted": (low + high) / 2,
            "consistent": low <= high,
        }

    mismatches = []
    for entry in measured:
        want = (entry["FLDCOUNT"], entry["icp"], entry["r_value"] - 22)
        got = pump.pump(entry["fref"], entry["fvco"])
        if got != want:
            mismatches.append({"run_id": entry["run_id"], "want": list(want),
                               "got": list(got)})

    result = {
        "task": "P1.T41", "device": "GW5AST-138C",
        "measured_points": len(measured),
        "refused_points": refused,
        "unsupported_mdiv_points": unsupported,
        "kvco": sorted({e["KVCO"] for e in measured}),
        "lpf_cap": sorted({str(e["A_LPF_CAP_SEL"]) for e in measured}),
        "fldcount_by_fref": sorted({(round(e["fref"], 4), e["FLDCOUNT"])
                                    for e in measured}),
        "fit": fit,
        "mismatches": mismatches,
        "points": measured,
    }
    print(f"{len(measured)} measured points, {len(unsupported)} excluded "
          f"(MDIV_SEL {UNSUPPORTED_MDIV}), {len(refused)} refused by the vendor")
    for r_idx, row in sorted(fit.items()):
        print(f"  R{r_idx}: {row['points']:3d} points, Ic/Ndiv in "
              f"[{row['interval'][0]:.5f}, {row['interval'][1]:.5f}] "
              f"-> {row['fitted']:.6f}")
    print(f"KVCO {result['kvco']}, A_LPF_CAP_SEL {result['lpf_cap']}")
    print(f"{len(mismatches)} of {len(measured)} points disagree with "
          f"apycula.gw5ast138c_pll_pump")
    if out_path:
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("wrote", out_path)
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
