"""Tests for cronwrap.semaphore."""
import json
import os
from pathlib import Path

import pytest

from cronwrap.semaphore import (
    SemaphoreConfig,
    SemaphoreExhausted,
    _load_holders,
    _prune_dead,
    _state_path,
    parse_semaphore,
    semaphore_slot,
)


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path / "sems")


def _cfg(sdir: str, slots: int = 2, name: str = "testjob") -> SemaphoreConfig:
    return SemaphoreConfig(name=name, slots=slots, state_dir=sdir)


def test_acquire_creates_state_file(sdir: str) -> None:
    cfg = _cfg(sdir)
    with semaphore_slot(cfg) as idx:
        path = _state_path(cfg)
        assert path.exists()
        holders = _load_holders(path)
        assert len(holders) == 1
        assert holders[0]["pid"] == os.getpid()
    assert idx == 0


def test_slot_released_on_exit(sdir: str) -> None:
    cfg = _cfg(sdir)
    with semaphore_slot(cfg):
        pass
    holders = _load_holders(_state_path(cfg))
    live = [h for h in holders if h.get("pid") == os.getpid()]
    assert live == []


def test_slot_released_on_exception(sdir: str) -> None:
    cfg = _cfg(sdir)
    with pytest.raises(RuntimeError):
        with semaphore_slot(cfg):
            raise RuntimeError("boom")
    holders = _load_holders(_state_path(cfg))
    live = [h for h in holders if h.get("pid") == os.getpid()]
    assert live == []


def test_single_slot_exhausted_raises(sdir: str) -> None:
    cfg = _cfg(sdir, slots=1)
    path = _state_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Inject a fake live entry using our own PID so prune keeps it
    path.write_text(json.dumps([{"pid": os.getpid(), "acquired_at": 0.0}]))
    with pytest.raises(SemaphoreExhausted, match="full"):
        with semaphore_slot(cfg):
            pass


def test_dead_pid_pruned_allows_entry(sdir: str) -> None:
    cfg = _cfg(sdir, slots=1)
    path = _state_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    # PID 999999999 almost certainly does not exist
    path.write_text(json.dumps([{"pid": 999999999, "acquired_at": 0.0}]))
    with semaphore_slot(cfg) as idx:
        assert idx == 0


def test_prune_dead_removes_nonexistent_pid() -> None:
    holders = [{"pid": 999999999}, {"pid": os.getpid()}]
    result = _prune_dead(holders)
    assert len(result) == 1
    assert result[0]["pid"] == os.getpid()


def test_parse_semaphore_none_when_no_name(sdir: str) -> None:
    assert parse_semaphore(None, "3", sdir) is None


def test_parse_semaphore_none_when_no_slots(sdir: str) -> None:
    assert parse_semaphore("job", None, sdir) is None


def test_parse_semaphore_none_when_zero_slots(sdir: str) -> None:
    assert parse_semaphore("job", "0", sdir) is None


def test_parse_semaphore_returns_config(sdir: str) -> None:
    cfg = parse_semaphore("myjob", "4", sdir)
    assert cfg is not None
    assert cfg.name == "myjob"
    assert cfg.slots == 4
    assert cfg.state_dir == sdir
