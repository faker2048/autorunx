"""测试服务存储。"""

import os
import tempfile
import pytest
from autostartx.config import ConfigManager
from autostartx.storage import ServiceStorage
from autostartx.models import ServiceInfo, ServiceStatus


@pytest.fixture
def storage():
    """创建测试用的存储实例。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.toml")
        config_manager = ConfigManager(config_path)
        # 确保使用独立的数据目录
        config_manager.config.data_dir = os.path.join(temp_dir, "data")
        config_manager.config.log_dir = os.path.join(temp_dir, "logs")
        yield ServiceStorage(config_manager)


def test_add_service(storage):
    """测试添加服务。"""
    service = storage.add_service(
        name="test-service",
        command="echo hello",
        auto_restart=True
    )
    
    assert service.name == "test-service"
    assert service.command == "echo hello"
    assert service.auto_restart is True
    assert len(service.id) == 8  # UUID前8位
    assert service.status == ServiceStatus.STOPPED


def test_add_duplicate_service(storage):
    """测试添加重复名称的服务。"""
    storage.add_service(name="test-service", command="echo hello")
    
    with pytest.raises(ValueError, match="服务名称 'test-service' 已存在"):
        storage.add_service(name="test-service", command="echo world")


def test_get_service(storage):
    """测试获取服务。"""
    # 添加服务
    original_service = storage.add_service(
        name="test-service", 
        command="echo hello"
    )
    
    # 按ID获取
    service = storage.get_service(original_service.id)
    assert service is not None
    assert service.id == original_service.id
    assert service.name == "test-service"
    
    # 获取不存在的服务
    assert storage.get_service("nonexistent") is None


def test_get_service_by_name(storage):
    """测试按名称获取服务。"""
    # 添加服务
    original_service = storage.add_service(
        name="test-service",
        command="echo hello"
    )
    
    # 按名称获取
    service = storage.get_service_by_name("test-service")
    assert service is not None
    assert service.name == "test-service"
    assert service.id == original_service.id
    
    # 获取不存在的服务
    assert storage.get_service_by_name("nonexistent") is None


def test_find_service(storage):
    """测试查找服务（ID或名称）。"""
    # 添加服务
    original_service = storage.add_service(
        name="test-service",
        command="echo hello"
    )
    
    # 按ID查找
    service = storage.find_service(original_service.id)
    assert service is not None
    assert service.id == original_service.id
    
    # 按名称查找
    service = storage.find_service("test-service")
    assert service is not None
    assert service.name == "test-service"
    
    # 查找不存在的服务
    assert storage.find_service("nonexistent") is None


def test_get_all_services(storage):
    """测试获取所有服务。"""
    # 初始应该为空
    assert len(storage.get_all_services()) == 0
    
    # 添加服务
    storage.add_service(name="service-1", command="echo 1")
    storage.add_service(name="service-2", command="echo 2")
    
    services = storage.get_all_services()
    assert len(services) == 2
    
    service_names = [s.name for s in services]
    assert "service-1" in service_names
    assert "service-2" in service_names


def test_update_service(storage):
    """测试更新服务。"""
    # 添加服务
    service = storage.add_service(name="test-service", command="echo hello")
    original_updated_at = service.updated_at
    
    # 修改服务
    service.update_status(ServiceStatus.RUNNING)
    service.pid = 1234
    
    # 更新存储
    storage.update_service(service)
    
    # 重新获取验证
    updated_service = storage.get_service(service.id)
    assert updated_service.status == ServiceStatus.RUNNING
    assert updated_service.pid == 1234
    assert updated_service.updated_at > original_updated_at


def test_remove_service(storage):
    """测试删除服务。"""
    # 添加服务
    service = storage.add_service(name="test-service", command="echo hello")
    service_id = service.id
    
    # 确认服务存在
    assert storage.get_service(service_id) is not None
    
    # 删除服务
    result = storage.remove_service(service_id)
    assert result is True
    
    # 确认服务已删除
    assert storage.get_service(service_id) is None
    
    # 删除不存在的服务
    result = storage.remove_service("nonexistent")
    assert result is False


def test_get_services_by_status(storage):
    """测试按状态获取服务。"""
    # 添加服务
    service1 = storage.add_service(name="service-1", command="echo 1")
    service2 = storage.add_service(name="service-2", command="echo 2")
    
    # 修改状态
    service1.update_status(ServiceStatus.RUNNING)
    storage.update_service(service1)
    
    # 测试按状态获取
    running_services = storage.get_services_by_status(ServiceStatus.RUNNING)
    stopped_services = storage.get_services_by_status(ServiceStatus.STOPPED)
    
    assert len(running_services) == 1
    assert len(stopped_services) == 1
    assert running_services[0].id == service1.id
    assert stopped_services[0].id == service2.id


def test_persistence(storage):
    """测试数据持久化。"""
    # 添加服务
    service = storage.add_service(name="test-service", command="echo hello")
    service_id = service.id
    
    # 创建新的存储实例（模拟重启）
    new_storage = ServiceStorage(storage.config_manager)
    
    # 验证数据已持久化
    loaded_service = new_storage.get_service(service_id)
    assert loaded_service is not None
    assert loaded_service.name == "test-service"
    assert loaded_service.command == "echo hello"