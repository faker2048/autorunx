"""数据模型定义."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class ServiceStatus(Enum):
    """服务状态枚举."""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    FAILED = "failed"
    STARTING = "starting"


@dataclass
class ServiceInfo:
    """服务信息数据类."""
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
        """转换为字典格式."""
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
        """从字典创建实例."""
        data = data.copy()
        if "status" in data:
            data["status"] = ServiceStatus(data["status"])
        return cls(**data)
    
    def update_status(self, status: ServiceStatus) -> None:
        """更新服务状态."""
        self.status = status
        self.updated_at = time.time()
    
    def increment_restart_count(self) -> None:
        """增加重启计数."""
        self.restart_count += 1
        self.updated_at = time.time()
    
    def reset_restart_count(self) -> None:
        """重置重启计数."""
        self.restart_count = 0
        self.updated_at = time.time()