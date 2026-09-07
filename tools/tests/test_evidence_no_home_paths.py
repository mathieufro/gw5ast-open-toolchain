"""No committed evidence JSON embeds an absolute *repo-tree* home path.

`D41` (`brainstorm-decisions.md:172`) deliberately references large binaries
by an absolute path into the **local data store**,
`/Users/<user>/fine-line-data/open-toolchain-gw5ast/`, outside any git tree --
that carve-out is intentional and this test does not flag it. What it does
flag is a path rooted at the author's `$HOME` that points *inside the repo
tree itself* (`evidence/ae350/port-inventory.json` embedded
`/Users/alex/fine-line/vendor/gowin/ip/...`, gestalt-p2 `C5`) -- that is both
a cosmetic leak and a path that will not resolve on anyone else's machine,
where a repo-relative path would. This sweeps every committed evidence JSON
for that shape, rather than re-checking the one file the finding named, so a
future evidence file carrying the same mistake is caught the same way.
"""
import glob
import json
import os
import re

OTC_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE_DIR = os.path.join(OTC_ROOT, "evidence")

#: A path rooted at a user's home directory, inside the `fine-line` repo tree
#: specifically (never `fine-line-data`, which is `D41`'s sanctioned external
#: data store, or `/Applications/...`, a system install location -- neither
#: is this shape and neither is matched here).
HOME_PATH_RE = re.compile(r"/Users/[^/\"]+/fine-line/")


def _all_evidence_json_files():
    return sorted(glob.glob(os.path.join(EVIDENCE_DIR, "**", "*.json"),
                             recursive=True))


def _find_home_paths(value, path=""):
    """Yield `(json_path, string)` for every string value matching the home-path shape."""
    if isinstance(value, str):
        if HOME_PATH_RE.search(value):
            yield path, value
    elif isinstance(value, dict):
        for key, sub in value.items():
            yield from _find_home_paths(sub, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            yield from _find_home_paths(sub, f"{path}[{i}]")


def test_no_committed_evidence_json_embeds_a_home_directory_path():
    """Every path string in every evidence JSON is repo-relative, not `$HOME`-rooted."""
    files = _all_evidence_json_files()
    assert files, f"no evidence JSON found under {EVIDENCE_DIR}"

    offenders = {}
    for path in files:
        with open(path) as f:
            data = json.load(f)
        hits = list(_find_home_paths(data))
        if hits:
            offenders[os.path.relpath(path, OTC_ROOT)] = hits

    assert not offenders, (
        "evidence JSON embeds an absolute home-directory path (gestalt-p2 C5): "
        + "; ".join(
            f"{rel}: {json_path} = {value!r}"
            for rel, hits in offenders.items()
            for json_path, value in hits
        )
    )
