"""`V12a --classes io` against this phase's own vendor SDF (`P3.T34`)."""

import os
import re
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.dirname(_HERE)
_WORKTREE = os.path.dirname(os.path.dirname(_TOOLS))

SDF = ("/Users/alex/fine-line-data/open-toolchain-gw5ast/p3t12/"
       "p3-oddr-iddr-io_basic-0000/run/impl/pnr/run.sdf")
CHIPDB = os.path.join(_WORKTREE, "apicula/apycula/GW5AST-138C.msgpack.xz")

HEADER = re.compile(
    r"^L0 ok: [0-9]+/[0-9]+ arcs within ±10%, ([0-9]+) exceptions listed$")


@pytest.fixture(scope="module")
def v12a_io():
    """The literal `V12a --classes io` invocation, run once."""
    for path in (SDF, CHIPDB):
        if not os.path.exists(path):
            pytest.skip(f"{path} is not in the datastore on this host")
    proc = subprocess.run(
        [sys.executable, os.path.join(_TOOLS, "check_timing_l0.py"),
         "--classes", "io", "--sdf", SDF, "--chipdb", CHIPDB],
        capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.splitlines()


def test_v12a_io_output_contract(v12a_io):
    assert HEADER.match(v12a_io[0]), v12a_io[0]
    assert v12a_io[1].strip(), "the SDF condition line must follow the header"


def test_v12a_io_exceptions_enumerated(v12a_io):
    listed = int(HEADER.match(v12a_io[0]).group(1))
    exceptions = [line for line in v12a_io[1:]
                  if line.startswith("exception:")]
    assert len(exceptions) == listed
