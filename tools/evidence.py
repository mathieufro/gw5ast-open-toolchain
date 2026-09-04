#!/usr/bin/env python3
"""Shim (cross-phase F1): the SAME tool as
`python -m fuzz.gw5ast138c.harness.evidence`, same flags (`--rollup`,
`--ensure-tree`, `--evidence-root`). It re-implements nothing; no phase
anywhere creates a second implementation.
"""
import sys
for _apicula in (
        "/Users/alex/fine-line/apicula",
        "/Users/alex/fine-line/.atelier/worktrees/"
        "2026-09-03-open-toolchain-gw5ast-7e84/apicula"):
    sys.path.insert(0, _apicula)
from fuzz.gw5ast138c.harness.evidence import main  # noqa: E402
sys.exit(main(sys.argv[1:]))
