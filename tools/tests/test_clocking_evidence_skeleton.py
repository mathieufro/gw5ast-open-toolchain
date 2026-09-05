"""`P1.T03` -- the clocking evidence skeleton and the oracle-run ledger.

Asserts the committed tree, not a throwaway fixture: `evidence/<slug>/` for
each of the seven Phase-1-owned primitives exists with a `summary.md`
carrying the four required headings, and `evidence/_budget/clocking-runs.tsv`
carries exactly one data row with `cumulative == 0`.

Deliberately does **not** assert a `runs.jsonl` file at each slug (`size 0`
or otherwise): `runs.jsonl` is created lazily by
`fuzz.gw5ast138c.harness.evidence.append_row` on the first real oracle run,
same as everywhere else in this tree, because `check_evidence.py`'s own D90
invariant (`test_check_evidence_rejects_empty_runs_jsonl`) makes an empty
`runs.jsonl` anywhere in the tree a hard failure -- "an empty ... evidence
file is not evidence." Pre-creating one here would make this task
unlandable through the binding local gate (`LOOP-BRIEF` C8). See
`tools/check_evidence.py`'s P1.T03 note and
`TestSkeletonDirectoryIsPending` in `test_check_evidence.py` for the paired
fix that keeps a directory-only skeleton `PENDING`, never `BLANK`.
"""
import os

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTC_ROOT = os.path.dirname(TOOLS_DIR)
EVIDENCE_ROOT = os.path.join(OTC_ROOT, "evidence")

SLUGS = ("plla", "hclk", "clkdiv", "clkdiv2", "dhcen", "dqce", "dcs")
REQUIRED_HEADINGS = ("## Row", "## Sweep", "## Verdict", "## Artefacts")


def test_clocking_evidence_skeleton_present():
    assert len(SLUGS) == 7
    for slug in SLUGS:
        slug_dir = os.path.join(EVIDENCE_ROOT, slug)
        assert os.path.isdir(slug_dir), f"missing evidence directory: {slug_dir}"

        summary_path = os.path.join(slug_dir, "summary.md")
        assert os.path.isfile(summary_path), f"missing summary.md: {summary_path}"
        with open(summary_path, encoding="utf-8") as fh:
            text = fh.read()
        for heading in REQUIRED_HEADINGS:
            assert heading in text, f"{summary_path} missing heading {heading!r}"

    tsv_path = os.path.join(EVIDENCE_ROOT, "_budget", "clocking-runs.tsv")
    assert os.path.isfile(tsv_path), f"missing {tsv_path}"
    with open(tsv_path, encoding="utf-8") as fh:
        lines = [line.rstrip("\n") for line in fh if line.strip()]
    header, data_rows = lines[0], lines[1:]
    assert header.split("\t") == [
        "batch_id", "slug", "runs", "cumulative", "timestamp"]
    # The seed row plus one row per recorded batch. This used to assert
    # `== 1`, which pinned the ledger at its pre-measurement state and turned
    # the first recorded batch into a failure -- a guard that forbade its own
    # subject. What it guards now is the schema and the running total.
    assert len(data_rows) >= 1, f"expected at least 1 data row, got {data_rows}"
    running = 0
    for line in data_rows:
        cols = line.split("\t")
        assert len(cols) == 5, f"malformed ledger row: {line!r}"
        running += int(cols[2])
        assert int(cols[3]) == running, (
            f"cumulative column is not the running sum of runs: {line!r} "
            f"(expected {running})")
    fields = data_rows[0].split("\t")
    cumulative = fields[3]
    assert cumulative == "0", f"expected cumulative == 0, got {cumulative!r}"
