"""Tests for `P2.T34` -- summaries, roll-up, storage hygiene.

Each slug's `summary.md` quotes run counts, verdict distribution, artefact
paths + sha256 into the data store, and any deferred observation, at
`<= 200` lines (`spec-harness.md` §6). `evidence-table.md` is the append-only
roll-up. Storage hygiene (`V20`/`D41`): the evidence tree denies binaries by
`.gitignore`, the two sha256 manifests exist, and no binary of the seven
denied extensions is tracked under `evidence/`.
"""
import hashlib
import os
import re

OTC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE_DIR = os.path.join(OTC, "evidence")

#: `P2.T34`'s three slugs. `dualpin` is `P2.T29`'s (a separate branch) and
#: may not exist yet -- its summary is not this task's to write.
SLUGS = ("ae350", "ae350-ram")
SLUGS_INCLUDING_PENDING = ("ae350", "ae350-ram", "dualpin")

MAX_SUMMARY_LINES = 200

#: `path | sha256` pairs quoted in a summary as a markdown table cell pair,
#: e.g. `` `/abs/path` `` followed later on the same row by 64 hex chars.
_SHA256_RE = re.compile(r"`([0-9a-f]{64})`")
_PATH_CELL_RE = re.compile(r"`(/[^`]+)`\s*\|\s*`([0-9a-f]{64})`")


def _summary_path(slug):
    return os.path.join(EVIDENCE_DIR, slug, "summary.md")


def test_each_summary_at_most_200_lines():
    for slug in SLUGS:
        path = _summary_path(slug)
        assert os.path.isfile(path), f"{path} is missing"
        with open(path, encoding="utf-8") as fh:
            n = sum(1 for _ in fh)
        assert n <= MAX_SUMMARY_LINES, f"{path} is {n} lines, over the {MAX_SUMMARY_LINES} cap"


def test_summary_sha256s_resolve():
    """Every path|sha256 pair quoted in a summary resolves and matches.

    A slug whose row never produced a bitstream (`ae350-ram`: `refused`
    before place-and-route) legitimately quotes none -- absence of pairs is
    not a failure there, only a mismatch is. At least one slug (`ae350`)
    must carry pairs, or the check itself would be vacuous.
    """
    mismatches = []
    checked = 0
    for slug in SLUGS:
        path = _summary_path(slug)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for m in _PATH_CELL_RE.finditer(text):
            file_path, claimed = m.group(1), m.group(2)
            checked += 1
            if not os.path.isfile(file_path):
                mismatches.append(f"{path}: {file_path} does not exist")
                continue
            with open(file_path, "rb") as fh:
                actual = hashlib.sha256(fh.read()).hexdigest()
            if actual != claimed:
                mismatches.append(
                    f"{path}: {file_path} sha256 {actual} != claimed {claimed}")
    assert checked > 0, "no path|sha256 pairs found to check across any slug"
    assert mismatches == [], "\n".join(mismatches)


def test_no_binaries_tracked_under_evidence():
    import subprocess
    denied_ext = (".fs", ".vo", ".tr", ".sdf", ".fse", ".dat", ".tm")
    out = subprocess.run(
        ["git", "-C", OTC, "ls-files", "evidence"],
        capture_output=True, text=True, check=True).stdout
    tracked = [p for p in out.splitlines() if p]
    binaries = [p for p in tracked if p.endswith(denied_ext)]
    assert binaries == [], f"binaries tracked under evidence/: {binaries}"


def test_evidence_gitignore_denies_fs_files():
    import subprocess
    result = subprocess.run(
        ["git", "-C", OTC, "check-ignore", "-q",
         os.path.join(EVIDENCE_DIR, "_runs", "x.fs")])
    assert result.returncode == 0, "evidence/.gitignore does not deny .fs files"


def test_the_two_sha256_manifests_exist():
    assert os.path.isfile(os.path.join(OTC, "vendor-gowin.sha256"))
    assert os.path.isfile(os.path.join(OTC, "ide-share-device.sha256"))


def test_evidence_table_has_rows_for_ae350_slugs():
    path = os.path.join(EVIDENCE_DIR, "evidence-table.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for slug in SLUGS:
        assert re.search(rf"\|\s*{re.escape(slug)}\s*\|", text), (
            f"evidence-table.md has no per-slug row for {slug!r}")
    assert "AE350_SOC" in text
    assert "AE350_RAM" in text


def test_dualpin_slug_is_skipped_gracefully_when_absent():
    """`P2.T29` (a separate branch) may not have landed `evidence/dualpin/`
    yet; T34 must not fail for a slug that legitimately does not exist."""
    dualpin_dir = os.path.join(EVIDENCE_DIR, "dualpin")
    if not os.path.isdir(dualpin_dir):
        assert not os.path.isfile(_summary_path("dualpin"))
    else:
        # P2.T29 landed since this test was written -- its own summary is
        # its own task's to write and check, not asserted here.
        pass
