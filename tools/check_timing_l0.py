#!/usr/bin/env python3
"""`P0.T32` -- the per-cell-class L0 arc-band checker (`DEL-e` first cut, `D63`).

The step `V12a` executes (`spec.md` §12, `D66`, `D60`):

    python $OTC/tools/check_timing_l0.py --classes <cfu|pll|io|dsp|all> \\
        --sdf <vendor .sdf path> --chipdb $FL/apicula/apycula/GW5AST-138C.msgpack.xz

Two modes, one contract each:

1. **band mode** (`--sdf` given) -- the `V12a` measurement. Every timing arc
   nextpnr installs from the chipdb (`gowin_arch_gen.py:create_timing_info`,
   `:1911+`) is compared with the same arc in the vendor SDF. Stdout line 1 is
   exactly `L0 ok: <n>/<n> arcs within ±10%, <k> exceptions listed`; line 2 is
   the SDF header's condition line, echoed verbatim. Corner and field
   convention are `D24`/`D49f`'s: the SDF is taken at `-device_version C` at
   the default (worst-case) condition and the comparison uses the **`max`**
   field of each `min:typ:max` triple. Exit is non-zero if any arc is out of
   band. The real measurement is `P0.T37`.

2. **inventory mode** (no `--sdf`) -- the chipdb-side half, which is what
   Phase 0 can assert before a vendor SDF exists. Per class and per speed
   grade it reports the arc count and the min/median/max delay, checks the
   C1/I0 : C2/I1 ratio band, and reports which chipdb arc keys
   `create_timing_info` never consumes (the emission gaps). Exit is non-zero
   if a required class has 0 arcs or a ratio falls outside the band.

**C1/I0 is DERIVED, not measured** (`P0.T35`, `S17a`, `apicula/doc/timing-c1i0.md`):
the `.tm` file decodes three chunks, chunk 0 is the C2/I1 table (mislabelled
`ES` upstream) and C1/I0 is chunk 0 scaled by the datasheet ratio 1.25
(DS1239E Table 3-13). Every grade this tool prints carries its provenance, and
the 1.25 band below is therefore a **derivation regression check**, not a
measurement of silicon.

Class membership is `D60`'s: **cfu** = LUT / ALU / DFF / SSRAM / BSRAM / wires /
glbsrc / HCLK. `pll`, `io` and `dsp` have no cells on this die until Phases 1,
3 and 4, so those classes print `L0 skipped: class <c> has no arcs yet` and
exit 0 -- the chipdb's `iodelay` group is not the `io` class, whose cells do
not exist until Phase 3. `--classes all` is Phase 6's union re-assertion and
aggregates whatever classes are live.
"""
import argparse
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import sibling  # noqa: E402

# --------------------------------------------------------------------------
# 0. class membership (D60) and grade provenance (P0.T35 / P0.T36)
# --------------------------------------------------------------------------
# group -> required?  (a supporting group is reported but may not stand alone:
# `fanout` carries the per-wire fanout adders that the `wire` block consumes.)
CFU_GROUPS = {
    "lut": True,
    "alu": True,
    "dff": True,
    "sram": True,   # SSRAM (RAM16SDP4)
    "bram": True,   # BSRAM
    "wire": True,
    "glbsrc": True,
    "hclk": True,
    "fanout": False,
}
CLASS_GROUPS = {
    "cfu": CFU_GROUPS,
    "pll": {},
    "io": {},   # `iodelay` belongs to the IOLOGIC work of Phase 3, not to Phase 0
    "dsp": {},
}
LIVE_CLASSES = ("cfu",)          # populated on this die today (`D60`)
ALL_CLASSES = ("cfu", "pll", "io", "dsp")

# C1/I0 = 1.25 x C2/I1 by construction (P0.T35). The band is a float-round-trip
# tolerance on an exact multiplication, not a measurement tolerance.
DERIVED_RATIO = 1.25
RATIO_BAND = (1.2375, 1.2625)    # +/- 1%
GRADE_PROVENANCE = {
    "C2/I1": "measured (.tm chunk 0)",
    "C1/I0": "derived (1.25 x C2/I1, P0.T35 -- NOT measured)",
}
UNIDENTIFIED_PROVENANCE = "unidentified (.tm chunk, P0.T36 -- not a graded table)"

