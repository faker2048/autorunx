"""Data model definitions."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ServiceStatus(Enum):
    """Service status enumeration."""

    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    FAILED = "failed"
    STARTING = "starting"


@dataclass
class ServiceInfo:
    """Service information data class."""

    id: str
    name: str
    command: str
    status: ServiceStatus = ServiceStatus.STOPPED
    pid: Optional[int] = None
    auto_restart: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    restart_count: int = 0
    max_restart_attempts: int = 3
    restart_delay: int = 5
    working_dir: str = ""
    env_vars: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "status": self.status.value,
            "pid": self.pid,
            "auto_restart": self.auto_restart,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "restart_count": self.restart_count,
            "max_restart_attempts": self.max_restart_attempts,
            "restart_delay": self.restart_delay,
            "working_dir": self.working_dir,
            "env_vars": self.env_vars,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceInfo":
        """Create instance from dictionary."""
        data = data.copy()
        if "status" in data:
            data["status"] = ServiceStatus(data["status"])
        return cls(**data)

    def update_status(self, status: ServiceStatus) -> None:
        """Update service status."""
        self.status = status
        self.updated_at = time.time()

    def increment_restart_count(self) -> None:
        """Increment restart count."""
        self.restart_count += 1
        self.updated_at = time.time()

    def reset_restart_count(self) -> None:
        """Reset restart count."""
        self.restart_count = 0
        self.updated_at = time.time()
