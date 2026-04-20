"""Dependency checking: verify external commands exist before running a job."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DependencyConfig:
    """Configuration for dependency checks."""
    required: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)


@dataclass
class DependencyResult:
    """Result of a dependency check."""
    name: str
    found: bool
    path: Optional[str]
    required: bool

    def __str__(self) -> str:
        status = "OK" if self.found else "MISSING"
        kind = "required" if self.required else "optional"
        path_info = f" ({self.path})" if self.path else ""
        return f"[{status}] {self.name}{path_info} ({kind})"


def check_dependency(name: str, required: bool = True) -> DependencyResult:
    """Check whether a single command exists on PATH."""
    resolved = shutil.which(name)
    return DependencyResult(
        name=name,
        found=resolved is not None,
        path=resolved,
        required=required,
    )


def check_dependencies(config: DependencyConfig) -> List[DependencyResult]:
    """Check all required and optional dependencies."""
    results: List[DependencyResult] = []
    for name in config.required:
        results.append(check_dependency(name, required=True))
    for name in config.optional:
        results.append(check_dependency(name, required=False))
    return results


class MissingDependencyError(RuntimeError):
    """Raised when one or more required dependencies are not found."""

    def __init__(self, missing: List[str]) -> None:
        self.missing = missing
        names = ", ".join(missing)
        super().__init__(f"Missing required dependencies: {names}")


def assert_dependencies(config: DependencyConfig) -> List[DependencyResult]:
    """Check dependencies and raise if any required ones are absent.

    Returns the full list of results (including optional) on success.
    """
    results = check_dependencies(config)
    missing = [r.name for r in results if r.required and not r.found]
    if missing:
        raise MissingDependencyError(missing)
    return results