BAND = 0.10                      # +/-10% (D24 L0)


# --------------------------------------------------------------------------
# 1. chipdb / timing-dict loading
# --------------------------------------------------------------------------
def load_timing(chipdb_path):
    """Return the `db.timing` mapping: {grade: {group: {arc: value}}}.

    A `.json` path is read directly (synthetic fixtures); anything else is
    loaded as an apicula chipdb through `apycula.chipdb.load_chipdb`.
    """
    if chipdb_path.endswith(".json"):
        with open(chipdb_path) as f:
            return json.load(f)
    apicula = sibling("apicula", "APICULA_DIR")
    if apicula not in sys.path:
        sys.path.insert(0, apicula)
    from apycula.chipdb import load_chipdb  # noqa: E402
    return load_chipdb(chipdb_path).timing


def arc_max(value):
    """The delay of one chipdb timing entry, in ns.

    Entries are 4-tuples `(ff, fr, rr, rf)`; `create_timing_info`'s
    `group_to_timingvalue` takes their max as the slow corner. Scalar entries
    (`fanout`'s `*Num` fan counts) are not delays and return `None`.
    """
    if isinstance(value, (list, tuple)):
        return max(float(v) for v in value)
    return None


def class_arcs(timing, groups):
    """{group: {grade: {arc_key: ns}}} for the given group set."""
    out = {}
    for group in groups:
        per_grade = {}
        for grade, grade_groups in timing.items():
            arcs = grade_groups.get(group)
            if arcs is None:
                continue
            vals = {k: arc_max(v) for k, v in arcs.items()}
            per_grade[grade] = {k: v for k, v in vals.items() if v is not None}
        out[group] = per_grade
    return out


# --------------------------------------------------------------------------
# 2. what nextpnr actually emits (gowin_arch_gen.py:create_timing_info)
# --------------------------------------------------------------------------
class _RecDict(dict):
    """A dict that records every key `create_timing_info` reads."""

    def __init__(self, data, log):
        super().__init__(data)
        self._log = log

    def __getitem__(self, key):
        self._log.add(key)
        return super().__getitem__(key)


class _Cell:
    def __init__(self, speed, name, sink):
        self.speed, self.name, self.sink = speed, name, sink

    def _put(self, frm, to, tv):
        self.sink[(self.speed, self.name, frm, to)] = tv.slow_max / 1000.0

    def add_comb_arc(self, from_pin, to_pin, delay):
        self._put(from_pin, to_pin, delay)

    def add_clock_out(self, clock, output_pin, edge, delay):
        self._put(clock, output_pin, delay)

    def add_setup_hold(self, clock, input_pin, edge, setup, hold):
        pass  # setup/hold checks are not IOPATH arcs; L0 compares IOPATHs


class _Tmg:
    def __init__(self):
        self.arcs = {}
        self.pips = {}

    def add_cell_variant(self, speed_grade, name):
        return _Cell(speed_grade, name, self.arcs)

    def set_pip_class(self, grade, name, delay, *args, **kwargs):
        self.pips[(grade, name)] = delay.slow_max / 1000.0


class _Chip:
    def __init__(self):
        self.tmg = _Tmg()
        self.speed_grades = None

    def set_speed_grades(self, speed_grades):
        self.speed_grades = list(speed_grades)
        return self.tmg


class _Db:
    def __init__(self, timing):
        self.timing = timing


