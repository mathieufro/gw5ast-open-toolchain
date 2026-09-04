#!/usr/bin/env python3
"""`P0.T31` -- the DONE-STD criteria checker (`DEL-e` first cut, `D63`, `D42`).

Reads `spec-primitives.md`'s per-primitive table, and for each row asks
whether the evidence directory (`$PIPE/evidence/`) proves DONE-STD
(`spec-primitives.md` "DONE-STD" note, clauses a-e):

    (a) instantiates on the device without error
    (b) the swept set is E1-equivalent (or E0 + recorded reason)
    (c) the decode check (c1 and c2) passes
    (d) a gate example exists and runs in the local blocking gate
        -- disabled before Phase 7 (`D65`); see `--enable-clause-d`
    (e) the evidence directory is populated

A row whose evidence shows `verdict: refused` is exempt from clauses (b)
and (d) by construction (`spec-primitives.md`, "Clauses (b) and (d) do not
apply..."): it only needs the exact error text recorded (clause a/c's
"definitive result") and a populated evidence directory (clause e).

Stdout contract (exact): `CRITERIA ok: <n>/<n>`.

Scoping (mandatory, `F8`):
  - unscoped (no `--rows`, no `--phase`): a SURVEY. Reports satisfied/total
    over the whole table, lists every unmet row as `pending: <id>`, and
    always exits 0 -- a partial table is expected before the epic closes.
  - scoped (`--rows` and/or `--phase`): an ASSERTION. Every named row must
    be satisfied; an unmet one is a failure, reported as
    `CRITERIA FAIL: unmet rows: <id>[, <id>...]` and a non-zero exit.

`--phase <n>` resolves to the rows `spec-primitives.md`'s own `Phase`
column attributes to phase `<n>` (values may be bare ints or `5a`/`5b`
strings) -- so `--phase <n>` is exactly equivalent to passing that same
row-id set to `--rows`. Until a `Phase` column exists in the table (it is
an owed amendment, `spec.md` F31/2135), `--phase` resolves to the empty
set for every value, which is a vacuous (0/0, exit 0) assertion rather
than an error -- the tool must not crash while the table is still partial.

Every phase's `V14`/`V18` runs the scoped form (`--phase <n>`): an
unscoped run cannot assert anything about "this phase is done" because no
phase closes the whole table (`spec.md` V14).

There is no `--chipdb` flag: this tool never touches a chipdb, only
`spec-primitives.md` and the evidence tree.
"""
import argparse
import json
import os
import re
import sys

CLAUSE_D_DEFERRED_LINE = "clause-d: deferred to Phase 7 (D65)"
CLAUSE_D_GATE_MARKER = "GATE:PASS"

REFUSED = "refused"
OK = "ok"
E_LEVELS_FULL = ("E1", "E2")


# --------------------------------------------------------------------------
# 1. spec-primitives.md parsing
# --------------------------------------------------------------------------
class Row:
    __slots__ = ("id", "phase", "evidence_slug", "raw")

    def __init__(self, id_, phase, evidence_slug, raw):
        self.id = id_
        self.phase = phase
        self.evidence_slug = evidence_slug
        self.raw = raw

    def __repr__(self):
        return f"Row({self.id!r}, phase={self.phase!r})"


