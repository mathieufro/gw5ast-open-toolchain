"""Tests for `tools/gate_status.py` -- the read side of the detached local
gate (C12/D94/D95). Never touches the real `evidence/_gates/`; each test
builds a throwaway gates directory and calls `main()` directly.
"""
import json
import os
import sys
import time

import pytest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

import gate_status as gs  # noqa: E402


def touch(path, mtime_minutes_ago=None, content=None):
    if content is not None:
        with open(path, "w") as fh:
            fh.write(content)
    else:
        open(path, "a").close()
    if mtime_minutes_ago is not None:
        stamp = time.time() - mtime_minutes_ago * 60
        os.utime(path, (stamp, stamp))


def test_no_gates_found(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()

    rc = gs.main(gates_dir=str(gates_dir))

    assert rc == 0
    out = capsys.readouterr().out
    assert "no gates found" in out


def test_no_gates_dir_at_all(tmp_path, capsys):
    # the directory doesn't even exist yet -- still a clean "nothing found".
    gates_dir = tmp_path / "_gates"

    rc = gs.main(gates_dir=str(gates_dir))

    assert rc == 0
    assert "no gates found" in capsys.readouterr().out


def test_pass_and_fail_in_two_repos(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "one-main-abc123.result"), content="PASS")
    touch(str(gates_dir / "two-main-def456.result"), content="FAIL")

    rc = gs.main(gates_dir=str(gates_dir))

    out = capsys.readouterr().out
    assert rc == 1
    assert "one-main-abc123  PASS" in out
    assert "two-main-def456  FAIL" in out


def test_newest_marker_of_a_repo_is_the_verdict(tmp_path, capsys):
    """A red run stays visible but stops counting once a green one follows."""
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-old111.result"), content="FAIL",
          mtime_minutes_ago=600)
    touch(str(gates_dir / "repo-main-new222.result"), content="PASS",
          mtime_minutes_ago=5)

    rc = gs.main(gates_dir=str(gates_dir))

    out = capsys.readouterr().out
    assert rc == 0
    assert "repo-main-new222  PASS" in out
    assert "repo-main-old111  SUPERSEDED" in out


def test_a_newer_red_run_is_still_a_failure(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-old111.result"), content="PASS",
          mtime_minutes_ago=600)
    touch(str(gates_dir / "repo-main-new222.result"), content="FAIL",
          mtime_minutes_ago=5)

    assert gs.main(gates_dir=str(gates_dir)) == 1
    assert "repo-main-new222  FAIL" in capsys.readouterr().out


def test_running_gate_whose_process_is_gone_is_dead(tmp_path, capsys):
    """A killed gate never writes a result; it must not read as RUNNING."""
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-abc123.log"), mtime_minutes_ago=2)
    dead_pid = _a_pid_that_is_not_running()
    touch(str(gates_dir / "repo-main-abc123.pid"), content=str(dead_pid))

    rc = gs.main(gates_dir=str(gates_dir))

    assert rc == 1
    assert "repo-main-abc123  DEAD" in capsys.readouterr().out


def _a_pid_that_is_not_running():
    """A pid no process holds: fork a child and reap it."""
    pid = os.fork()
    if pid == 0:  # pragma: no cover -- the child never returns
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


def test_running_gate_under_30_minutes_is_ok(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    # only a .log exists (no .result yet) -- gate started but hasn't finished.
    touch(str(gates_dir / "repo-main-abc123.log"), mtime_minutes_ago=5)

    rc = gs.main(gates_dir=str(gates_dir))

    out = capsys.readouterr().out
    assert rc == 0
    assert "repo-main-abc123  RUNNING" in out


def test_running_gate_over_30_minutes_is_stale(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-abc123.log"), mtime_minutes_ago=45)

    rc = gs.main(gates_dir=str(gates_dir))

    out = capsys.readouterr().out
    assert rc == 1
    assert "repo-main-abc123  RUNNING" in out


def test_result_present_takes_priority_over_log(tmp_path, capsys):
    # a finished gate leaves both a .log and a .result; RUNNING must not
    # win once a terminal result exists.
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-abc123.log"), mtime_minutes_ago=45)
    touch(str(gates_dir / "repo-main-abc123.result"), content="PASS")

    rc = gs.main(gates_dir=str(gates_dir))

    out = capsys.readouterr().out
    assert rc == 0
    assert "repo-main-abc123  PASS" in out
    assert "RUNNING" not in out


def test_json_flag_shape(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-abc123.result"), content="PASS")
    touch(str(gates_dir / "repo-dev-xyz999.log"), mtime_minutes_ago=1)

    rc = gs.main(gates_dir=str(gates_dir), json_output=True)

    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert isinstance(payload, list)
    ids = {g["id"] for g in payload}
    assert ids == {"repo-main-abc123", "repo-dev-xyz999"}
    for gate in payload:
        assert set(gate.keys()) == {"id", "status", "age_minutes"}
        assert gate["status"] in ("PASS", "FAIL", "RUNNING", "DEAD",
                                  "SUPERSEDED")
        assert isinstance(gate["age_minutes"], (int, float))


def test_json_flag_empty_is_valid_json(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()

    rc = gs.main(gates_dir=str(gates_dir), json_output=True)

    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out) == []


def test_watchdog_log_is_not_a_second_gate(tmp_path, capsys):
    # every finished (or running) gate also has an `<id>.watchdog.log`
    # sibling (gate_watchdog.sh). `*.watchdog.log` also matches `*.log`, so
    # naive stripping of ".log" would misread it as a second gate id
    # "<id>.watchdog" stuck RUNNING forever.
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-abc123.result"), content="PASS")
    touch(str(gates_dir / "repo-main-abc123.log"), mtime_minutes_ago=2)
    touch(str(gates_dir / "repo-main-abc123.watchdog.log"), mtime_minutes_ago=2)
    touch(str(gates_dir / "repo-main-abc123.pid"), content="12345")

    rc = gs.main(gates_dir=str(gates_dir))

    out = capsys.readouterr().out
    assert rc == 0
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0].startswith("repo-main-abc123  PASS")


def test_sorted_by_id(tmp_path, capsys):
    gates_dir = tmp_path / "_gates"
    gates_dir.mkdir()
    touch(str(gates_dir / "repo-main-zzz.result"), content="PASS")
    touch(str(gates_dir / "repo-main-aaa.result"), content="PASS")

    gs.main(gates_dir=str(gates_dir))

    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    assert lines[0].startswith("repo-main-aaa")
    assert lines[1].startswith("repo-main-zzz")
