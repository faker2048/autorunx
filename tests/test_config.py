"""测试配置管理。"""

import os
import tempfile
import pytest
from pathlib import Path
from autorunx.config import Config, ConfigManager


def test_config_defaults():
    """测试默认配置。"""
    config = Config()
    
    assert config.log_level == "INFO"
    assert config.max_log_size == "10MB"
    assert config.log_retention_days == 7
    assert config.auto_restart is True
    assert config.restart_delay == 5
    assert config.max_restart_attempts == 3
    assert config.interactive_mode is True
    assert config.color_output is True


def test_config_manager_creation():
    """测试配置管理器创建。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.toml")
        manager = ConfigManager(config_path)
        
        assert manager.config_path == config_path
        assert isinstance(manager.config, Config)
        
        # 检查目录是否创建
        assert os.path.exists(manager.config.config_dir)
        assert os.path.exists(manager.config.data_dir)
        assert os.path.exists(manager.config.log_dir)


def test_config_save_and_load():
    """测试配置保存和加载。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.toml")
        
        # 创建配置管理器并修改配置
        manager = ConfigManager(config_path)
        manager.config.log_level = "DEBUG"
        manager.config.max_restart_attempts = 5
        manager.save_config()
        
        # 创建新的管理器并验证配置已加载
        new_manager = ConfigManager(config_path)
        assert new_manager.config.log_level == "DEBUG"
        assert new_manager.config.max_restart_attempts == 5


def test_get_paths():
    """测试路径获取方法。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.toml")
        manager = ConfigManager(config_path)
        
        # 测试数据库路径
        db_path = manager.get_services_db_path()
        assert db_path.endswith("services.json")
        assert manager.config.data_dir in db_path
        
        # 测试日志路径
        log_path = manager.get_service_log_path("test-service")
        assert log_path.endswith("test-service.log")
        assert manager.config.log_dir in log_path