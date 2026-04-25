"""Tests for cronwrap.runbook."""
import pytest
from pathlib import Path

from cronwrap.runbook import (
    Runbook,
    save_runbook,
    load_runbook,
    delete_runbook,
    list_runbooks,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


def test_has_content_true_when_url_set():
    rb = Runbook(job_name="job1", url="https://wiki.example.com/job1")
    assert rb.has_content() is True


def test_has_content_true_when_note_set():
    rb = Runbook(job_name="job1", note="Check disk space first.")
    assert rb.has_content() is True


def test_has_content_false_when_empty():
    rb = Runbook(job_name="job1")
    assert rb.has_content() is False


def test_format_includes_url(sdir):
    rb = Runbook(job_name="myjob", url="https://example.com")
    text = rb.format()
    assert "https://example.com" in text
    assert "myjob" in text


def test_format_no_content_shows_placeholder():
    rb = Runbook(job_name="myjob")
    assert "no runbook configured" in rb.format()


def test_save_and_load_roundtrip(sdir):
    rb = Runbook(job_name="backup", url="https://docs.example.com", note="Run as root")
    save_runbook(rb, sdir)
    loaded = load_runbook("backup", sdir)
    assert loaded is not None
    assert loaded.job_name == "backup"
    assert loaded.url == "https://docs.example.com"
    assert loaded.note == "Run as root"


def test_load_missing_returns_none(sdir):
    assert load_runbook("nonexistent", sdir) is None


def test_delete_existing_returns_true(sdir):
    rb = Runbook(job_name="todelete", url="http://x.com")
    save_runbook(rb, sdir)
    assert delete_runbook("todelete", sdir) is True
    assert load_runbook("todelete", sdir) is None


def test_delete_missing_returns_false(sdir):
    assert delete_runbook("ghost", sdir) is False


def test_list_runbooks_empty(sdir):
    assert list_runbooks(sdir) == []


def test_list_runbooks_returns_all(sdir):
    for name in ("alpha", "beta", "gamma"):
        save_runbook(Runbook(job_name=name, url=f"http://{name}.com"), sdir)
    books = list_runbooks(sdir)
    assert len(books) == 3
    names = {rb.job_name for rb in books}
    assert names == {"alpha", "beta", "gamma"}
