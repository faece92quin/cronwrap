"""Tests for cronwrap.metrics."""
import json
import os
import time

import pytest

from cronwrap.metrics import collect_metrics, write_metrics, ExecutionMetrics


START = 1_700_000_000.0
END = 1_700_000_005.25


def _make_metrics(**kwargs):
    defaults = dict(
        command="echo hi",
        started_at=START,
        finished_at=END,
        exit_code=0,
        attempts=1,
        stdout="hello\n",
        stderr="",
    )
    defaults.update(kwargs)
    return collect_metrics(**defaults)


def test_duration_calculated():
    m = _make_metrics()
    assert m.duration_seconds == pytest.approx(5.25, abs=1e-3)


def test_succeeded_flag_true_on_zero_exit():
    m = _make_metrics(exit_code=0)
    assert m.succeeded is True


def test_succeeded_flag_false_on_nonzero_exit():
    m = _make_metrics(exit_code=1)
    assert m.succeeded is False


def test_stdout_bytes_counted():
    m = _make_metrics(stdout="hello\n")
    assert m.stdout_bytes == len("hello\n".encode())


def test_extra_stored():
    m = _make_metrics(extra={"job": "backup"})
    assert m.extra == {"job": "backup"}


def test_to_dict_contains_keys():
    m = _make_metrics()
    d = m.to_dict()
    for key in ("command", "exit_code", "duration_seconds", "attempts", "succeeded"):
        assert key in d


def test_to_json_is_valid(tmp_path):
    m = _make_metrics()
    data = json.loads(m.to_json())
    assert data["command"] == "echo hi"


def test_write_metrics_creates_file(tmp_path):
    path = str(tmp_path / "logs" / "metrics.jsonl")
    m = _make_metrics()
    write_metrics(m, path)
    assert os.path.exists(path)


def test_write_metrics_appends(tmp_path):
    path = str(tmp_path / "metrics.jsonl")
    m = _make_metrics()
    write_metrics(m, path)
    write_metrics(m, path)
    lines = open(path).readlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["command"] == "echo hi"
