#!/usr/bin/env python3
"""Shim (cross-phase F1): the SAME tool as
`python -m fuzz.gw5ast138c.harness.evidence`, same flags (`--rollup`,
`--ensure-tree`, `--evidence-root`). It re-implements nothing; no phase
anywhere creates a second implementation.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import apicula_root  # noqa: E402

_root = apicula_root()
if _root is None:
    raise SystemExit("evidence.py: no apicula checkout found")
sys.path.insert(0, _root)

from fuzz.gw5ast138c.harness.evidence import main  # noqa: E402

sys.exit(main(sys.argv[1:]))
