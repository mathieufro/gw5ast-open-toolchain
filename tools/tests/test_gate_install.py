"""S23b -- the local blocking gate is installed in this repo (C8, D75-D77),
mirroring the pattern already used in the `apicula` submodule.

Structural/wiring checks only: hook files present, executable, foreground,
`core.hooksPath` configured, and the `Makefile` carries a `gate` target.
The end-to-end proof that a failing check actually refuses a commit is a
one-off manual proof (temp branch, deleted afterwards), not a repeatable
test here -- a real refusal needs a real failing check and a real commit,
which is exactly what must never be left lying around in this repo.
"""
import os
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run(cmd, cwd=REPO_ROOT):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def test_hooks_exist_and_executable():
    for hook in ("pre-commit", "pre-push"):
        path = os.path.join(REPO_ROOT, ".githooks", hook)
        assert os.path.isfile(path), f"missing {path}"
        assert os.access(path, os.X_OK), f"{path} is not executable"


def test_hooks_run_in_foreground_and_never_bypass():
    for hook in ("pre-commit", "pre-push"):
        path = os.path.join(REPO_ROOT, ".githooks", hook)
        body = open(path).read()
        assert "nohup" not in body, f"{hook} backgrounds via nohup"
        assert "--no-verify" not in body, f"{hook} bypasses itself"
        for line in body.splitlines():
            stripped = line.split("#", 1)[0].rstrip()
            if not stripped.endswith("&"):
                continue
            assert stripped.endswith("&&"), (
                f"{hook} backgrounds a command: {line!r}")


def test_makefile_has_gate_target():
    path = os.path.join(REPO_ROOT, "Makefile")
    assert os.path.isfile(path), f"missing {path}"
    body = open(path).read()
    assert "gate:" in body, "Makefile has no gate target"
    for scope_target in ("_gate-fast:", "_gate-full:", "_gate-all:"):
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
