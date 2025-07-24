"""交互式选择器."""

from typing import List, Optional
from .models import ServiceInfo


def select_service(services: List[ServiceInfo], prompt: str = "请选择服务") -> Optional[ServiceInfo]:
    """交互式选择服务."""
    if not services:
        print("没有可用的服务")
        return None
    
    if len(services) == 1:
        return services[0]
    
    print(f"\n{prompt}:")
    print("-" * 50)
    
    for i, service in enumerate(services, 1):
        status_color = _get_status_color(service.status.value)
        print(f"{i:2d}. {service.name:<20} [{status_color}{service.status.value}{_get_reset_color()}] {service.id}")
    
    print("-" * 50)
    
    while True:
        try:
            choice = input("请输入序号 (1-{}, q退出): ".format(len(services))).strip()
            
            if choice.lower() == 'q':
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(services):
                return services[index]
            else:
                print(f"请输入有效的序号 (1-{len(services)})")
        
        except (ValueError, KeyboardInterrupt):
            print("\n已取消操作")
            return None


def confirm_action(action: str, target: str) -> bool:
    """确认操作."""
    try:
        response = input(f"确定要{action} '{target}' 吗? (y/N): ").strip().lower()
        return response in ['y', 'yes', '是']
    except KeyboardInterrupt:
        print("\n已取消操作")
        return False


def _get_status_color(status: str) -> str:
    """获取状态颜色代码."""
    colors = {
        "running": "\033[32m",    # 绿色
        "stopped": "\033[31m",    # 红色  
        "paused": "\033[33m",     # 黄色
        "failed": "\033[91m",     # 亮红色
        "starting": "\033[36m",   # 青色
    }
    return colors.get(status, "")


def _get_reset_color() -> str:
    """获取颜色重置代码."""
    return "\033[0m"