def record_emission(timing):
    """Run the real `create_timing_info` against a recording chipdb.

    Returns `(arcs, pips, consumed, handled_groups, error)`:
      * `arcs`     {(grade, cell, from_pin, to_pin): ns}
      * `pips`     {(grade, pip_class): ns}
      * `consumed` {group: set(arc keys read)}
      * `handled_groups`  the group names the emitter has a branch for
      * `error`    a string if nextpnr's generator could not be imported
    """
    gowin_dir = os.path.join(
        sibling("nextpnr", "NEXTPNR_DIR"), "himbaechel", "uarch", "gowin")
    apicula = sibling("apicula", "APICULA_DIR")
    for p in (gowin_dir, apicula):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import gowin_arch_gen
    except Exception as exc:                        # pragma: no cover - env dependent
        return {}, {}, {}, set(), f"{type(exc).__name__}: {exc}"

    consumed = {}
    rec = {}
    for grade, groups in timing.items():
        rec_groups = {}
        for group, arcs in groups.items():
            log = consumed.setdefault(group, set())
            rec_groups[group] = _RecDict(arcs, log)
        rec[grade] = _RecDict(rec_groups, set())
    chip = _Chip()
    gowin_arch_gen.create_timing_info(chip, _Db(rec))

    src = open(gowin_arch_gen.__file__).read()
    body = src[src.index("def create_timing_info"):]
    body = body[:body.index("\ndef ")]
    handled = set(re.findall(r'group\s*==\s*"([^"]+)"', body))
    return chip.tmg.arcs, chip.tmg.pips, consumed, handled, None


# --------------------------------------------------------------------------
# 3. SDF reading (D49f: `max` field of every min:typ:max triple)
# --------------------------------------------------------------------------
CONDITION_RE = re.compile(r"(?i)condition|\(PROCESS|\(VOLTAGE|\(TEMPERATURE")
TRIPLE_RE = re.compile(r"[-+0-9.eE]*:[-+0-9.eE]*:[-+0-9.eE]*")


def sdf_triple_max(text):
    """The `max` field of a `min:typ:max` triple (`D49f`). Missing -> 0.0."""
    text = text.strip().strip("()").strip()
    m = TRIPLE_RE.search(text)
    if m:
        field = m.group(0).split(":")[2]
    else:
        field = text
    return float(field) if field.strip() else 0.0


def norm_pin(name):
    """Canonical pin name: `DO[0]` and `DO0` are the same physical arc.

    The vendor SDF names a Verilog port bit `DO[0]`; nextpnr's cell variants
    name the same bit `DO0` (`gowin_arch_gen.py`), while `RAM16SDP4` uses the
    bracketed form on both sides. Stripping the brackets makes the two
    namespaces comparable without inventing any mapping (`P0.T37`).
    """
    return re.sub(r"\[(\d+)\]", r"\1", name.strip())


def read_sdf(path):
    """Return `(arcs, condition_line, timescale_ns)`.

    `arcs` is a list of `(celltype, instance, from_pin, to_pin, ns)`; the value
    is the largest `max` field among the IOPATH's delay triples.
    """
    text = open(path).read()
    # `(CELL ` starts a cell block; `(CELLTYPE` must not be mistaken for one.
    cell_split = re.compile(r"\(CELL\b(?!TYPE)")
    head = cell_split.split(text, 1)[0]
    # `D49f` wants the corner, and a real Gowin SDF spreads it over three
    # header lines (VOLTAGE / PROCESS / TEMPERATURE). `V12a` allows exactly
    # one condition line, so they are joined -- each verbatim, in file order.
    parts = [line.strip() for line in head.splitlines()
             if CONDITION_RE.search(line)]
    condition = " ".join(parts) if parts else None
    ts = 1.0
    m = re.search(r"\(TIMESCALE\s+([0-9.]*)\s*(ps|ns)\s*\)", text)
    if m:
        ts = (float(m.group(1) or 1)) * (0.001 if m.group(2) == "ps" else 1.0)

    arcs = []
    for chunk in cell_split.split(text)[1:]:
        ct = re.search(r'\(CELLTYPE\s+"([^"]+)"\)', chunk)
        inst = re.search(r"\(INSTANCE\s+([^\)\s]*)\s*\)", chunk)
        cell = ct.group(1) if ct else "?"
        instance = (inst.group(1) if inst else "") or "top"
        for io in re.finditer(r"\(IOPATH\s+(\S+)\s+(\S+)\s+(.*)", chunk):
            frm, to, rest = io.group(1), io.group(2), io.group(3)
            triples = re.findall(r"\(([^()]*:[^()]*)\)", rest)
            if not triples:
                continue
            ns = max(sdf_triple_max(t) for t in triples) * ts
            arcs.append((cell, instance, frm, to, ns))
    return arcs, condition, ts


