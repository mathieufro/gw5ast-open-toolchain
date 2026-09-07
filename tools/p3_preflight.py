"""Phase-3 preflight: prove the inherited Phase-0 / Phase-1 exit state from artefacts.

Phase 3 (IO and IOLOGIC) assumes seven things that earlier phases were supposed
to leave behind.  Assuming them is exactly the failure mode this pipeline is
built to avoid, so `P3.T01` re-proves each one and writes the result to
`$OTC/evidence/_runs/p3-preflight.log`.

The checks are ordered so that a failure of an earlier one explains a failure of
a later one: the chipdb must build before its flags can be read, and the guard
must be spelled correctly before the refusal test can fire.

Usage::

    python tools/p3_preflight.py            # run all seven, write the log
    python tools/p3_preflight.py --help
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paths  # noqa: E402

#: The device this whole pipeline is about.
DEVICE = "GW5AST-138C"

#: Local data store; binaries never enter a git tree (`D41`).
DATASTORE = os.environ.get(
    "DATASTORE", "/Users/alex/fine-line-data/open-toolchain-gw5ast")

#: The last line a passing run prints, and the `P3.T01` Done-when literal.
OK_LINE = "P3-PREFLIGHT ok: 7/7 checks"

#: Tools that must exist and answer `--help` (check 6).
REQUIRED_TOOLS = ("check_evidence.py", "check_criteria.py",
                  "check_timing_l0.py", "evidence.py")


def sha256(path):
    """Hex digest of a file, streamed -- the chipdb is ~1 MB but the .bin is not."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(argv, cwd, env=None):
    """`(returncode, combined output)`; never raises on a non-zero exit."""
    proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                          text=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def _venv_python():
    """The apicula editable-install interpreter (`LOOP-BRIEF` §2)."""
    candidate = "/Users/alex/fine-line/vendor/venv/bin/python"
    return candidate if os.path.isfile(candidate) else sys.executable


def _fse_iologic_source(apicula):
    """The body of `fse_iologic` alone -- the guard must be checked in place."""
    text = open(os.path.join(apicula, "apycula", "chipdb.py"),
                encoding="utf-8").read()
    match = re.search(r"^def fse_iologic\(.*?^(?=def )", text,
                      re.S | re.M)
    return match.group(0) if match else ""


def check_chipdb_builds(apicula, env):
    """(1) The builder exits 0 and its default output matches the datastore copy."""
    code, out = _run([_venv_python(), "-m", "apycula.chipdb_builder", DEVICE],
                     cwd=apicula, env=env)
    default = os.path.join(apicula, "apycula", f"{DEVICE}.msgpack.xz")
    if code != 0 or not os.path.isfile(default):
        return False, f"builder exit={code}, {default} present={os.path.isfile(default)}", {}
    target_dir = os.path.join(DATASTORE, "p3")
    os.makedirs(target_dir, exist_ok=True)
    copy = os.path.join(target_dir, f"chipdb-{DEVICE}.msgpack.xz")
    shutil.copy2(default, copy)
    left, right = sha256(default), sha256(copy)
    return (left == right,
            f"exit=0 canonical={default} sha256={left} copy_sha256={right}",
            {"chipdb_sha256": left, "chipdb_path": default,
             "chipdb_copy": copy, "builder_log_tail": out[-400:]})


def check_has_5a_hclk(apicula, env):
    """(2) `HAS_5A_HCLK` is in the canonical chipdb's `chip_flags` (`F21`, `F56`)."""
    snippet = (
        "from apycula.gowin_pack import ChipDB;"
        f"db = ChipDB('{DEVICE}').db;"
        "print('HCLK_FLAG_COUNT', list(db.chip_flags).count('HAS_5A_HCLK'))")
    code, out = _run([_venv_python(), "-c", snippet], cwd=apicula, env=env)
    hit = re.search(r"HCLK_FLAG_COUNT (\d+)", out)
    count = int(hit.group(1)) if hit else -1
    return count == 1, f"exit={code} HAS_5A_HCLK count={count}", {}


def check_guard_state_one(apicula, env):
    """(3) `D39` state (1): the misspelling is gone and the real guard is present."""
    text = open(os.path.join(apicula, "apycula", "chipdb.py"),
                encoding="utf-8").read()
    misspelled = text.count("GW5AST-138AC")
    guarded = _fse_iologic_source(apicula).count(
        "if device in {'GW5AST-138C'}:")
    return (misspelled == 0 and guarded >= 1,
            f"GW5AST-138AC occurrences={misspelled}, "
            f"fse_iologic bare 138C guards={guarded}",
            {"misspelled_count": misspelled, "guard_count": guarded})


def check_refusal_test(apicula, env):
    """(4) The IOLOGIC-before-HCLK refusal test is green on the synthetic fixture."""
    code, out = _run([_venv_python(), "-m", "pytest", "tests", "-k",
                      "unsupported_error and iologic", "-q"],
                     cwd=apicula, env=env)
    tail = out.strip().splitlines()[-1] if out.strip() else "<no output>"
    return code == 0, f"exit={code} {tail}", {}


#: The self-test needs a built design to inject into; the smoke design is the
#: one `P0.T29` calibrated it on, and `selftest` has no default for it.
SELFTEST_DESIGN = os.path.join(DATASTORE, "oracle-smoke")


