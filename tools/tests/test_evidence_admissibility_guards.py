"""Guards for the three admissibility defects the Phase-2 close uncovered.

Each test here exists because something real got past the checker once:

1. an evidence row put per-band figures inside `diff_count`, whose keys are
   fixed by `spec-harness.md` §6 -- the row was rejected, but nothing
   stopped a later row from doing the same;
2. an artefact path spelled relative to `$OTC` (`evidence/_runs/<batch>.log`)
   was resolved only against the slug directory, so a log that exists was
   reported missing;
3. the dual-purpose rows recorded the *vehicle's* primitive (`CLKDIV`)
   rather than the primitive under measurement, which made
   `spec-primitives.md`'s Dual-purpose-pins row read `BLANK`;

plus the one that is not a row at all: two `chipdb-GW5AST-138C.bin` files
under the installed nextpnr's share tree, one of them left over from an
earlier build.  A stale database is silently *usable* -- nextpnr picks it up
by path and nothing says the constids no longer match -- which is exactly the
kind of thing an artefact check has to catch.

These sweep the live tree, so they are the tree's guard rather than a
fixture's.  A slug or a datastore that is not present is skipped, never
failed: this suite runs on boxes that carry only the checkout.
"""
import hashlib
import json
import os
import sys
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

import check_evidence  # noqa: E402
from paths import OTC_ROOT, apicula_root  # noqa: E402

EVIDENCE_ROOT = os.path.join(OTC_ROOT, "evidence")

#: The nextpnr share tree the open flow's binary reads its database from.
DATASTORE = "/Users/alex/fine-line-data/open-toolchain-gw5ast"
NEXTPNR_SHARE = os.path.join(DATASTORE, "toolchains", "nextpnr", "share")


def _runs_files():
    for dirpath, _dirnames, filenames in os.walk(EVIDENCE_ROOT):
        if "runs.jsonl" in filenames:
            yield os.path.join(dirpath, "runs.jsonl")


def _rows(path):
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if line:
                yield lineno, json.loads(line)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _schema():
    root = apicula_root()
    if root is None:
        return None
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from fuzz.gw5ast138c.harness import evidence
    except ImportError:
        return None
    return evidence


class DiffCountKeysTest(unittest.TestCase):
    """`diff_count` carries the four §6 keys and nothing invented beside them."""

    def test_no_row_carries_a_non_schema_diff_count_key(self):
        schema = _schema()
        if schema is None:
            self.skipTest("no apicula checkout: the §6 schema is not importable")
        allowed = set(schema.DIFF_COUNT_KEYS)
        offenders = []
        for path in _runs_files():
            for lineno, row in _rows(path):
                bad = sorted(set(row.get("diff_count") or {}) - allowed)
                if bad:
                    slug = os.path.basename(os.path.dirname(path))
                    offenders.append(f"{slug}:{lineno} {row.get('run_id')}: {bad}")
        self.assertEqual(offenders, [], "diff_count keys outside §6")


class ArtifactPathResolutionTest(unittest.TestCase):
    """A path spelled relative to `$OTC` is a legal spelling, not a miss."""

    def test_repo_relative_path_resolves_against_the_checkout_root(self):
        slug_dir = os.path.join(EVIDENCE_ROOT, "ae350")
        marker = os.path.join(EVIDENCE_ROOT, "_runs")
        if not os.path.isdir(marker):
            self.skipTest("no evidence/_runs in this checkout")
        names = [n for n in sorted(os.listdir(marker)) if n.endswith(".log")]
        if not names:
            self.skipTest("no batch log to resolve")
        relative = os.path.join("evidence", "_runs", names[0])
        resolved = check_evidence._resolve_artifact(
            relative, slug_dir, EVIDENCE_ROOT)
        self.assertTrue(os.path.isfile(resolved), resolved)

    def test_absolute_path_is_taken_as_written(self):
        absolute = os.path.join(EVIDENCE_ROOT, "does-not-exist.log")
        self.assertEqual(
            check_evidence._resolve_artifact(absolute, EVIDENCE_ROOT, EVIDENCE_ROOT),
            absolute)

    def test_unresolvable_relative_path_is_reported_against_its_slug(self):
        slug_dir = os.path.join(EVIDENCE_ROOT, "ae350")
        resolved = check_evidence._resolve_artifact(
            "no/such/file.log", slug_dir, EVIDENCE_ROOT)
        self.assertEqual(resolved, os.path.join(slug_dir, "no/such/file.log"))


class PrimitiveLabelTest(unittest.TestCase):
    """A row names the primitive it measures, never the vehicle that carried it."""

    def test_every_dualpin_row_names_the_dual_purpose_primitive(self):
        path = os.path.join(EVIDENCE_ROOT, "dualpin", "runs.jsonl")
        if not os.path.isfile(path):
            self.skipTest("no dualpin slug in this checkout")
        named = {row["primitive"] for _lineno, row in _rows(path)}
        self.assertEqual(named, {"Dual-purpose pins"},
                         "the dual-purpose rows must name their own primitive")

    def test_no_slug_is_blank_against_spec_primitives(self):
        """Every primitive row with a populated slug has at least one row.

        The `BLANK` finding the checker prints is only reachable through the
        whole run; this asserts the same property directly, so a mislabelled
        row fails here with the slug named.
        """
        from paths import default_spec_primitives
        spec = default_spec_primitives()
        if not spec or not os.path.isfile(spec):
            self.skipTest("no spec-primitives.md reachable")
        blank = []
        for prow in check_evidence.parse_spec_primitives(spec):
            path = os.path.join(EVIDENCE_ROOT, prow.slug, "runs.jsonl")
            if not os.path.isfile(path):
                continue  # PENDING, not BLANK -- the slug has no rows yet
            if not any(str(row.get("primitive", "")).strip().lower()
                       == prow.id.lower() for _lineno, row in _rows(path)):
                blank.append(f"{prow.id} -> {prow.slug}")
        self.assertEqual(blank, [], "slugs carrying rows for no known primitive")


class InstalledChipdbTest(unittest.TestCase):
    """One database under the nextpnr share tree, never a stale second copy.

    The binary and its `.bin` are a matching pair (a constids change
    invalidates every older database), and nextpnr resolves the file by path
    without checking it -- so two differing copies under the share tree is a
    defect whether or not today's flow happens to read the right one.
    """

    def test_installed_chipdb_bins_are_one_database(self):
        if not os.path.isdir(NEXTPNR_SHARE):
            self.skipTest("no datastore nextpnr share tree on this box")
        found = {}
        for dirpath, _dirnames, filenames in os.walk(NEXTPNR_SHARE):
            for name in filenames:
                if name.startswith("chipdb-") and name.endswith(".bin"):
                    path = os.path.join(dirpath, name)
                    found.setdefault(name, {})[path] = _sha256(path)
        self.assertTrue(found, "no chipdb .bin installed under the share tree")
        for name, copies in sorted(found.items()):
            self.assertEqual(
                len(set(copies.values())), 1,
                f"{name} has diverging copies under the share tree: "
                + ", ".join(f"{p}={s[:8]}" for p, s in sorted(copies.items())))


if __name__ == "__main__":
    unittest.main()
