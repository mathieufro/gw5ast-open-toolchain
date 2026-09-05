"""S23b -- the local blocking gate is installed in this repo (C8, D75-D77),
mirroring the pattern already used in the `apicula` submodule.

Structural/wiring checks only: hook files present, executable, `pre-push`
detaches the gate and never blocks, `core.hooksPath` configured, and the
`Makefile` carries a `gate` target. The end-to-end proof that a failing
check actually shows up as a FAIL marker is a one-off manual proof (temp
branch, deleted afterwards), not a repeatable test here -- a real gate run
takes real wall-clock time, which is exactly what must never be left
lying around in this repo.

Owner ruling (C12/D94/D95): there is no `pre-commit` hook any more --
`pre-push` is the only hook, and it now backgrounds the gate on purpose
(that's the whole point: the push is never blocked).
"""
import os
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run(cmd, cwd=REPO_ROOT):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def test_pre_push_hook_exists_and_executable():
    path = os.path.join(REPO_ROOT, ".githooks", "pre-push")
    assert os.path.isfile(path), f"missing {path}"
    assert os.access(path, os.X_OK), f"{path} is not executable"


def test_pre_commit_hook_removed():
    # C12/D94/D95: pre-commit was deleted repo-wide -- pre-push is the only
    # hook. Positive proof it's gone, not just absence-by-omission.
    path = os.path.join(REPO_ROOT, ".githooks", "pre-commit")
    assert not os.path.exists(path), (
        f"{path} exists but pre-commit was removed by C12/D94/D95")


def test_pre_push_never_bypasses_itself():
    path = os.path.join(REPO_ROOT, ".githooks", "pre-push")
    body = open(path).read()
    assert "--no-verify" not in body, "pre-push bypasses itself"


def test_pre_push_exits_zero_promptly():
    # C12: the hook must never block a push -- it always exits 0 after
    # spawning the detached gate, whether or not this push targets a
    # gated ref.
    path = os.path.join(REPO_ROOT, ".githooks", "pre-push")
    body = open(path).read()
    assert "exit 0" in body


def test_makefile_has_gate_target():
    path = os.path.join(REPO_ROOT, "Makefile")
    assert os.path.isfile(path), f"missing {path}"
    body = open(path).read()
    assert "gate:" in body, "Makefile has no gate target"
    for scope_target in ("_gate-fast:", "_gate-branch:", "_gate-full:"):
        assert scope_target in body, f"Makefile missing {scope_target}"


def test_gate_env_exists_and_exports_gowinhome():
    path = os.path.join(REPO_ROOT, "gate.env")
    assert os.path.isfile(path), f"missing {path}"
    body = open(path).read()
    assert "GOWINHOME" in body


def test_hookspath_configured():
    proc = _run(["git", "config", "--get", "core.hooksPath"])
    assert proc.returncode == 0, "core.hooksPath is not set"
    assert proc.stdout.strip() == ".githooks", (
        f"core.hooksPath={proc.stdout.strip()!r}, expected '.githooks'")
