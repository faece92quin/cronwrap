"""Helpers for capturing and validating the runtime environment."""
from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvSnapshot:
    python_version: str
    platform: str
    hostname: str
    user: str
    env_vars: Dict[str, str] = field(default_factory=dict)


def capture_env(include_vars: Optional[List[str]] = None) -> EnvSnapshot:
    """Capture relevant runtime environment details.

    Args:
        include_vars: explicit list of env-var names to capture.
                      Defaults to a safe minimal set.
    """
    safe_defaults = ["PATH", "HOME", "USER", "SHELL", "LANG", "TZ"]
    names = include_vars if include_vars is not None else safe_defaults
    env_vars = {k: os.environ.get(k, "") for k in names}

    return EnvSnapshot(
        python_version=sys.version,
        platform=platform.platform(),
        hostname=platform.node(),
        user=os.environ.get("USER", os.environ.get("LOGNAME", "unknown")),
        env_vars=env_vars,
    )


def check_required_vars(names: List[str]) -> List[str]:
    """Return names of required env vars that are missing."""
    return [n for n in names if not os.environ.get(n)]
