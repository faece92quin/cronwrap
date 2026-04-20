"""Tests for cronwrap.dependency."""

import pytest

from cronwrap.dependency import (
    DependencyConfig,
    DependencyResult,
    MissingDependencyError,
    assert_dependencies,
    check_dependencies,
    check_dependency,
)


# ---------------------------------------------------------------------------
# check_dependency
# ---------------------------------------------------------------------------

def test_check_dependency_found_python():
    """'python' or 'python3' should be resolvable in any test environment."""
    import sys, shutil
    name = "python3" if shutil.which("python3") else "python"
    result = check_dependency(name, required=True)
    assert result.found is True
    assert result.path is not None
    assert result.name == name
    assert result.required is True


def test_check_dependency_missing():
    result = check_dependency("__no_such_binary_xyz__", required=False)
    assert result.found is False
    assert result.path is None
    assert result.required is False


def test_dependency_result_str_found():
    r = DependencyResult(name="git", found=True, path="/usr/bin/git", required=True)
    s = str(r)
    assert "OK" in s
    assert "git" in s
    assert "required" in s


def test_dependency_result_str_missing():
    r = DependencyResult(name="ghost", found=False, path=None, required=False)
    s = str(r)
    assert "MISSING" in s
    assert "optional" in s


# ---------------------------------------------------------------------------
# check_dependencies
# ---------------------------------------------------------------------------

def test_check_dependencies_empty_config():
    cfg = DependencyConfig()
    results = check_dependencies(cfg)
    assert results == []


def test_check_dependencies_mixed(monkeypatch):
    import shutil
    real_which = shutil.which

    def fake_which(name):
        return "/usr/bin/" + name if name == "git" else None

    monkeypatch.setattr(shutil, "which", fake_which)
    cfg = DependencyConfig(required=["git"], optional=["curl"])
    results = check_dependencies(cfg)
    assert len(results) == 2
    git_r = next(r for r in results if r.name == "git")
    curl_r = next(r for r in results if r.name == "curl")
    assert git_r.found is True and git_r.required is True
    assert curl_r.found is False and curl_r.required is False


# ---------------------------------------------------------------------------
# assert_dependencies
# ---------------------------------------------------------------------------

def test_assert_dependencies_all_present(monkeypatch):
    import shutil
    monkeypatch.setattr(shutil, "which", lambda n: f"/usr/bin/{n}")
    cfg = DependencyConfig(required=["git", "curl"])
    results = assert_dependencies(cfg)
    assert all(r.found for r in results)


def test_assert_dependencies_raises_on_missing(monkeypatch):
    import shutil
    monkeypatch.setattr(shutil, "which", lambda n: None)
    cfg = DependencyConfig(required=["git", "curl"], optional=["jq"])
    with pytest.raises(MissingDependencyError) as exc_info:
        assert_dependencies(cfg)
    assert "git" in exc_info.value.missing
    assert "curl" in exc_info.value.missing
    assert "jq" not in exc_info.value.missing


def test_missing_dependency_error_message():
    err = MissingDependencyError(["foo", "bar"])
    assert "foo" in str(err)
    assert "bar" in str(err)
