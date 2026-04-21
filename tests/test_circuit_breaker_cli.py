"""Tests for cronwrap.circuit_breaker_cli."""
import json
import pytest
from cronwrap.circuit_breaker import record_circuit_outcome
from cronwrap.circuit_breaker_cli import run_circuit_cli


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


def test_show_closed_circuit(sdir, capsys):
    rc = run_circuit_cli(["--state-dir", sdir, "show", "myjob"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "closed"
    assert out["failures"] == 0
    assert out["job"] == "myjob"


def test_show_open_circuit(sdir, capsys):
    import time
    now = time.time()
    for _ in range(3):
        record_circuit_outcome(sdir, "myjob", succeeded=False, threshold=3, now=now)
    rc = run_circuit_cli(["--state-dir", sdir, "show", "myjob"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "open"
    assert out["failures"] == 3


def test_reset_existing_state(sdir, capsys):
    import time
    now = time.time()
    for _ in range(3):
        record_circuit_outcome(sdir, "myjob", succeeded=False, threshold=3, now=now)
    rc = run_circuit_cli(["--state-dir", sdir, "reset", "myjob"])
    assert rc == 0
    assert "reset" in capsys.readouterr().out
    # After reset, show should report closed
    run_circuit_cli(["--state-dir", sdir, "show", "myjob"])
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "closed"


def test_reset_nonexistent_job(sdir, capsys):
    rc = run_circuit_cli(["--state-dir", sdir, "reset", "ghost"])
    assert rc == 0
    assert "No circuit state" in capsys.readouterr().out


def test_no_subcommand_prints_help(sdir, capsys):
    rc = run_circuit_cli(["--state-dir", sdir])
    assert rc == 1
