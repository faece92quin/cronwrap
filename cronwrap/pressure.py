"""System resource pressure checks for cronwrap.

Allows jobs to be skipped or delayed when the host is under high
CPU, memory, or load-average pressure.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


class PressureExceeded(Exception):
    """Raised when a resource pressure threshold is breached."""


@dataclass
class PressureConfig:
    max_load_1: Optional[float] = None   # 1-minute load average ceiling
    max_load_5: Optional[float] = None   # 5-minute load average ceiling
    max_mem_pct: Optional[float] = None  # 0-100 percentage of used memory
    cpu_count: int = field(default_factory=os.cpu_count)  # type: ignore[arg-type]


def _load_averages() -> tuple[float, float, float]:
    """Return (1-min, 5-min, 15-min) load averages."""
    return os.getloadavg()


def _mem_used_pct() -> float:
    """Return approximate used-memory percentage by reading /proc/meminfo."""
    info: dict[str, int] = {}
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 2:
                    info[parts[0].rstrip(":")] = int(parts[1])
    except FileNotFoundError:
        # macOS / non-Linux: skip memory check
        return 0.0
    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", 0)
    if total == 0:
        return 0.0
    return (total - available) / total * 100.0


def check_pressure(cfg: PressureConfig) -> None:
    """Raise PressureExceeded if any configured threshold is breached."""
    if cfg.max_load_1 is not None or cfg.max_load_5 is not None:
        load1, load5, _ = _load_averages()
        if cfg.max_load_1 is not None and load1 > cfg.max_load_1:
            raise PressureExceeded(
                f"1-min load {load1:.2f} exceeds threshold {cfg.max_load_1}"
            )
        if cfg.max_load_5 is not None and load5 > cfg.max_load_5:
            raise PressureExceeded(
                f"5-min load {load5:.2f} exceeds threshold {cfg.max_load_5}"
            )

    if cfg.max_mem_pct is not None:
        used = _mem_used_pct()
        if used > cfg.max_mem_pct:
            raise PressureExceeded(
                f"Memory used {used:.1f}% exceeds threshold {cfg.max_mem_pct}%"
            )


def parse_pressure(args: object) -> Optional[PressureConfig]:
    """Build a PressureConfig from parsed CLI args, or return None."""
    load1 = getattr(args, "max_load_1", None)
    load5 = getattr(args, "max_load_5", None)
    mem = getattr(args, "max_mem_pct", None)
    if load1 is None and load5 is None and mem is None:
        return None
    return PressureConfig(
        max_load_1=float(load1) if load1 is not None else None,
        max_load_5=float(load5) if load5 is not None else None,
        max_mem_pct=float(mem) if mem is not None else None,
    )