# --------------------------------------------------------------------------
# 4. band mode (`--sdf`) -- the V12a stdout contract
# --------------------------------------------------------------------------
def band_mode(timing, sdf_path, grade, out):
    sdf_arcs, condition, _ts = read_sdf(sdf_path)
    if condition is None:
        print(f"L0 FAIL: no operating-condition line in {sdf_path} header "
              f"(D49f requires it recorded)", file=out)
        return 2
    model, _pips, _consumed, _handled, err = record_emission(timing)
    if err:
        print(f"L0 FAIL: cannot read nextpnr's emitted arcs: {err}", file=out)
        return 2

    # index the model on normalised pin names (`P0.T37`: SDF `DO[0]` vs
    # nextpnr `DO0` are the same arc)
    norm_model = {(g, c, norm_pin(f), norm_pin(t)): v
                  for (g, c, f, t), v in model.items()}
    compared, exceptions, unmapped = [], [], []
    for cell, inst, frm, to, ns in sdf_arcs:
        key = (grade, cell, norm_pin(frm), norm_pin(to))
        if key not in norm_model:
            unmapped.append(f"{cell}/{inst} {frm}->{to}")
            continue
        m = norm_model[key]
        dev = (m - ns) / ns if ns else (0.0 if m == 0 else 1.0)
        compared.append((cell, inst, frm, to, m, ns, dev))
        if abs(dev) > BAND:
            exceptions.append((cell, inst, frm, to, m, ns, dev))

    n = len(compared)
    ok = n - len(exceptions)
    print(f"L0 ok: {ok}/{n} arcs within ±{int(BAND * 100)}%, "
          f"{len(exceptions)} exceptions listed", file=out)
    print(condition, file=out)
    print(f"grade: {grade} -- {GRADE_PROVENANCE.get(grade, 'unknown provenance')}",
          file=out)
    for cell, inst, frm, to, m, ns, dev in exceptions:
        print(f"exception: {cell}/{inst} {frm}->{to} model={m:.3f}ns "
              f"sdf={ns:.3f}ns dev={dev * 100:+.1f}%", file=out)
    if unmapped:
        print(f"unmapped: {len(unmapped)} SDF arcs have no nextpnr model arc: "
              + ", ".join(unmapped[:10])
              + (" ..." if len(unmapped) > 10 else ""), file=out)
    return 1 if exceptions else 0


# --------------------------------------------------------------------------
# 5. inventory mode (no `--sdf`) -- the chipdb-side measurement
# --------------------------------------------------------------------------
def provenance(grade):
    return GRADE_PROVENANCE.get(grade, UNIDENTIFIED_PROVENANCE)


