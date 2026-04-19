"""Tests for cronwrap.config."""

import pytest
from cronwrap.config import load_config_dict, config_to_json, JobConfig


def _base() -> dict:
    return {"name": "backup", "command": "tar czf /tmp/out.tgz /data"}


def test_minimal_config():
    cfg = load_config_dict(_base())
    assert cfg.name == "backup"
    assert cfg.command == "tar czf /tmp/out.tgz /data"
    assert cfg.retries == 0
    assert cfg.timeout is None


def test_full_config():
    data = {
        **_base(),
        "retries": 3,
        "timeout": 120,
        "schedule": "0 2 * * *",
        "required_env": ["AWS_KEY"],
        "alert_on_failure": True,
        "webhook_url": "https://hooks.example.com/xyz",
    }
    cfg = load_config_dict(data)
    assert cfg.retries == 3
    assert cfg.timeout == 120
    assert cfg.schedule == "0 2 * * *"
    assert "AWS_KEY" in cfg.required_env
    assert cfg.alert_on_failure is True
    assert cfg.webhook_url == "https://hooks.example.com/xyz"


def test_missing_name_raises():
    with pytest.raises(ValueError, match="name"):
        load_config_dict({"command": "echo hi"})


def test_missing_command_raises():
    with pytest.raises(ValueError, match="command"):
        load_config_dict({"name": "myjob"})


def test_unknown_keys_ignored():
    data = {**_base(), "unknown_key": "value"}
    cfg = load_config_dict(data)
    assert not hasattr(cfg, "unknown_key")


def test_config_to_json():
    cfg = load_config_dict(_base())
    out = config_to_json(cfg)
    assert "backup" in out
    assert "command" in out


def test_load_config_file_not_found():
    from cronwrap.config import load_config_file
    with pytest.raises(FileNotFoundError):
        load_config_file("/nonexistent/path/job.toml")
