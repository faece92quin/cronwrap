"""Tests for cronwrap.watchdog and cronwrap.watchdog_cli."""
from __future__ import annotations

import time
import pytest
from pathlib import Path

from cronwrap.watchdog import (
    WatchdogConfig,
    check_watchdog,
    record_heartbeat,
    parse_watchdog,
)
from cronwrap.watchdog_cli import run_watchdog_cli


@pytest.fixture()
def sdir(tmp_path: Path) -> str:
    return str(tmp_path / "wd")


def _cfg(sdir: str, interval: int = 300, grace: int = 60) -> WatchdogConfig:
    return WatchdogConfig(job_name="myjob", expected_interval_seconds=interval, grace_seconds=grace, state_dir=sdir)


# --- watchdog core ---

def test_no_heartbeat_is_overdue(sdir: str) -> None:
    status = check_watchdog(_cfg(sdir))
    assert status.overdue is True
    assert status.last_seen is None


def test_fresh_heartbeat_not_overdue(sdir: str) -> None:
    cfg = _cfg(sdir)
    record_heartbeat(cfg)
    status = check_watchdog(cfg)
    assert status.overdue is False
    assert status.seconds_overdue == 0.0


def test_old_heartbeat_is_overdue(sdir: str) -> None:
    cfg = _cfg(sdir, interval=300, grace=60)
    old_ts = time.time() - 400  # 400s ago, beyond interval+grace
    record_heartbeat(cfg, ts=old_ts)
    status = check_watchdog(cfg)
    assert status.overdue is True
    assert status.seconds_overdue > 0


def test_heartbeat_within_grace_not_overdue(sdir: str) -> None:
    cfg = _cfg(sdir, interval=300, grace=60)
    ts = time.time() - 330  # 330s ago, within 300+60=360 window
    record_heartbeat(cfg, ts=ts)
    status = check_watchdog(cfg)
    assert status.overdue is False


def test_record_heartbeat_creates_file(sdir: str) -> None:
    cfg = _cfg(sdir)
    record_heartbeat(cfg)
    state_file = Path(sdir) / "myjob.json"
    assert state_file.exists()


# --- parse_watchdog ---

def test_parse_watchdog_none_on_empty(sdir: str) -> None:
    assert parse_watchdog("job", None, state_dir=sdir) is None
    assert parse_watchdog("job", "", state_dir=sdir) is None


def test_parse_watchdog_minutes(sdir: str) -> None:
    cfg = parse_watchdog("job", "5m", state_dir=sdir)
    assert cfg is not None
    assert cfg.expected_interval_seconds == 300


def test_parse_watchdog_hours(sdir: str) -> None:
    cfg = parse_watchdog("job", "2h", state_dir=sdir)
    assert cfg is not None
    assert cfg.expected_interval_seconds == 7200


def test_parse_watchdog_grace_minutes(sdir: str) -> None:
    cfg = parse_watchdog("job", "10m", "2m", state_dir=sdir)
    assert cfg is not None
    assert cfg.grace_seconds == 120


# --- watchdog CLI ---

def test_cli_touch_records_heartbeat(sdir: str) -> None:
    rc = run_watchdog_cli(["touch", "myjob", "--interval", "5m", "--state-dir", sdir])
    assert rc == 0
    assert (Path(sdir) / "myjob.json").exists()


def test_cli_show_ok(sdir: str) -> None:
    run_watchdog_cli(["touch", "myjob", "--interval", "5m", "--state-dir", sdir])
    rc = run_watchdog_cli(["show", "myjob", "--interval", "5m", "--state-dir", sdir])
    assert rc == 0


def test_cli_show_overdue_returns_1(sdir: str) -> None:
    rc = run_watchdog_cli(["show", "myjob", "--interval", "5m", "--state-dir", sdir])
    assert rc == 1


def test_cli_show_json(sdir: str, capsys: pytest.CaptureFixture) -> None:
    import json
    run_watchdog_cli(["touch", "myjob", "--interval", "5m", "--state-dir", sdir])
    run_watchdog_cli(["show", "myjob", "--interval", "5m", "--state-dir", sdir, "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["job_name"] == "myjob"
    assert "overdue" in data
