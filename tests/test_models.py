"""测试数据模型."""

import time
import pytest
from autorunx.models import ServiceInfo, ServiceStatus


def test_service_info_creation():
    """测试服务信息创建."""
    service = ServiceInfo(
        id="test-001",
        name="test-service",
        command="echo hello",
        auto_restart=True
    )
    
    assert service.id == "test-001"
    assert service.name == "test-service"
    assert service.command == "echo hello"
    assert service.status == ServiceStatus.STOPPED
    assert service.auto_restart is True
    assert service.restart_count == 0


def test_service_info_to_dict():
    """测试服务信息转字典。"""
    service = ServiceInfo(
        id="test-001",
        name="test-service",
        command="echo hello"
    )
    
    data = service.to_dict()
    
    assert data["id"] == "test-001"
    assert data["name"] == "test-service"
    assert data["command"] == "echo hello"
    assert data["status"] == "stopped"
    assert data["auto_restart"] is True


def test_service_info_from_dict():
    """测试从字典创建服务信息。"""
    data = {
        "id": "test-001",
        "name": "test-service",
        "command": "echo hello",
        "status": "running",
        "auto_restart": False,
        "created_at": time.time(),
        "updated_at": time.time(),
        "restart_count": 5,
        "max_restart_attempts": 3,
        "restart_delay": 10,
        "working_dir": "/tmp",
        "env_vars": {"ENV": "test"},
    }
    
    service = ServiceInfo.from_dict(data)
    
    assert service.id == "test-001"
    assert service.name == "test-service"
    assert service.status == ServiceStatus.RUNNING
    assert service.auto_restart is False
    assert service.restart_count == 5


def test_service_status_update():
    """测试状态更新。"""
    service = ServiceInfo(
        id="test-001",
        name="test-service",
        command="echo hello"
    )
    
    old_updated_at = service.updated_at
    time.sleep(0.01)  # 确保时间差异
    
    service.update_status(ServiceStatus.RUNNING)
    
    assert service.status == ServiceStatus.RUNNING
    assert service.updated_at > old_updated_at


def test_restart_count_operations():
    """测试重启计数操作。"""
    service = ServiceInfo(
        id="test-001",
        name="test-service",
        command="echo hello"
    )
    
    assert service.restart_count == 0
    
    service.increment_restart_count()
    assert service.restart_count == 1
    
    service.increment_restart_count()
    assert service.restart_count == 2
    
    service.reset_restart_count()
    assert service.restart_count == 0