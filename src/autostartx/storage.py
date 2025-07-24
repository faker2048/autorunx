"""服务数据存储管理."""

import json
import os
import uuid
from typing import Dict, List, Optional
from .models import ServiceInfo, ServiceStatus
from .config import ConfigManager


class ServiceStorage:
    """服务数据存储管理器."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.db_path = config_manager.get_services_db_path()
        self._services: Dict[str, ServiceInfo] = {}
        self.load_services()
    
    def load_services(self) -> None:
        """从文件加载服务数据."""
        if not os.path.exists(self.db_path):
            self._services = {}
            return
        
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._services = {}
            for service_id, service_data in data.items():
                try:
                    service = ServiceInfo.from_dict(service_data)
                    self._services[service_id] = service
                except Exception as e:
                    print(f"警告: 加载服务 {service_id} 失败: {e}")
                    
        except Exception as e:
            print(f"警告: 加载服务数据失败: {e}")
            self._services = {}
    
    def save_services(self) -> None:
        """保存服务数据到文件."""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            data = {}
            for service_id, service in self._services.items():
                data[service_id] = service.to_dict()
            
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"错误: 保存服务数据失败: {e}")
    
    def add_service(self, name: str, command: str, auto_restart: bool = True, 
                   working_dir: str = "", env_vars: Optional[Dict[str, str]] = None) -> ServiceInfo:
        """添加新服务."""
        service_id = self._generate_service_id()
        
        # 检查名称冲突
        if self.get_service_by_name(name):
            raise ValueError(f"服务名称 '{name}' 已存在")
        
        service = ServiceInfo(
            id=service_id,
            name=name,
            command=command,
            auto_restart=auto_restart,
            working_dir=working_dir or os.getcwd(),
            env_vars=env_vars or {},
            max_restart_attempts=self.config_manager.config.max_restart_attempts,
            restart_delay=self.config_manager.config.restart_delay,
        )
        
        self._services[service_id] = service
        self.save_services()
        return service
    
    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """根据ID获取服务."""
        return self._services.get(service_id)
    
    def get_service_by_name(self, name: str) -> Optional[ServiceInfo]:
        """根据名称获取服务."""
        for service in self._services.values():
            if service.name == name:
                return service
        return None
    
    def get_all_services(self) -> List[ServiceInfo]:
        """获取所有服务."""
        return list(self._services.values())
    
    def update_service(self, service: ServiceInfo) -> None:
        """更新服务信息."""
        if service.id in self._services:
            self._services[service.id] = service
            self.save_services()
        else:
            raise ValueError(f"服务 {service.id} 不存在")
    
    def remove_service(self, service_id: str) -> bool:
        """删除服务."""
        if service_id in self._services:
            del self._services[service_id]
            self.save_services()
            return True
        return False
    
    def find_service(self, service_id_or_name: str) -> Optional[ServiceInfo]:
        """根据ID或名称查找服务."""
        # 先尝试按ID查找
        service = self.get_service(service_id_or_name)
        if service:
            return service
        
        # 再尝试按名称查找
        return self.get_service_by_name(service_id_or_name)
    
    def get_services_by_status(self, status: ServiceStatus) -> List[ServiceInfo]:
        """根据状态获取服务列表."""
        return [service for service in self._services.values() if service.status == status]
    
    def _generate_service_id(self) -> str:
        """生成唯一的服务ID."""
        while True:
            service_id = str(uuid.uuid4())[:8]
            if service_id not in self._services:
                return service_id