#!/usr/bin/env python3
"""`P0.T31` -- the DONE-STD criteria checker (`DEL-e` first cut, `D63`, `D42`).

Reads `spec-primitives.md`'s per-primitive table, and for each row asks
whether the evidence directory (`$OTC/evidence/`) proves DONE-STD
(`spec-primitives.md` "DONE-STD" note, clauses a-e):

    (a) instantiates on the device without error
    (b) the swept set is E1-equivalent (or E0 + recorded reason)
    (c) the decode check (c1 and c2) passes
    (d) a gate example exists and runs in the local blocking gate
        -- disabled before Phase 7 (`D65`); see `--enable-clause-d`
    (e) the evidence directory is populated

A row **declared** `refused:<error>` in its `138C status` cell is exempt
from clauses (b) and (d) by construction (`spec-primitives.md`, "Clauses (b)
and (d) do not apply to a row closing as `refused:<error>`"): it only needs
the exact error text recorded (clause a/c's "definitive result") and a
populated evidence directory (clause e).  The exemption is a property of the
declared status, never of an individual evidence row's verdict -- a refusal
is an ordinary measurement, and a sweep that contains one buys nothing.
Symmetrically, a row declared at an equivalence level is satisfied only by
evidence rows **at that level or stronger**: a row declaring `E1` is not
proven by its own `E0` rows.

Stdout contract (exact): `CRITERIA ok: <n>/<n>`.

**`D90` (gestalt `G6`).** A scoped run (`--phase <n>`) additionally asserts
the phase's own ledger, `<evidence>/phase<n>/phase-report.md`: every
criterion that report marks `REACHED` must be **backed** by at least one
evidence row, linked through the evidence slug that claims that criterion in
its own markdown (`summary.md` and siblings).  A criterion whose claiming
slugs carry zero rows fails the run; a criterion no slug claims is printed
as `unlinked:` and counted (a phase's tooling/hygiene criteria are proven by
tests, not by `runs.jsonl` rows).  `CRITERIA ok: 0/0` is no longer a pass:
a scoped run that examined nothing is a vacuous assertion and fails.

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

#: Equivalence levels in ascending strength.  A row declared at one level is
#: satisfied by an evidence row at that level or a stronger one, never by a
#: weaker one -- that is clause (b) read as the table declares it.
E_LEVEL_ORDER = ("E0", "E1", "E2")

#: The declared-status vocabulary of `spec-primitives.md` ("Status vocabulary
#: for the filled-in table"), longest spelling first so `E0+hw-pending` is not
#: read as `E0`.
_STATUS_TOKEN_RE = re.compile(
    r"^[\s*`]*(E0\+hw-pending|E0\+hw|E0|E1|E2|refused|blocked|open)\b",
    re.IGNORECASE)


# --------------------------------------------------------------------------
# 1. spec-primitives.md parsing
# --------------------------------------------------------------------------
class Row:
    __slots__ = ("id", "phase", "status", "evidence_slug", "raw")

    def __init__(self, id_, phase, status, evidence_slug, raw):
        self.id = id_
        self.phase = phase
        #: the primitive's DECLARED status, from the `138C status` column
        #: (`E1`, `E0+hw-pending`, `refused:<error>`, ...).  DONE-STD is
        #: keyed on this, never on an individual evidence row's verdict.
        self.status = status
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


def _clean_status(cell):
    """The declared status token of a `138C status` cell, lowercased.

    `` `E0+hw-pending` -- (rows...) `` -> `e0+hw-pending`; a prose cell
    (`not present`, `untriaged`) has no token and returns None, which means
    "this row declares no level" rather than "E0".
    """
    m = _STATUS_TOKEN_RE.match(cell or "")
    return m.group(1).lower() if m else None


def declared_level(status):
    """The equivalence level a declared status commits to, or None."""
    if not status:
        return None
    head = status.split("+", 1)[0].upper()
    return head if head in E_LEVEL_ORDER else None


def _levels_at_or_above(level):
    return E_LEVEL_ORDER[E_LEVEL_ORDER.index(level):]


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
        status = None
        evidence_slug = None
        by_col = dict(zip(header, cells))
        for key, value in by_col.items():
            if key == "phase":
                phase = value.strip() or None
            if key.endswith("status") and not key.startswith(("25a", "family")):
                status = _clean_status(value)
            if "evidence" in key:
                evidence_slug = _clean_slug(value)
        rows.append(Row(row_id, phase, status, evidence_slug, by_col))
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

    # DONE-STD is keyed on the primitive's DECLARED status, never on an
    # individual evidence row's verdict: the `refused` exemption belongs to a
    # primitive that *closes* as `refused:<error>`, and a primitive declared at
    # a level is proven only by rows at that level or stronger.  A sweep that
    # merely happens to contain one refused oracle run buys no exemption.
    status = row.status or ""
    is_declared_refused = status.startswith(REFUSED)
    want_level = declared_level(status)
    admissible = _levels_at_or_above(want_level) if want_level else None

    for evrow in matches:
        verdict = evrow.get("verdict")
        notes = str(evrow.get("notes") or "")

        if verdict == REFUSED:
            # (b), (d) exempted by construction; (a)/(c) reduce to "the
            # refusal itself is the definitive, recorded result" -- but only
            # for a row that declares itself refused.
            if is_declared_refused and notes.strip():
                return True, "refused (exempt from b, d)", False
            continue

        if verdict != OK:
            continue  # diff/aborted rows are not a satisfying result

        level = evrow.get("level")
        if admissible is not None and level not in admissible:
            continue  # clause (b), against the level the table declares

        level_ok = level in E_LEVELS_FULL
        if not level_ok and level == "E0":
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

    if is_declared_refused:
        return False, "declared refused, but no refused row records the error", False
    if want_level:
        return False, (f"no {want_level} evidence row satisfies DONE-STD for "
                       f"this scope"), False
    return False, "no evidence row satisfies DONE-STD for this scope", False


# --------------------------------------------------------------------------
# 3b. The phase report (`D90`, gestalt `G6`)
# --------------------------------------------------------------------------
#: `<evidence>/phase<N>/phase-report.md` -- the ledger a phase closes on.
PHASE_REPORT_NAME = "phase-report.md"

#: `REACHED` in a verdict cell, but never `NOT REACHED`.
_REACHED_RE = re.compile(r"(?<!NOT )\bREACHED\b")

#: A criterion id (`S1`, `S6b`, `S17a`) as a standalone token.  `S0->O` and
#: `.../S3` (an SDF pin, a path) are not criterion references.
_CRITERION_ID_RE = re.compile(r"(?<![\w/\\])(S\d+[a-z]?)\b(?!\s*->)")

#: Evidence-tree directories that are never a slug: the raw-log drop
#: (`_runs`) and the phase-report directories themselves.
_NON_SLUG_RE = re.compile(r"^(_.*|phase\d+[a-z]?)$")


class Criterion:
    __slots__ = ("id", "text")

    def __init__(self, id_, text):
        self.id = id_
        self.text = text

    def __repr__(self):
        return f"Criterion({self.id!r})"


def phase_report_path(evidence_dir, phase):
    """`<evidence>/phase<N>/phase-report.md`, or None when there is none."""
    if not evidence_dir or phase is None:
        return None
    candidate = os.path.join(evidence_dir, f"phase{phase}", PHASE_REPORT_NAME)
    return candidate if os.path.isfile(candidate) else None


def parse_phase_report(path):
    """The criteria the phase report marks **REACHED**, in table order.

    One `Criterion` per markdown table row whose last cell says `REACHED`
    (and not `NOT REACHED`).  The id is the first criterion token in the
    row's first cell (`S5`, `S17a`), else the cleaned first cell itself --
    a phase report also carries `entry:` and `standing:` rows that have no
    `S`-id and are still criteria.
    """
    criteria = []
    if not path or not os.path.isfile(path):
        return criteria
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    header = None
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip().startswith("|"):
            header = None
            continue
        cells = _split_row(line)
        if header is None:
            header = cells
            continue
        if _is_separator(cells):
            continue
        if len(cells) < 2:
            continue
        verdict_cell = cells[-1]
        if not _REACHED_RE.search(verdict_cell):
            continue
        first = cells[0]
        m = _CRITERION_ID_RE.search(first.replace("`", ""))
        cid = m.group(1) if m else re.sub(r"[`*]", "", first).strip()
        if not cid:
            continue
        criteria.append(Criterion(cid, line))
    return criteria


def _slug_dirs(evidence_dir):
    if not evidence_dir or not os.path.isdir(evidence_dir):
        return []
    return [name for name in sorted(os.listdir(evidence_dir))
            if os.path.isdir(os.path.join(evidence_dir, name))
            and not _NON_SLUG_RE.match(name)]


def slug_claims(evidence_dir):
    """`{slug: {criterion id, ...}}` -- which criteria each slug claims.

    A slug claims a criterion by naming it in one of its own markdown
    documents (`summary.md` and its siblings): that is the link between a
    phase report's `REACHED` line and the rows that are supposed to back it,
    and it is data already in the tree rather than a second ledger.
    """
    claims = {}
    for slug in _slug_dirs(evidence_dir):
        slug_dir = os.path.join(evidence_dir, slug)
        ids = set()
        for name in sorted(os.listdir(slug_dir)):
            if not name.endswith(".md"):
                continue
            try:
                with open(os.path.join(slug_dir, name), encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            ids.update(_CRITERION_ID_RE.findall(text))
        claims[slug] = ids
    return claims


def slug_row_counts(evidence_rows, evidence_dir):
    """`{slug: n rows}` for every slug directory, zero-filled."""
    counts = {slug: 0 for slug in _slug_dirs(evidence_dir)}
    for row in evidence_rows:
        slug = row.get("_slug")
        if slug in counts:
            counts[slug] += 1
    return counts


def check_phase_report(report_path, evidence_rows, evidence_dir):
    """`(criteria, backed, unlinked, findings)` for one phase report.

    A criterion marked `REACHED` must be **backed**: at least one evidence
    slug that claims it carries at least one evidence row.  A criterion no
    slug claims at all is `unlinked` -- reported, counted, not fatal: a
    phase's tooling and hygiene criteria (`the local gate is blocking`,
    `forks are submodules`) are proven by tests, not by `runs.jsonl` rows.
    A criterion whose claiming slugs carry **zero** rows is the vacuous
    case `D90` exists to stop, and is a hard failure.
    """
    criteria = parse_phase_report(report_path)
    claims = slug_claims(evidence_dir)
    counts = slug_row_counts(evidence_rows, evidence_dir)

    backed, unlinked, findings = [], [], []
    for crit in criteria:
        claiming = sorted(slug for slug, ids in claims.items()
                          if crit.id in ids)
        if not claiming:
            unlinked.append(crit)
            continue
        if any(counts.get(slug, 0) > 0 for slug in claiming):
            backed.append(crit)
            continue
        findings.append(
            f"unbacked REACHED: {crit.id} is marked REACHED but the only "
            f"evidence slug(s) claiming it ({', '.join(claiming)}) carry 0 "
            f"evidence rows (D90)")
    return criteria, backed, unlinked, findings


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
        "--phase-report", default=None,
        help=("Path to the phase report to assert against (default: "
              "<evidence>/phase<N>/phase-report.md). Every criterion it "
              "marks REACHED must be backed by an evidence row (D90)."))
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

    # `D90`/`G6`: a scoped run also asserts the phase report's own ledger.
    report_path = args.phase_report or phase_report_path(
        args.evidence_dir, args.phase)
    report_findings = []
    n_reached = n_backed = n_unlinked = 0
    if is_scoped and report_path:
        criteria, backed, unlinked, report_findings = check_phase_report(
            report_path, evidence_rows, args.evidence_dir)
        n_reached, n_backed, n_unlinked = len(criteria), len(backed), len(unlinked)
        print(f"PHASE-REPORT {os.path.relpath(report_path, args.evidence_dir)}: "
              f"{n_reached} REACHED, {n_backed} backed, {n_unlinked} unlinked, "
              f"{len(report_findings)} unbacked")
        for crit in unlinked:
            print(f"unlinked: {crit.id} (no evidence slug claims it)")

    if not args.enable_clause_d and any_deferred:
        print(CLAUSE_D_DEFERRED_LINE)

    n_ok = len(satisfied) + n_backed + n_unlinked
    n_total = len(target_rows) + n_reached
    print(f"CRITERIA ok: {n_ok}/{n_total}")

    if not is_scoped:
        for row in unmet:
            print(f"pending: {row.id}")
        return 0

    if n_total == 0:
        # `D90`: an assertion that examined nothing is not a pass.
        print("CRITERIA FAIL: vacuous assertion -- 0 criteria examined "
              "(no spec-primitives.md rows in scope and no phase report "
              "claiming criteria)")
        return 1

    for finding in report_findings:
        print(finding)
    if unmet:
        names = ", ".join(row.id for row in unmet)
        print(f"CRITERIA FAIL: unmet rows: {names}")
    if unmet or report_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
