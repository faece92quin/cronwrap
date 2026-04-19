"""Pre/post execution hooks for cronwrap."""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional

log = logging.getLogger(__name__)


@dataclass
class HookConfig:
    pre_hooks: List[str] = field(default_factory=list)
    post_hooks: List[str] = field(default_factory=list)
    stop_on_pre_failure: bool = True


def _run_hook(cmd: str, timeout: int = 30) -> bool:
    """Run a single shell hook command. Returns True on success."""
    log.debug("Running hook: %s", cmd)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            log.warning(
                "Hook failed (exit %d): %s\nstderr: %s",
                result.returncode,
                cmd,
                result.stderr.strip(),
            )
            return False
        log.debug("Hook succeeded: %s", cmd)
        return True
    except subprocess.TimeoutExpired:
        log.error("Hook timed out after %ds: %s", timeout, cmd)
        return False
    except Exception as exc:  # pragma: no cover
        log.error("Hook error (%s): %s", cmd, exc)
        return False


def run_pre_hooks(config: HookConfig) -> bool:
    """Run all pre-hooks. Returns False if any fail and stop_on_pre_failure is set."""
    for cmd in config.pre_hooks:
        ok = _run_hook(cmd)
        if not ok and config.stop_on_pre_failure:
            log.error("Pre-hook failed, aborting job: %s", cmd)
            return False
    return True


def run_post_hooks(config: HookConfig) -> None:
    """Run all post-hooks (failures are logged but do not raise)."""
    for cmd in config.post_hooks:
        _run_hook(cmd)