def _split_row(line):
    """Split one `| a | b | c |` markdown table line into stripped cells."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _is_separator(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip())


def _clean_id(cell):
    """The primitive id: the bold span in column 1, else the whole cell."""
    m = re.match(r"\*\*([^*]+)\*\*", cell.strip())
    text = m.group(1) if m else cell.strip()
    # Drop a trailing parenthetical, e.g. "OSC (on-chip oscillator)".
    text = re.sub(r"\s*\(.*\)\s*$", "", text).strip()
    return text


def _clean_slug(cell):
    """`` `evidence/plla/` `` -> `plla`."""
    m = re.search(r"evidence/([A-Za-z0-9_.-]+)/?", cell)
    return m.group(1) if m else None


def parse_spec_primitives(path):
    """Every data row of every table in `spec-primitives.md`, as `Row`s.

    Tolerant by design: tables vary their non-id columns across sections
    (`25A status` vs `Family status`), and a `Phase` column may not exist
    yet (F31/2135) -- both are handled, not assumed.
    """
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    rows = []
    header = None
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if not line.strip().startswith("|"):
            header = None
            continue
        cells = _split_row(line)
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if _is_separator(cells):
            continue
        if len(cells) != len(header):
            # A malformed/continuation line -- not a data row we can trust.
            continue
        if cells[0].lower() == header[0]:
            continue  # a repeated header row (spec-primitives.md has five)
        row_id = _clean_id(cells[0])
        if not row_id or row_id in ("-", "—"):
            continue
        phase = None
        evidence_slug = None
        by_col = dict(zip(header, cells))
        for key, value in by_col.items():
            if key == "phase":
                phase = value.strip() or None
            if "evidence" in key:
                evidence_slug = _clean_slug(value)
        rows.append(Row(row_id, phase, evidence_slug, by_col))
    return rows


# --------------------------------------------------------------------------
# 2. Evidence
# --------------------------------------------------------------------------
def _read_jsonl(path):
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def load_evidence(evidence_dir):
    """Every evidence row under `evidence_dir`, from every `<slug>/runs.jsonl`."""
    rows = []
    if not os.path.isdir(evidence_dir):
        return rows
    for slug in sorted(os.listdir(evidence_dir)):
        slug_dir = os.path.join(evidence_dir, slug)
        jsonl = os.path.join(slug_dir, "runs.jsonl")
        for r in _read_jsonl(jsonl):
            r = dict(r)
            r["_slug"] = slug
            rows.append(r)
    return rows


def rows_for_primitive(evidence_rows, primitive_id, slug=None):
    matches = [
        r for r in evidence_rows
        if str(r.get("primitive", "")).strip().lower() == primitive_id.lower()
    ]
    if slug:
        scoped = [r for r in matches if r.get("_slug") == slug]
        if scoped:
            return scoped
    return matches


def evidence_dir_populated(evidence_dir, slug, primitive_id, evidence_rows):
    if slug:
        slug_dir = os.path.join(evidence_dir, slug)
        if os.path.isdir(slug_dir):
            for name in ("runs.jsonl", "summary.md"):
                p = os.path.join(slug_dir, name)
                if os.path.isfile(p) and os.path.getsize(p) > 0:
                    return True
    return bool(rows_for_primitive(evidence_rows, primitive_id, slug))


# --------------------------------------------------------------------------
# 3. DONE-STD evaluation
# --------------------------------------------------------------------------
def _decode_ok(evrow):
    dc = evrow.get("decode_check") or {}
    return dc.get("c1") == OK and dc.get("c2") == OK


def evaluate_row(row, evidence_rows, evidence_dir, enable_clause_d):
    """Return `(satisfied, reason, deferred_clause_d)` for one `Row`.

    `deferred_clause_d` is True when the row was accepted only because
    clause (d) was skipped (the default before Phase 7, `D65`) -- i.e. its
    satisfying evidence row lacks the gate marker and would fail if
    `--enable-clause-d` were passed. It is always False when the row fails
    outright or does not depend on the deferral.
    """
    matches = rows_for_primitive(evidence_rows, row.id, row.evidence_slug)
    if not matches:
        return False, "no evidence rows", False

    populated = evidence_dir_populated(
        evidence_dir, row.evidence_slug, row.id, evidence_rows)
    if not populated:
        return False, "evidence directory not populated (clause e)", False

    for evrow in matches:
        verdict = evrow.get("verdict")
        notes = str(evrow.get("notes") or "")

        if verdict == REFUSED:
            # (b), (d) exempted by construction; (a)/(c) reduce to "the
            # refusal itself is the definitive, recorded result".
            if notes.strip():
                return True, "refused (exempt from b, d)", False
            continue

        if verdict != OK:
            continue  # diff/aborted rows are not a satisfying result

        level_ok = evrow.get("level") in E_LEVELS_FULL
        if not level_ok and evrow.get("level") == "E0":
            # E0 + recorded reason is an accepted clause-(b) alternative.
            level_ok = bool(notes.strip())
        if not level_ok:
            continue

        if not _decode_ok(evrow):
            continue  # clause (c)

        marker_present = CLAUSE_D_GATE_MARKER in notes
        if enable_clause_d:
            if not marker_present:
                continue  # clause (d), enforced and unmet -- try next row
            return True, "ok", False

        return True, "ok", not marker_present

    return False, "no evidence row satisfies DONE-STD for this scope", False


# --------------------------------------------------------------------------
# 4. Scoping
# --------------------------------------------------------------------------
def resolve_rows(all_rows, row_ids=None, phase=None):
    """The rows named by `--rows`/`--phase`, or `None` for "unscoped"."""
    if row_ids is None and phase is None:
        return None
    by_id = {r.id: r for r in all_rows}
    selected = []
    if row_ids is not None:
        for rid in row_ids:
            r = by_id.get(rid)
            if r is not None and r not in selected:
                selected.append(r)
    if phase is not None:
        phase_str = str(phase)
        for r in all_rows:
            if r.phase is not None and str(r.phase) == phase_str and r not in selected:
                selected.append(r)
    return selected


# --------------------------------------------------------------------------
# 5. CLI
# --------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        prog="check_criteria.py",
        description=(
            "DONE-STD criteria checker (DEL-e first cut, D63/D42). "
            "Unscoped run = survey (always exits 0). "
            "Scoped run (--rows/--phase) = assertion (exits non-zero on an "
            "unmet row). Every phase's V14/V18 runs the scoped form "
            "(--phase <n>). There is no --chipdb flag."))
    p.add_argument("spec_primitives", help="path to spec-primitives.md")
    p.add_argument("evidence_dir", help="path to the evidence/ directory")
    p.add_argument("--rows", help="comma-separated row ids to assert")
    p.add_argument("--phase", help="phase value to assert (e.g. 0, 5a, 5b)")
    p.add_argument(
        "--enable-clause-d", action="store_true",
        help=(
            "Enforce DONE-STD clause (d) (the gate example). Off by "
            "default before Phase 7 (D65); the off path prints "
            f"'{CLAUSE_D_DEFERRED_LINE}' once per invocation."))
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    all_rows = parse_spec_primitives(args.spec_primitives)
    evidence_rows = load_evidence(args.evidence_dir)

    row_ids = None
    if args.rows:
        row_ids = [x.strip() for x in args.rows.split(",") if x.strip()]

    scoped_rows = resolve_rows(all_rows, row_ids=row_ids, phase=args.phase)
    is_scoped = scoped_rows is not None
    target_rows = scoped_rows if is_scoped else all_rows

    satisfied, unmet = [], []
    any_deferred = False
    for row in target_rows:
        ok, _reason, deferred = evaluate_row(
            row, evidence_rows, args.evidence_dir, args.enable_clause_d)
        (satisfied if ok else unmet).append(row)
        any_deferred = any_deferred or deferred

    if not args.enable_clause_d and any_deferred:
        print(CLAUSE_D_DEFERRED_LINE)

    n_ok, n_total = len(satisfied), len(target_rows)
    print(f"CRITERIA ok: {n_ok}/{n_total}")

    if not is_scoped:
        for row in unmet:
            print(f"pending: {row.id}")
        return 0

    if unmet:
        names = ", ".join(row.id for row in unmet)
        print(f"CRITERIA FAIL: unmet rows: {names}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
