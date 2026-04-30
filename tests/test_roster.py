"""Tests for cronwrap.roster."""
import pytest

from cronwrap.roster import (
    RosterEntry,
    get_job,
    list_jobs,
    register_job,
    unregister_job,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


def _entry(name="backup", command="/usr/bin/backup.sh", **kw) -> RosterEntry:
    return RosterEntry(name=name, command=command, **kw)


def test_register_creates_entry(sdir):
    register_job(sdir, _entry())
    job = get_job(sdir, "backup")
    assert job is not None
    assert job.command == "/usr/bin/backup.sh"


def test_register_overwrites_existing(sdir):
    register_job(sdir, _entry(command="old"))
    register_job(sdir, _entry(command="new"))
    assert get_job(sdir, "backup").command == "new"


def test_get_job_missing_returns_none(sdir):
    assert get_job(sdir, "ghost") is None


def test_list_jobs_empty(sdir):
    assert list_jobs(sdir) == []


def test_list_jobs_returns_all(sdir):
    register_job(sdir, _entry("a", "cmd_a"))
    register_job(sdir, _entry("b", "cmd_b"))
    names = {j.name for j in list_jobs(sdir)}
    assert names == {"a", "b"}


def test_list_jobs_filtered_by_tag(sdir):
    register_job(sdir, _entry("a", "cmd_a", tags=["db", "nightly"]))
    register_job(sdir, _entry("b", "cmd_b", tags=["web"]))
    result = list_jobs(sdir, tag="db")
    assert len(result) == 1
    assert result[0].name == "a"


def test_list_jobs_tag_no_match(sdir):
    register_job(sdir, _entry("a", "cmd_a", tags=["web"]))
    assert list_jobs(sdir, tag="db") == []


def test_unregister_existing(sdir):
    register_job(sdir, _entry())
    removed = unregister_job(sdir, "backup")
    assert removed is True
    assert get_job(sdir, "backup") is None


def test_unregister_missing_returns_false(sdir):
    assert unregister_job(sdir, "ghost") is False


def test_entry_enabled_default(sdir):
    register_job(sdir, _entry())
    assert get_job(sdir, "backup").enabled is True


def test_entry_disabled(sdir):
    register_job(sdir, _entry(enabled=False))
    assert get_job(sdir, "backup").enabled is False


def test_as_dict_roundtrip():
    e = _entry(tags=["x"], description="desc", schedule="0 * * * *")
    d = e.as_dict()
    assert d["name"] == "backup"
    assert d["tags"] == ["x"]
    assert d["description"] == "desc"
