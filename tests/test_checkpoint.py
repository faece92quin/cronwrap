"""Tests for cronwrap.checkpoint."""

from __future__ import annotations

import time

import pytest

from cronwrap.checkpoint import (
    Checkpoint,
    clear_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path / "checkpoints")


def test_save_creates_file(sdir):
    cp = save_checkpoint(sdir, "myjob", "page", 42)
    assert cp.job == "myjob"
    assert cp.name == "page"
    assert cp.value == 42


def test_load_returns_checkpoint(sdir):
    save_checkpoint(sdir, "myjob", "page", 99)
    cp = load_checkpoint(sdir, "myjob", "page")
    assert cp is not None
    assert cp.value == 99


def test_load_missing_returns_none(sdir):
    result = load_checkpoint(sdir, "myjob", "nonexistent")
    assert result is None


def test_clear_existing_returns_true(sdir):
    save_checkpoint(sdir, "myjob", "step", "done")
    assert clear_checkpoint(sdir, "myjob", "step") is True
    assert load_checkpoint(sdir, "myjob", "step") is None


def test_clear_missing_returns_false(sdir):
    assert clear_checkpoint(sdir, "myjob", "ghost") is False


def test_list_checkpoints_empty(sdir):
    assert list_checkpoints(sdir, "myjob") == []


def test_list_checkpoints_multiple(sdir):
    save_checkpoint(sdir, "myjob", "alpha", 1)
    save_checkpoint(sdir, "myjob", "beta", 2)
    save_checkpoint(sdir, "otherjob", "alpha", 3)
    names = list_checkpoints(sdir, "myjob")
    assert sorted(names) == ["alpha", "beta"]


def test_age_seconds_is_small(sdir):
    cp = save_checkpoint(sdir, "myjob", "ts", "now")
    assert cp.age_seconds() < 2.0


def test_checkpoint_value_complex(sdir):
    data = {"offset": 100, "ids": [1, 2, 3]}
    save_checkpoint(sdir, "myjob", "state", data)
    cp = load_checkpoint(sdir, "myjob", "state")
    assert cp is not None
    assert cp.value == data


def test_overwrite_checkpoint(sdir):
    save_checkpoint(sdir, "myjob", "cursor", 10)
    save_checkpoint(sdir, "myjob", "cursor", 20)
    cp = load_checkpoint(sdir, "myjob", "cursor")
    assert cp is not None
    assert cp.value == 20