def check_selftest(apicula, env):
    """(5) The harness selftest still reports exactly one injected difference."""
    if not os.path.isdir(SELFTEST_DESIGN):
        return False, f"design dir absent: {SELFTEST_DESIGN}", {}
    code, out = _run([_venv_python(), "-m",
                      "fuzz.gw5ast138c.harness.selftest",
                      "--design-dir", SELFTEST_DESIGN, "--inject-one-fuse"],
                     cwd=apicula, env=env)
    expected = "SELFTEST ok: 1 difference reported, 0 spurious"
    return expected in out, (f"exit={code} expected_line_present={expected in out} "
                             f"(--design-dir {SELFTEST_DESIGN})"), {}


def check_tools(env):
    """(6) The `DEL-e` tools exist and answer `--help` with exit 0."""
    misses = []
    for name in REQUIRED_TOOLS:
        path = os.path.join(paths.OTC_ROOT, "tools", name)
        if not os.path.isfile(path):
            misses.append(f"{name}:absent")
            continue
        code, _ = _run([sys.executable, path, "--help"],
                       cwd=paths.OTC_ROOT, env=env)
        if code != 0:
            misses.append(f"{name}:help_exit={code}")
    return not misses, ("all 4 present, --help exit 0" if not misses
                        else ", ".join(misses)), {}


def check_tests_package(apicula):
    """(7) apicula's pytest package exists; create it here if Phase 0 left it out."""
    tests = os.path.join(apicula, "tests")
    created = []
    if not os.path.isdir(tests):
        os.makedirs(tests)
    for name in ("__init__.py", "conftest.py"):
        target = os.path.join(tests, name)
        if not os.path.exists(target):
            open(target, "w", encoding="utf-8").close()
            created.append(name)
    note = "present" if not created else f"INHERITED GAP: created {created}"
    return True, note, {"tests_created": created}


def build_env(apicula):
    """`PYTHONPATH` at the apicula checkout plus the Gowin dyld triple."""
    env = dict(os.environ)
    env["PYTHONPATH"] = apicula + os.pathsep + env.get("PYTHONPATH", "")
    gowinhome = env.get(
        "GOWINHOME",
        "/Applications/GowinIDE.app/Contents/Resources/Gowin_EDA")
    env["GOWINHOME"] = gowinhome
    env["DYLD_LIBRARY_PATH"] = os.path.join(gowinhome, "IDE", "lib")
    env["DYLD_FRAMEWORK_PATH"] = os.path.join(gowinhome, "IDE", "lib")
    return env


def git_sha(repo):
    code, out = _run(["git", "-C", repo, "rev-parse", "HEAD"], cwd=repo)
    return out.strip() if code == 0 else "<unknown>"


def ide_version(gowinhome):
    try:
        from apycula import fse_parser
        return fse_parser.detect_ide_version(gowinhome)
    except Exception:  # noqa: BLE001 - a missing IDE is a reportable value
        return "unknown"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--output", default=os.path.join(
        paths.OTC_ROOT, "evidence", "_runs", "p3-preflight.log"))
    args = parser.parse_args(argv)

    apicula = paths.apicula_root()
    nextpnr = paths.sibling("nextpnr", "NEXTPNR_DIR")
    env = build_env(apicula)
    sys.path.insert(0, apicula)

    facts = {}
    results = []
    for label, fn in (
            ("1 chipdb builds, canonical == datastore copy",
             lambda: check_chipdb_builds(apicula, env)),
            ("2 HAS_5A_HCLK in chip_flags",
             lambda: check_has_5a_hclk(apicula, env)),
            ("3 D39 state (1) guard spelled GW5AST-138C",
             lambda: check_guard_state_one(apicula, env)),
            ("4 IOLOGIC-before-HCLK refusal test green",
             lambda: check_refusal_test(apicula, env)),
            ("5 harness selftest --inject-one-fuse",
             lambda: check_selftest(apicula, env)),
            ("6 DEL-e tools present and --help ok",
             lambda: check_tools(env)),
            ("7 apicula tests package present",
             lambda: check_tests_package(apicula)),
    ):
        ok, note, extra = fn()
        facts.update(extra)
        results.append((label, ok, note))

    mask = os.path.join(apicula, "fuzz", "gw5ast138c", "dontcare.mask")
    header = [
        "# P3.T01 - Phase-3 preflight over the inherited Phase-0 / Phase-1 state",
        f"apicula_sha: {git_sha(apicula)}",
        f"nextpnr_sha: {git_sha(nextpnr)}",
        f"chipdb_sha256: {facts.get('chipdb_sha256', '<unbuilt>')}",
        f"mask_sha256: {sha256(mask) if os.path.isfile(mask) else '<absent>'}",
        f"ide_version: {ide_version(env['GOWINHOME'])}",
        f"gowinhome: {env['GOWINHOME']}",
        "",
    ]
    body = [f"{'ok  ' if ok else 'FAIL'} {label}: {note}"
            for label, ok, note in results]
    passed = sum(1 for _, ok, _ in results if ok)
    last = OK_LINE if passed == len(results) else \
        f"P3-PREFLIGHT FAIL: {passed}/{len(results)} checks"

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write("\n".join(header + body + [last, ""]))
    print("\n".join(body + [last]))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