def inventory_mode(timing, classes, chipdb_path, out):
    failures = []
    grades = sorted(timing.keys())
    print(f"L0 inventory: chipdb {os.path.basename(chipdb_path)}", file=out)
    print("grades: " + "; ".join(f"{g} = {provenance(g)}" for g in grades), file=out)
    print("", file=out)
    print(f"{'class':5} {'group':8} {'grade':15} {'arcs':>5} "
          f"{'min':>8} {'median':>8} {'max':>8}   (ns)", file=out)

    for cls in classes:
        groups = CLASS_GROUPS[cls]
        per_group = class_arcs(timing, groups)
        for group, required in groups.items():
            per_grade = per_group.get(group, {})
            if not any(per_grade.values()):
                mark = "missing" if required else "absent (supporting group)"
                print(f"{cls:5} {group:8} {'-':15} {0:5}   {mark}", file=out)
                if required:
                    failures.append(f"required class group {cls}/{group} has 0 arcs")
                continue
            for grade in grades:
                vals = sorted(per_grade.get(grade, {}).values())
                if not vals:
                    continue
                print(f"{cls:5} {group:8} {grade:15} {len(vals):5} "
                      f"{min(vals):8.3f} {statistics.median(vals):8.3f} "
                      f"{max(vals):8.3f}", file=out)

    # --- C1/I0 : C2/I1 ratio band (derived by construction, P0.T35) ---
    print("", file=out)
    ratios = []
    for cls in classes:
        for group in CLASS_GROUPS[cls]:
            a = timing.get("C1/I0", {}).get(group, {})
            b = timing.get("C2/I1", {}).get(group, {})
            for key in a:
                va, vb = arc_max(a[key]), arc_max(b.get(key))
                if va is None or not vb:
                    continue
                ratios.append((va / vb, f"{group}/{key}"))
    if not ratios:
        print("ratio C1/I0 : C2/I1 -- no comparable arcs (both grades needed)",
              file=out)
        if any(CLASS_GROUPS[c] for c in classes):
            failures.append("no C1/I0 : C2/I1 ratio could be computed")
    else:
        vals = [r for r, _ in ratios]
        bad = [(r, k) for r, k in ratios if not RATIO_BAND[0] <= r <= RATIO_BAND[1]]
        status = "FAIL" if bad else "ok"
        print(f"ratio C1/I0 : C2/I1: n={len(vals)} min={min(vals):.3f} "
              f"median={statistics.median(vals):.3f} max={max(vals):.3f} "
              f"band=[{RATIO_BAND[0]},{RATIO_BAND[1]}] expect={DERIVED_RATIO} "
              f"status: {status} -- DERIVED, not measured "
              f"(P0.T35, apicula/doc/timing-c1i0.md)", file=out)
        for r, k in bad[:10]:
            print(f"ratio exception: {k} = {r:.3f}", file=out)
        if bad:
            failures.append(f"{len(bad)} arcs outside the C1/I0 ratio band")

    # --- what nextpnr emits vs what the chipdb holds ---
    print("", file=out)
    arcs, pips, consumed, handled, err = record_emission(timing)
    if err:
        print(f"nextpnr emission: UNAVAILABLE ({err})", file=out)
        failures.append("nextpnr emission could not be recorded")
    else:
        chipdb_groups = sorted({g for gg in timing.values() for g in gg})
        never = [g for g in chipdb_groups if g not in handled]
        print(f"nextpnr emission (gowin_arch_gen.py create_timing_info): "
              f"{len(arcs)} cell arcs, {len(pips)} pip classes, "
              f"{len(handled)} groups handled", file=out)
        print("chipdb groups nextpnr never emits: "
              + (", ".join(never) if never else "none"), file=out)
        gaps = []
        for group in sorted(chipdb_groups):
            keys = {k for gg in timing.values() for k in gg.get(group, {})}
            missed = sorted(keys - consumed.get(group, set()))
            if missed:
                gaps.append(f"{group}: " + ", ".join(missed))
        print(f"unconsumed chipdb arc keys ({sum(len(g.split(',')) for g in gaps)} "
              f"across {len(gaps)} groups):", file=out)
        for line in gaps:
            print(f"  gap: {line}", file=out)
        if not gaps:
            print("  gap: none", file=out)

    print("", file=out)
    required_total = sum(1 for c in classes for g, r in CLASS_GROUPS[c].items() if r)
    if failures:
        print(f"L0 INVENTORY FAIL: " + "; ".join(failures), file=out)
        return 1
    print(f"L0 INVENTORY ok: {required_total}/{required_total} required groups "
          f"populated, {len(grades)} grades, ratio band ok", file=out)
    return 0


# --------------------------------------------------------------------------
# 6. CLI
# --------------------------------------------------------------------------
def main(argv=None, out=None):
    out = out or sys.stdout
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--classes", required=True,
                    choices=list(ALL_CLASSES) + ["all"])
    ap.add_argument("--sdf", help="vendor .sdf (-device_version C, worst case). "
                                  "Omit for the chipdb-side inventory.")
    ap.add_argument("--chipdb", required=True,
                    help="apicula chipdb (.msgpack.xz), or a .json timing dict")
    ap.add_argument("--grade", default="C1/I0",
                    help="speed grade to compare in band mode (default C1/I0, "
                         "the part's own grade -- DERIVED, see P0.T35)")
    args = ap.parse_args(argv)

    if args.classes == "all":
        classes = [c for c in ALL_CLASSES if c in LIVE_CLASSES]
    elif args.classes not in LIVE_CLASSES:
        print(f"L0 skipped: class {args.classes} has no arcs yet", file=out)
        return 0
    else:
        classes = [args.classes]

    timing = load_timing(args.chipdb)
    if args.sdf:
        return band_mode(timing, args.sdf, args.grade, out)
    return inventory_mode(timing, classes, args.chipdb, out)


if __name__ == "__main__":
    sys.exit(main())
