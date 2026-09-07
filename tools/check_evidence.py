#!/usr/bin/env python3
"""`P0.T30` -- the evidence checker `V9` runs (`DEL-e` first cut, `D63`, `D42`).

**This module is the single owner of `check_evidence.py`'s call shape and of
its stdout contract** (cross-phase `F2`/`F16`); every phase from 1 to 8 quotes
what is written here and invents nothing.

Call shape (`spec.md` F2 reconciliation, `blueprints/P0-foundation.md` P0.T30)::

    python check_evidence.py [<spec-primitives.md>] [<evidence-dir>]
                              [--evidence <dir>] [--slug <name>]...
                              [--exclude-slug <name>]...

- both positionals are optional, defaulting to this checkout's own
  `spec-primitives.md` (else the pipeline docs dir, `C10`/`D80`, read-only)
  and `$OTC/evidence` (`$OTC` is this script's own grandparent directory --
  never inferred from cwd);
- `--evidence <dir>` is an alternative spelling of the second positional and
  **wins** over it;
- `--slug <name>` is repeatable and additive: with one or more, the run is
  scoped to exactly those slugs (and the `spec-primitives.md` rows they
  carry); with none, the run covers the whole tree;
- `--exclude-slug <name>` is repeatable and removes named slugs from
  whichever set `--slug` (or its absence) produced -- `spec.md` F2.

Stdout contract, on a clean tree, identical in every mode -- one `RUNS` line
per discovered `runs.jsonl`, then the roll-up, then the two contract lines::

    RUNS <slug>/runs.jsonl: <r> rows, <v> valid
    RUNS: <f> files, <r> rows, <v> valid
    EVIDENCE ok: <n> rows, <p> pending, 0 blank, 0 missing artifacts
    0 admissibility findings

**`D90` (gestalt `G6`).** The `spec-primitives.md` walk below can only reach
rows the (still partial) table names, which is how this checker came to pass
vacuously on a tree carrying 24 evidence rows.  So it *also* sweeps **every**
`runs.jsonl` found anywhere under the evidence root -- slugs are discovered by
walking the tree, never listed -- and validates every row against the same
`§6` schema (`fuzz.gw5ast138c.harness.evidence.validate_row`, with the `A12`
additive-field allowance for the `calibration` slug applied by
`validate_row_for_slug`).  A malformed row, a schema-violating row, or a
`runs.jsonl` that exists and yields **zero** valid rows is a failure.

`<n>` counts evidence rows matched to a `spec-primitives.md` primitive within
the active slug scope. `<p>` (`PENDING`) counts primitive rows whose evidence
*directory* does not exist yet, **or** exists only as a pre-measurement
skeleton (no `runs.jsonl` written yet -- `P1.T03`) -- never a failure, the
whole point of authoring this checker in Phase 0 against a partial table
(`D63`), and of a later phase being able to scaffold its evidence
directories ahead of its own oracle runs without tripping the gate. A
directory whose `runs.jsonl` exists and carries rows, none of which are for
this primitive, is `BLANK` and always fails -- that is a real anomaly, not a
scaffold. On failure the first token is `EVIDENCE FAIL:` and every finding is
printed, one per line, before the final counted line (`<k> admissibility
findings`).

It fails on: any `blocked:<row>` status recorded against a primitive in
`spec-primitives.md`'s Done column (an in-flight marker, never terminal --
`D33`); any row whose `runs.jsonl` entry lacks a terminal verdict or fails
`fuzz.gw5ast138c.harness.evidence`'s own `§6` schema (missing/unknown field,
bad `level`/`verdict` enum, an `E0` row with empty `notes`, ...); any row
whose `mask_sha256` does not match the checked-in
`fuzz/gw5ast138c/dontcare.mask`; any row with a non-empty, non-enumerated
(unjustified) `unexplained_bits` (`D35`); any row whose `verdict` is
inconsistent with its `diff_count` (`ok` with a non-zero cells/attrs/conns
delta, or `diff` with an all-zero one -- `pips` is a statistic, never a
verdict term, `D32`); any artefact path that does not resolve on disk or
whose recorded sha256 does not match the file's actual sha256.
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------
# 0. Locating $OTC and the apicula checkout (the evidence-row schema lives
#    in the harness, imported rather than re-declared -- one schema, D63).
# --------------------------------------------------------------------------
from paths import (OTC_ROOT as PIPE_ROOT, apicula_candidates,  # noqa: E402
                   apicula_root as find_apicula_root,
                   default_spec_primitives)


def load_schema():
    """Import `fuzz.gw5ast138c.harness.evidence`, adding apicula to `sys.path`.

    The venv's editable apicula install only exposes the `apycula` package,
    not `fuzz/` (`fuzz/__init__.py` is not part of the packaged distribution)
    -- so this tool adds the apicula checkout root to `sys.path` itself,
    exactly as `$OTC/tools/evidence.py` (`P0.T28`'s shim) already does.
    """
    root = find_apicula_root()
    if root is None:
        raise SystemExit(
            "check_evidence.py: no apicula checkout found (tried "
            + ", ".join(c for c in apicula_candidates() if c)
            + "); cannot import the evidence-row schema")
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from fuzz.gw5ast138c.harness import evidence as schema  # noqa
    except ImportError as exc:
        raise SystemExit(
            f"check_evidence.py: cannot import "
            f"fuzz.gw5ast138c.harness.evidence from {root}: {exc}")
    return schema, root


# --------------------------------------------------------------------------
# 1. spec-primitives.md parsing
# --------------------------------------------------------------------------
class PrimitiveRow:
    __slots__ = ("id", "slug", "done_text")

    def __init__(self, id_, slug, done_text):
        self.id = id_
        self.slug = slug
        self.done_text = done_text


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _is_separator(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip())


def _clean_id(cell):
    """The primitive id: the bold span in column 1, parenthetical dropped."""
    m = re.match(r"\*\*([^*]+)\*\*", cell.strip())
    text = m.group(1) if m else cell.strip()
    text = re.sub(r"\s*\(.*\)\s*$", "", text).strip()
    text = text.strip("`")
    return text


def _clean_slug(cell):
    m = re.search(r"evidence/([A-Za-z0-9_.-]+)/?", cell)
    return m.group(1) if m else None


def parse_spec_primitives(path):
    """Every data row of every table in `spec-primitives.md`, as `PrimitiveRow`s.

    Tolerant by design (`D63`): a missing file, an empty file, or a table
    with no rows all yield an empty list rather than an error -- Phase 0
    runs this checker against a table that is still mostly prose.
    """
    if not path or not os.path.isfile(path):
        return []
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
            continue
        if cells and cells[0].lower() == header[0]:
            continue  # a repeated header row (spec-primitives.md has five)
        row_id = _clean_id(cells[0])
        if not row_id or row_id in ("-", "—", "total"):
            continue
        if row_id.lower() == "total":
            continue
        slug = None
        done_text = ""
        for key, value in zip(header, cells):
            if "evidence" in key:
                slug = _clean_slug(value)
            if key == "done":
                done_text = value
        if slug is None:
            continue  # no evidence column resolved -- not a primitive row
        rows.append(PrimitiveRow(row_id, slug, done_text))
    return rows


_BLOCKED_RE = re.compile(r"\bblocked:\S+")

RUNS_NAME = "runs.jsonl"

#: `spec-harness.md` §6 `A12`: the `calibration` slug's rows carry the §6
#: fields **plus** the ones the calibration blueprint's own tests require --
#: additive, never a violation, and only for that slug.  The harness's
#: `validate_row` has no slug parameter, so the allowance is applied here by
#: dropping the additive keys before delegating: every other rule (missing
#: field, bad enum, `E0` without notes, ...) is still the harness's own.
A12_ADDITIVE_SLUG = "calibration"


#: The fields that make a row a `§6` **run row**: an equivalence result.  A
#: row carrying these is held to the whole `§6` contract.  A row carrying
#: none of them is a *bookkeeping* row -- the chipdb build log, the `D26`
#: budget measurements, an oracle preflight -- which `§6` never described and
#: which must not be judged against a schema it does not claim.
RUN_ROW_MARKERS = ("diff_count", "decode_check")

#: The floor a bookkeeping row must still clear: it is a real, readable
#: record, and it does not *half* claim an equivalence result.
BOOKKEEPING_MIN_FIELDS = 2


def row_kind(row):
    """`"run"` or `"bookkeeping"` -- derived from the row, not the slug."""
    if not isinstance(row, dict):
        return "run"  # not a dict: let the schema say so, loudly
    return "run" if all(k in row for k in RUN_ROW_MARKERS) else "bookkeeping"


def validate_bookkeeping_row(row, schema):
    """The contract for a non-`§6` row (`D90`): readable, honest, falsifiable.

    Not a second schema -- there is no second field list.  A bookkeeping row
    must be a JSON object with at least `BOOKKEEPING_MIN_FIELDS` fields, and
    every `§6` field it *does* carry is held to `§6`'s own vocabulary, taken
    from the schema module rather than restated here.  A row that carries the
    whole equivalence result (`RUN_ROW_MARKERS`) is never routed here: it is
    a run row and answers to the whole of `§6`.
    """
    if not isinstance(row, dict):
        raise schema.EvidenceSchemaError(
            f"evidence row must be a dict, got {type(row)}")
    if len(row) < BOOKKEEPING_MIN_FIELDS:
        raise schema.EvidenceSchemaError(
            f"a bookkeeping row carries {len(row)} field(s); at least "
            f"{BOOKKEEPING_MIN_FIELDS} are needed for it to record anything")
    decode = row.get("decode_check")
    if decode:
        bad = sorted(set(decode) - set(schema.DECODE_KEYS))
        if bad:
            raise schema.EvidenceSchemaError(
                f"decode_check has non-schema key(s): {', '.join(bad)}")
    if "level" in row and row["level"] not in schema.LEVELS:
        raise schema.EvidenceSchemaError(
            f"level {row['level']!r} is not one of {'|'.join(schema.LEVELS)}")
    if "verdict" in row and row["verdict"] not in schema.VERDICTS:
        raise schema.EvidenceSchemaError(
            f"verdict {row['verdict']!r} is not one of "
            f"{'|'.join(schema.VERDICTS)}")
    return row


def validate_row_for_slug(row, slug, schema):
    """Validate one row against the schema its **kind** actually declares.

    A `§6` run row goes to `schema.validate_row` -- the one schema, never
    re-implemented -- with `spec-harness.md` §6 `A12`'s additive-field
    allowance applied for the `calibration` slug.  A bookkeeping row goes to
    `validate_bookkeeping_row`.  Neither path is a warning: both raise.
    """
    if row_kind(row) == "bookkeeping":
        return validate_bookkeeping_row(row, schema)
    if slug == A12_ADDITIVE_SLUG and isinstance(row, dict):
        row = {k: v for k, v in row.items() if k in schema.REQUIRED_FIELDS}
    return schema.validate_row(row)


def discover_runs_files(evidence_dir):
    """Every `runs.jsonl` anywhere under `evidence_dir`, deepest path last.

    Slugs are **discovered**, never listed: a new evidence directory is
    covered by this checker the moment it carries a `runs.jsonl` (`D90`).
    Returns a sorted list of `(relpath, abspath, slug)`, where `slug` is the
    first path component under the evidence root (the file's own directory
    name for a nested layout is kept in `relpath`).
    """
    out = []
    if not evidence_dir or not os.path.isdir(evidence_dir):
        return out
    for dirpath, _dirnames, filenames in os.walk(evidence_dir):
        if RUNS_NAME not in filenames:
            continue
        abspath = os.path.join(dirpath, RUNS_NAME)
        relpath = os.path.relpath(abspath, evidence_dir)
        slug = relpath.split(os.sep)[0]
        out.append((relpath, abspath, slug))
    return sorted(out)


def check_runs_files(evidence_dir, slugs, exclude_slugs, schema):
    """Validate **every** discovered `runs.jsonl`, row by row (`D90`, `G6`).

    Returns `(counts, findings)` where `counts` is a list of
    `(relpath, n_rows, n_valid)`, one entry per file, in path order.  A file
    that exists and yields zero valid rows is a finding: an empty evidence
    file is never evidence.
    """
    include = set(slugs) if slugs else None
    exclude = set(exclude_slugs)

    counts = []
    findings = []
    for relpath, abspath, slug in discover_runs_files(evidence_dir):
        if slug in exclude:
            continue
        if include is not None and slug not in include:
            continue

        n_rows = 0
        n_valid = 0
        with open(abspath, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                n_rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    findings.append(
                        f"{relpath}:{lineno}: not valid JSON Lines: {exc}")
                    continue
                try:
                    validate_row_for_slug(row, slug, schema)
                except schema.EvidenceSchemaError as exc:
                    run_id = (row.get("run_id") if isinstance(row, dict)
                              else None) or "<no run_id>"
                    findings.append(f"{relpath}:{lineno} {run_id}: {exc}")
                    continue
                n_valid += 1

        counts.append((relpath, n_rows, n_valid))
        if n_valid == 0:
            findings.append(
                f"{relpath}: 0 valid evidence rows in a runs.jsonl that "
                f"exists ({n_rows} row(s) read) -- an empty or wholly "
                f"unschema'd evidence file is not evidence (D90)")
    return counts, findings


# --------------------------------------------------------------------------
# 2. Evidence tree
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
            out.append(json.loads(line))
    return out


def _sha256_of(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _as_path_entries(value):
    """Normalise an artefact field to a list of `{"path": ..., "sha256": ...}`."""
    if not value:
        return []
    if isinstance(value, str):
        return [{"path": value}]
    if isinstance(value, dict):
        return [value]
    out = []
    for item in value:
        if isinstance(item, str):
            out.append({"path": item})
        elif isinstance(item, dict):
            out.append(item)
    return out


ARTIFACT_FIELDS = ("oracle_log", "open_log", "vendor_fs", "open_fs", "sdf", "tr")

#: `D99`: an artefact pruned from the datastore is admissible when its row
#: carries `artefact_pruned: true` and the artefact's `path` was rewritten to
#: `sha256:<hex>` (or `sha256:unknown` when no hash was ever recorded) rather
#: than left pointing at a live filesystem path. This is the single
#: definition of that marker shape; `evidence.py`'s own
#: `PRUNED_ARTIFACT_RE` says the same thing for the schema side.
PRUNED_ARTIFACT_RE = re.compile(r"^sha256:([0-9a-f]{64}|unknown)$")


#: A `notes` tail of the shape `<key>=[...]`, JSON-encoded.  Rows carry a few
#: of these beside `extra={...}`; the one below is checked because a string
#: passed where a list of paths was expected is not a type error in Python --
#: it is iterated, and lands in the row as one array element per character.
NOTE_PATH_LIST_RE = re.compile(r"artefact_pruned_paths=(\[[^\]]*\])")


def _pruned_paths_findings(notes):
    """Why this row's `artefact_pruned_paths` tail is not a list of paths."""
    match = NOTE_PATH_LIST_RE.search(notes or "")
    if match is None:
        return []
    try:
        paths = json.loads(match.group(1))
    except ValueError:
        return ["artefact_pruned_paths is not valid JSON"]
    bad = [p for p in paths if not isinstance(p, str) or "/" not in p]
    if bad:
        return [f"artefact_pruned_paths holds {len(bad)} entry/entries that "
                f"are not paths (first {bad[0]!r}) -- a single path string "
                f"iterated character by character has this shape"]
    return []


def _is_justified(item):
    """One `unexplained_bits` entry counts as enumerated only if justified."""
    if isinstance(item, dict):
        return bool(str(item.get("justification") or item.get("reason") or "").strip())
    if isinstance(item, (list, tuple)):
        return len(item) >= 2 and bool(str(item[-1]).strip())
    return False


def _unexplained_bits_unjustified(unexplained_bits):
    """True when the residual is non-empty and not fully enumerated/justified."""
    if not unexplained_bits:
        return False
    if isinstance(unexplained_bits, dict):
        return True  # a raw residual map is never "enumerated" (D35)
    return any(not _is_justified(item) for item in unexplained_bits)


def _diff_count_sum(diff_count):
    if not diff_count:
        return 0
    return sum(int(diff_count.get(k) or 0) for k in ("cells", "attrs", "conns"))


# --------------------------------------------------------------------------
# 3. The check
# --------------------------------------------------------------------------
def check(spec_path, evidence_dir, slugs, exclude_slugs, schema, apicula_root):
    findings = []
    n_rows = 0
    n_pending = 0
    n_blank = 0
    n_missing_artifacts = 0

    primitive_rows = parse_spec_primitives(spec_path)

    include = set(slugs) if slugs else None
    exclude = set(exclude_slugs)

    scoped = []
    for row in primitive_rows:
        if row.slug in exclude:
            continue
        if include is not None and row.slug not in include:
            continue
        scoped.append(row)

    # `mask_sha256` provenance: the checked-in mask, one sha256 for the whole
    # run (`spec-harness.md` §5.3/§6).
    expected_mask_sha256 = None
    if apicula_root:
        mask_path = os.path.join(apicula_root, "fuzz", "gw5ast138c", "dontcare.mask")
        if os.path.isfile(mask_path):
            expected_mask_sha256 = _sha256_of(mask_path)

    for prow in scoped:
        if _BLOCKED_RE.search(prow.done_text or ""):
            findings.append(
                f"{prow.id}: blocked: status in spec-primitives.md is an "
                f"in-flight marker, never terminal (D33): {prow.done_text.strip()!r}")

        slug_dir = os.path.join(evidence_dir, prow.slug) if evidence_dir else None
        jsonl_path = os.path.join(slug_dir, "runs.jsonl") if slug_dir else None
        if not slug_dir or not os.path.isdir(slug_dir) or not os.path.isfile(jsonl_path):
            # P1.T03: a slug directory created ahead of its first oracle run
            # (the evidence *skeleton*: summary.md stub, no runs.jsonl yet --
            # `runs.jsonl` is created lazily by `append_row` on the first
            # real row, same as the harness) is not yet evidence of
            # anything, one way or the other -- indistinguishable in intent
            # from the directory not existing at all, so it is PENDING like
            # any other not-yet-reached primitive, never BLANK. BLANK stays
            # reserved for the real anomaly the D63 note describes: a
            # `runs.jsonl` that exists and carries rows, none of which are
            # for this primitive.
            n_pending += 1
            continue

        try:
            rows = _read_jsonl(jsonl_path)
        except json.JSONDecodeError as exc:
            findings.append(f"{prow.id}: {jsonl_path} is not valid JSON Lines: {exc}")
            continue

        matched = [
            r for r in rows
            if str(r.get("primitive", "")).strip().lower() == prow.id.lower()
        ]
        if not matched:
            n_blank += 1
            findings.append(
                f"{prow.id}: evidence directory {slug_dir} exists but carries "
                f"0 rows for this primitive (BLANK, D63)")
            continue

        for row in matched:
            run_id = row.get("run_id", "<no run_id>")
            try:
                schema.validate_row(row)
            except schema.EvidenceSchemaError as exc:
                findings.append(f"{prow.id}/{run_id}: {exc}")
                continue  # further checks assume a schema-valid row

            verdict = row.get("verdict")
            if verdict not in ("ok", "diff", "aborted", "refused"):
                findings.append(
                    f"{prow.id}/{run_id}: not a terminal verdict: {verdict!r}")
                continue

            diff_sum = _diff_count_sum(row.get("diff_count"))
            if verdict == "ok" and diff_sum != 0:
                findings.append(
                    f"{prow.id}/{run_id}: verdict 'ok' but diff_count has a "
                    f"non-zero cells/attrs/conns delta ({diff_sum})")
            # A `diff` with three clean sets is admissible only when the
            # row names the other verdict term it failed on: the raw residual
            # (`spec-harness.md` 5.1b, D35) or the decode check (5.4, D34).
            # Both are required for a row to close, so neither can be a set
            # difference and neither shows up in `diff_count`.
            decode_failed = any(
                value != "ok"
                for value in (row.get("decode_check") or {}).values())
            if (verdict == "diff" and diff_sum == 0
                    and not row.get("unexplained_bits")
                    and not decode_failed):
                findings.append(
                    f"{prow.id}/{run_id}: verdict 'diff' but diff_count's "
                    f"cells/attrs/conns are all zero, and neither the "
                    f"residual nor the decode check says otherwise")

            # The mask is an input to the E0/E1 comparison, so it is only
            # meaningful on a row whose comparison actually ran. An `aborted`
            # or `refused` row stopped before `equiv` and legitimately carries
            # no mask -- demanding one there turns every recorded refusal into
            # a finding, and a refusal is a deliverable (`spec-harness.md` 6).
            # A *wrong* non-null mask is still caught on every verdict.
            row_mask = row.get("mask_sha256")
            mask_required = verdict in ("ok", "diff")
            if expected_mask_sha256 and (mask_required or row_mask is not None):
                if row_mask != expected_mask_sha256:
                    findings.append(
                        f"{prow.id}/{run_id}: mask_sha256 {row_mask!r} "
                        f"does not match the checked-in dontcare.mask "
                        f"({expected_mask_sha256})")

            if _unexplained_bits_unjustified(row.get("unexplained_bits")):
                findings.append(
                    f"{prow.id}/{run_id}: unexplained_bits is non-empty and "
                    f"not fully enumerated/justified (D35)")

            for why in _pruned_paths_findings(row.get("notes")):
                findings.append(f"{prow.id}/{run_id}: {why}")

            row_pruned = bool(row.get("artefact_pruned"))
            for field in ARTIFACT_FIELDS:
                for entry in _as_path_entries(row.get(field)):
                    path = entry.get("path")
                    if not path:
                        continue
                    if row_pruned and PRUNED_ARTIFACT_RE.match(path):
                        # D99: admissible -- the artefact was pruned from the
                        # datastore and the row records its sha256 (or
                        # "unknown") instead of a live path. Nothing to
                        # resolve on disk and no sha256 to re-check.
                        continue
                    resolved = path if os.path.isabs(path) else os.path.join(slug_dir, path)
                    if not os.path.isfile(resolved):
                        n_missing_artifacts += 1
                        findings.append(
                            f"{prow.id}/{run_id}: {field} artefact does not "
                            f"resolve on disk: {resolved}")
                        continue
                    recorded_sha = entry.get("sha256")
                    if recorded_sha:
                        actual = _sha256_of(resolved)
                        if actual != recorded_sha:
                            n_missing_artifacts += 1
                            findings.append(
                                f"{prow.id}/{run_id}: {field} sha256 mismatch "
                                f"at {resolved} (recorded {recorded_sha}, "
                                f"actual {actual})")

            n_rows += 1

    return n_rows, n_pending, n_blank, n_missing_artifacts, findings


# --------------------------------------------------------------------------
# 4. CLI
# --------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="check_evidence.py",
        description="V9: spec-primitives.md rows vs the evidence tree (DEL-e first cut).")
    parser.add_argument("spec_primitives", nargs="?", default=None,
                        help="Path to spec-primitives.md (default: this "
                             "checkout's own copy, else the pipeline docs dir).")
    parser.add_argument("evidence_dir", nargs="?", default=None,
                        help="Path to the evidence tree (default: $OTC/evidence).")
    parser.add_argument("--evidence", dest="evidence_opt", default=None,
                        help="Alternative spelling of the evidence-dir positional; wins over it.")
    parser.add_argument("--slug", action="append", default=[],
                        help="Scope to this evidence slug; repeatable, additive.")
    parser.add_argument("--exclude-slug", action="append", default=[],
                        help="Remove this slug from the scope; repeatable.")
    return parser


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)

    spec_path = args.spec_primitives or default_spec_primitives()
    evidence_dir = (args.evidence_opt or args.evidence_dir
                     or os.path.join(PIPE_ROOT, "evidence"))

    schema, apicula_root = load_schema()

    n_rows, n_pending, n_blank, n_missing, findings = check(
        spec_path, evidence_dir, args.slug, args.exclude_slug, schema, apicula_root)

    # `D90`/`G6`: the sweep over the tree's own `runs.jsonl` files, which the
    # `spec-primitives.md` walk above cannot reach while the table is partial.
    runs_counts, runs_findings = check_runs_files(
        evidence_dir, args.slug, args.exclude_slug, schema)
    findings = findings + runs_findings

    for relpath, n_file_rows, n_file_valid in runs_counts:
        print(f"RUNS {relpath}: {n_file_rows} rows, {n_file_valid} valid")
    print(f"RUNS: {len(runs_counts)} files, "
          f"{sum(c[1] for c in runs_counts)} rows, "
          f"{sum(c[2] for c in runs_counts)} valid")

    status = "ok" if not findings else "FAIL"
    print(f"EVIDENCE {status}: {n_rows} rows, {n_pending} pending, "
          f"{n_blank} blank, {n_missing} missing artifacts")
    for finding in findings:
        print(finding)
    print(f"{len(findings)} admissibility findings")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
