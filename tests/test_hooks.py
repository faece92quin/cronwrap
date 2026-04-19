"""Tests for cronwrap.hooks."""
import pytest
from unittest.mock import patch, MagicMock
import subprocess

from cronwrap.hooks import HookConfig, _run_hook, run_pre_hooks, run_post_hooks


def _completed(returncode=0, stderr=""):
    r = MagicMock()
    r.returncode = returncode
    r.stderr = stderr
    return r


def test_run_hook_success():
    with patch("subprocess.run", return_value=_completed(0)) as m:
        assert _run_hook("echo hi") is True
        m.assert_called_once()


def test_run_hook_failure():
    with patch("subprocess.run", return_value=_completed(1, "bad")):
        assert _run_hook("false") is False


def test_run_hook_timeout():
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
        assert _run_hook("sleep 999") is False


def test_run_pre_hooks_all_succeed():
    cfg = HookConfig(pre_hooks=["echo a", "echo b"])
    with patch("cronwrap.hooks._run_hook", return_value=True) as m:
        result = run_pre_hooks(cfg)
        assert result is True
        assert m.call_count == 2


def test_run_pre_hooks_stops_on_failure():
    cfg = HookConfig(pre_hooks=["fail", "echo b"], stop_on_pre_failure=True)
    with patch("cronwrap.hooks._run_hook", return_value=False) as m:
        result = run_pre_hooks(cfg)
        assert result is False
        assert m.call_count == 1  # stopped after first


def test_run_pre_hooks_continues_on_failure_when_disabled():
    cfg = HookConfig(pre_hooks=["fail", "echo b"], stop_on_pre_failure=False)
    with patch("cronwrap.hooks._run_hook", return_value=False) as m:
        result = run_pre_hooks(cfg)
        assert result is True  # does not abort
        assert m.call_count == 2


def test_run_post_hooks_runs_all_even_on_failure():
    cfg = HookConfig(post_hooks=["fail", "also_fail"])
    with patch("cronwrap.hooks._run_hook", return_value=False) as m:
        run_post_hooks(cfg)  # should not raise
        assert m.call_count == 2


def test_empty_hooks():
    cfg = HookConfig()
    assert run_pre_hooks(cfg) is True
    run_post_hooks(cfg)  # no error
