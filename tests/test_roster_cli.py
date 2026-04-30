"""Tests for cronwrap.roster_cli."""
import argparse
import json
import pytest

from cronwrap.roster import register_job, RosterEntry
from cronwrap.roster_cli import build_roster_parser, run_roster_cli


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


def _parse(args):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_roster_parser(sub)
    return parser.parse_args(args)


def test_register_returns_0(sdir):
    ns = _parse(["roster", "register", "myjob", "echo hi", "--state-dir", sdir])
    assert run_roster_cli(ns) == 0


def test_register_then_show(sdir):
    ns = _parse(["roster", "register", "myjob", "echo hi", "--state-dir", sdir])
    run_roster_cli(ns)
    ns2 = _parse(["roster", "show", "myjob", "--state-dir", sdir])
    assert run_roster_cli(ns2) == 0


def test_show_missing_returns_1(sdir, capsys):
    ns = _parse(["roster", "show", "ghost", "--state-dir", sdir])
    assert run_roster_cli(ns) == 1


def test_unregister_existing(sdir):
    register_job(sdir, RosterEntry(name="j", command="cmd"))
    ns = _parse(["roster", "unregister", "j", "--state-dir", sdir])
    assert run_roster_cli(ns) == 0


def test_unregister_missing_returns_1(sdir):
    ns = _parse(["roster", "unregister", "ghost", "--state-dir", sdir])
    assert run_roster_cli(ns) == 1


def test_list_empty(sdir, capsys):
    ns = _parse(["roster", "list", "--state-dir", sdir])
    assert run_roster_cli(ns) == 0
    assert "No jobs" in capsys.readouterr().out


def test_list_json(sdir, capsys):
    register_job(sdir, RosterEntry(name="j", command="cmd", tags=["t1"]))
    ns = _parse(["roster", "list", "--json", "--state-dir", sdir])
    run_roster_cli(ns)
    data = json.loads(capsys.readouterr().out)
    assert data[0]["name"] == "j"


def test_list_tag_filter(sdir, capsys):
    register_job(sdir, RosterEntry(name="a", command="ca", tags=["db"]))
    register_job(sdir, RosterEntry(name="b", command="cb", tags=["web"]))
    ns = _parse(["roster", "list", "--tag", "db", "--state-dir", sdir])
    run_roster_cli(ns)
    out = capsys.readouterr().out
    assert "a" in out
    assert "b" not in out


def test_register_with_tags_and_schedule(sdir):
    ns = _parse([
        "roster", "register", "nightly", "backup.sh",
        "--schedule", "0 2 * * *",
        "--tags", "db", "nightly",
        "--state-dir", sdir,
    ])
    assert run_roster_cli(ns) == 0
