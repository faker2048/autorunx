#!/usr/bin/env python3
"""Autostartx 基本使用示例."""

import time
import sys
import os

# 添加项目路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autostartx.service_manager import ServiceManager
from autostartx.models import ServiceStatus


def main():
    """基本使用示例."""
    print("=== Autostartx 基本使用示例 ===\n")

    # 创建服务管理器
    manager = ServiceManager()

    # 添加一个简单的服务
    print("1. 添加一个 echo 服务")
    echo_service = manager.add_service(
        name="demo-echo",
        command="echo 'Hello from Autostartx!'",
        auto_restart=False,  # echo 命令运行完就退出，不需要重启
    )
    print(f"   服务已添加: {echo_service.name} ({echo_service.id})")

    # 添加一个持续运行的服务
    print("\n2. 添加一个 HTTP 服务")
    web_service = manager.add_service(
        name="demo-web", command="python -m http.server 8080", auto_restart=True
    )
    print(f"   服务已添加: {web_service.name} ({web_service.id})")

    # 查看所有服务
    print("\n3. 查看所有服务")
    services = manager.list_services()
    for service in services:
        print(f"   - {service.name}: {service.status.value}")

    # 启动 echo 服务
    print("\n4. 启动 echo 服务")
    if manager.start_service(echo_service.id):
        print("   启动成功")
        time.sleep(1)  # 等待命令执行完成

        # 查看日志
        logs = manager.get_service_logs(echo_service.id)
        if logs:
            print("   日志输出:")
            for line in logs[-5:]:  # 显示最后5行
                print(f"     {line.strip()}")

    # 启动 web 服务
    print("\n5. 启动 web 服务")
    if manager.start_service(web_service.id):
        print("   启动成功")
        print("   可以在浏览器中访问 http://localhost:8080")
        time.sleep(2)

        # 查看服务状态
        status_info = manager.get_service_status(web_service.id)
        if status_info:
            service = status_info["service"]
            process_info = status_info["process"]
            print(f"   服务状态: {service.status.value}")
            if process_info:
                print(f"   进程ID: {process_info['pid']}")
                print(f"   内存使用: {process_info['memory']['rss'] / 1024 / 1024:.1f} MB")

    # 停止 web 服务
    print("\n6. 停止 web 服务")
    if manager.stop_service(web_service.id):
        print("   停止成功")

    # 删除服务
    print("\n7. 清理服务")
    manager.remove_service(echo_service.id, force=True)
    manager.remove_service(web_service.id, force=True)
    print("   服务已清理")

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main()
