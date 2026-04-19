"""Load and validate cronwrap job configuration from a TOML or dict source."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import json
import os

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: Optional[str] = None
    retries: int = 0
    timeout: Optional[int] = None
    required_env: List[str] = field(default_factory=list)
    pre_hooks: List[str] = field(default_factory=list)
    post_hooks: List[str] = field(default_factory=list)
    alert_on_failure: bool = False
    webhook_url: Optional[str] = None


def _from_dict(data: dict) -> JobConfig:
    allowed = JobConfig.__dataclass_fields__.keys()
    filtered = {k: v for k, v in data.items() if k in allowed}
    if "name" not in filtered or "command" not in filtered:
        raise ValueError("Job config must include 'name' and 'command'.")
    return JobConfig(**filtered)


def load_config_file(path: str) -> JobConfig:
    """Load a job config from a TOML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    if tomllib is None:
        raise RuntimeError("tomllib/tomli is required to load TOML configs.")
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return _from_dict(data.get("job", data))


def load_config_dict(data: dict) -> JobConfig:
    """Load a job config from a plain dictionary."""
    return _from_dict(data)


def config_to_json(cfg: JobConfig) -> str:
    import dataclasses
    return json.dumps(dataclasses.asdict(cfg), indent=2)
