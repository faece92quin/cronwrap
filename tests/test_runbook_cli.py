"""Tests for cronwrap.runbook_cli."""
import pytest
from cronwrap.runbook import Runbook, save_runbook
from cronwrap.runbook_cli import build_runbook_parser, run_runbook_cli


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


def _parse(sdir, *args):
    p = build_runbook_parser()
    return p.parse_args(["--state-dir", sdir, *args])


def test_set_creates_runbook(sdir):
    args = _parse(sdir, "set", "myjob", "--url", "https://wiki.local")
    rc = run_runbook_cli(args)
    assert rc == 0
    from cronwrap.runbook import load_runbook
    rb = load_runbook("myjob", sdir)
    assert rb is not None
    assert rb.url == "https://wiki.local"


def test_show_existing(sdir, capsys):
    save_runbook(Runbook(job_name="showjob", url="http://example.com", note="check logs"), sdir)
    args = _parse(sdir, "show", "showjob")
    rc = run_runbook_cli(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "http://example.com" in out
    assert "check logs" in out


def test_show_missing_returns_1(sdir, capsys):
    args = _parse(sdir, "show", "ghost")
    rc = run_runbook_cli(args)
    assert rc == 1


def test_delete_existing(sdir):
    save_runbook(Runbook(job_name="todel"), sdir)
    args = _parse(sdir, "delete", "todel")
    rc = run_runbook_cli(args)
    assert rc == 0


def test_delete_missing_returns_1(sdir):
    args = _parse(sdir, "delete", "nobody")
    rc = run_runbook_cli(args)
    assert rc == 1


def test_list_empty(sdir, capsys):
    args = _parse(sdir, "list")
    rc = run_runbook_cli(args)
    assert rc == 0
    assert "No runbooks" in capsys.readouterr().out


def test_list_shows_entries(sdir, capsys):
    for name in ("a", "b"):
        save_runbook(Runbook(job_name=name, url=f"http://{name}.io"), sdir)
    args = _parse(sdir, "list")
    rc = run_runbook_cli(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "http://a.io" in out
    assert "http://b.io" in out


def test_no_subcommand_returns_1(sdir, capsys):
    args = _parse(sdir)
    rc = run_runbook_cli(args)
    assert rc == 1
