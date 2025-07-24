"""pytest配置文件。"""

import shutil
import tempfile

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境。"""
    # 在这里可以添加全局测试设置
    pass


@pytest.fixture
def temp_dir():
    """提供临时目录。"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)
