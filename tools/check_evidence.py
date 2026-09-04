#!/usr/bin/env python3
"""`P0.T30` -- the evidence checker `V9` runs (`DEL-e` first cut, `D63`, `D42`).

**This module is the single owner of `check_evidence.py`'s call shape and of
its stdout contract** (cross-phase `F2`/`F16`); every phase from 1 to 8 quotes
what is written here and invents nothing.

Call shape (`spec.md` F2 reconciliation, `blueprints/P0-foundation.md` P0.T30)::

    python check_evidence.py [<spec-primitives.md>] [<evidence-dir>]
                              [--evidence <dir>] [--slug <name>]...
                              [--exclude-slug <name>]...

- both positionals are optional, defaulting to `$PIPE/spec-primitives.md` and
  `$PIPE/evidence` (`$PIPE` is this script's own grandparent directory --
  never inferred from cwd);
- `--evidence <dir>` is an alternative spelling of the second positional and
  **wins** over it;
- `--slug <name>` is repeatable and additive: with one or more, the run is
  scoped to exactly those slugs (and the `spec-primitives.md` rows they
  carry); with none, the run covers the whole tree;
- `--exclude-slug <name>` is repeatable and removes named slugs from
  whichever set `--slug` (or its absence) produced -- `spec.md` F2.

Stdout contract, exact, two lines on a clean tree, identical in every mode::

    EVIDENCE ok: <n> rows, <p> pending, 0 blank, 0 missing artifacts
    0 admissibility findings

`<n>` counts evidence rows matched to a `spec-primitives.md` primitive within
the active slug scope. `<p>` (`PENDING`) counts primitive rows whose evidence
*directory* does not exist yet -- never a failure, the whole point of
authoring this checker in Phase 0 against a partial table (`D63`). A
directory that exists but carries zero rows is `BLANK` and always fails.  On
failure the first token is `EVIDENCE FAIL:` and every finding is printed, one
per line, before the final counted line (`<k> admissibility findings`).

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

# --------------------------------------------------------------------------
# 0. Locating $PIPE and the apicula checkout (the evidence-row schema lives
#    in the harness, imported rather than re-declared -- one schema, D63).
# --------------------------------------------------------------------------
PIPE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_APICULA_CANDIDATES = [
    os.environ.get("FL_APICULA"),
    "/Users/alex/fine-line/.atelier/worktrees/"
    "2026-09-03-open-toolchain-gw5ast-7e84/apicula",
    "/Users/alex/fine-line/apicula",
    "/Users/alex/fine-line/vendor/apicula",
]


def find_apicula_root():
    """The apicula checkout carrying `fuzz/gw5ast138c/harness/evidence.py`."""
    for candidate in _APICULA_CANDIDATES:
        if not candidate:
            continue
        marker = os.path.join(
            candidate, "fuzz", "gw5ast138c", "harness", "evidence.py")
        if os.path.isfile(marker):
            return candidate
    return None


def load_schema():
    """Import `fuzz.gw5ast138c.harness.evidence`, adding apicula to `sys.path`.

    The venv's editable apicula install only exposes the `apycula` package,
    not `fuzz/` (`fuzz/__init__.py` is not part of the packaged distribution)
    -- so this tool adds the apicula checkout root to `sys.path` itself,
    exactly as `$PIPE/tools/evidence.py` (`P0.T28`'s shim) already does.
    """
    root = find_apicula_root()
    if root is None:
        raise SystemExit(
            "check_evidence.py: no apicula checkout found (tried "
            + ", ".join(c for c in _APICULA_CANDIDATES if c)
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
        if not slug_dir or not os.path.isdir(slug_dir):
            n_pending += 1
            continue

        jsonl_path = os.path.join(slug_dir, "runs.jsonl")
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
            if verdict == "diff" and diff_sum == 0:
                findings.append(
                    f"{prow.id}/{run_id}: verdict 'diff' but diff_count's "
                    f"cells/attrs/conns are all zero")

            if expected_mask_sha256 and row.get("mask_sha256") != expected_mask_sha256:
                findings.append(
                    f"{prow.id}/{run_id}: mask_sha256 {row.get('mask_sha256')!r} "
                    f"does not match the checked-in dontcare.mask "
                    f"({expected_mask_sha256})")

            if _unexplained_bits_unjustified(row.get("unexplained_bits")):
                findings.append(
                    f"{prow.id}/{run_id}: unexplained_bits is non-empty and "
                    f"not fully enumerated/justified (D35)")

            for field in ARTIFACT_FIELDS:
                for entry in _as_path_entries(row.get(field)):
                    path = entry.get("path")
                    if not path:
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
                        help="Path to spec-primitives.md (default: $PIPE/spec-primitives.md).")
    parser.add_argument("evidence_dir", nargs="?", default=None,
                        help="Path to the evidence tree (default: $PIPE/evidence).")
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

    spec_path = args.spec_primitives or os.path.join(PIPE_ROOT, "spec-primitives.md")
    evidence_dir = (args.evidence_opt or args.evidence_dir
                     or os.path.join(PIPE_ROOT, "evidence"))

    schema, apicula_root = load_schema()

    n_rows, n_pending, n_blank, n_missing, findings = check(
        spec_path, evidence_dir, args.slug, args.exclude_slug, schema, apicula_root)

    status = "ok" if not findings else "FAIL"
    print(f"EVIDENCE {status}: {n_rows} rows, {n_pending} pending, "
          f"{n_blank} blank, {n_missing} missing artifacts")
    for finding in findings:
        print(finding)
    print(f"{len(findings)} admissibility findings")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
