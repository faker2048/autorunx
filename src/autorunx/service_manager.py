"""服务管理器 - 整合所有功能的核心类."""

import time
from typing import List, Optional, Dict, Any
from .models import ServiceInfo, ServiceStatus
from .config import ConfigManager
from .storage import ServiceStorage
from .process_manager import ProcessManager


class ServiceManager:
    """服务管理器."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.storage = ServiceStorage(self.config_manager)
        self.process_manager = ProcessManager(self.config_manager)
    
    def add_service(self, name: str, command: str, auto_restart: bool = True, 
                   working_dir: str = "", env_vars: Optional[Dict[str, str]] = None) -> ServiceInfo:
        """添加新服务."""
        service = self.storage.add_service(
            name=name,
            command=command,
            auto_restart=auto_restart,
            working_dir=working_dir,
            env_vars=env_vars
        )
        return service
    
    def start_service(self, service_id_or_name: str) -> bool:
        """启动服务."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False
        
        success = self.process_manager.start_service(service)
        if success:
            self.storage.update_service(service)
        return success
    
    def stop_service(self, service_id_or_name: str, force: bool = False) -> bool:
        """停止服务."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False
        
        success = self.process_manager.stop_service(service, force)
        if success:
            self.storage.update_service(service)
        return success
    
    def restart_service(self, service_id_or_name: str, force: bool = False) -> bool:
        """重启服务."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False
        
        success = self.process_manager.restart_service(service, force)
        if success:
            service.increment_restart_count()
            self.storage.update_service(service)
        return success
    
    def pause_service(self, service_id_or_name: str) -> bool:
        """暂停服务."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False
        
        success = self.process_manager.pause_service(service)
        if success:
            self.storage.update_service(service)
        return success
    
    def resume_service(self, service_id_or_name: str) -> bool:
        """恢复服务."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False
        
        success = self.process_manager.resume_service(service)
        if success:
            self.storage.update_service(service)
        return success
    
    def remove_service(self, service_id_or_name: str, force: bool = False) -> bool:
        """删除服务."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False
        
        # 如果服务在运行，先停止
        if service.status == ServiceStatus.RUNNING:
            if not force:
                return False  # 需要强制删除才能删除运行中的服务
            self.stop_service(service.id, force=True)
        
        return self.storage.remove_service(service.id)
    
    def get_service(self, service_id_or_name: str) -> Optional[ServiceInfo]:
        """获取服务信息."""
        return self.storage.find_service(service_id_or_name)
    
    def list_services(self) -> List[ServiceInfo]:
        """获取所有服务列表."""
        services = self.storage.get_all_services()
        
        # 更新服务状态
        for service in services:
            self._update_service_status(service)
        
        return services
    
    def get_service_status(self, service_id_or_name: str) -> Optional[Dict[str, Any]]:
        """获取服务详细状态."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return None
        
        # 更新状态
        self._update_service_status(service)
        
        # 获取进程信息
        process_info = self.process_manager.get_process_info(service)
        
        status_info = {
            "service": service,
            "process": process_info,
            "uptime": self._calculate_uptime(service, process_info),
        }
        
        return status_info
    
    def get_service_logs(self, service_id_or_name: str, lines: int = 100) -> Optional[List[str]]:
        """获取服务日志."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return None
        
        log_path = self.config_manager.get_service_log_path(service.id)
        
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if lines > 0 else all_lines
        except FileNotFoundError:
            return []
        except Exception:
            return None
    
    def clear_service_logs(self, service_id_or_name: str) -> bool:
        """清空服务日志."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False
        
        log_path = self.config_manager.get_service_log_path(service.id)
        
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
            return True
        except Exception:
            return False
    
    def _update_service_status(self, service: ServiceInfo) -> None:
        """更新服务状态."""
        if service.pid:
            if self.process_manager.is_process_running(service.pid):
                # 进程存在且状态不是运行中，更新状态
                if service.status != ServiceStatus.RUNNING and service.status != ServiceStatus.PAUSED:
                    service.update_status(ServiceStatus.RUNNING)
                    self.storage.update_service(service)
            else:
                # 进程不存在，更新状态
                service.pid = None
                service.update_status(ServiceStatus.STOPPED)
                self.storage.update_service(service)
        else:
            # 没有PID且状态不是停止，更新状态
            if service.status != ServiceStatus.STOPPED:
                service.update_status(ServiceStatus.STOPPED)
                self.storage.update_service(service)
    
    def _calculate_uptime(self, service: ServiceInfo, process_info: Optional[Dict[str, Any]]) -> Optional[float]:
        """计算服务运行时间."""
        if not process_info or not process_info.get("create_time"):
            return None
        
        return time.time() - process_info["create_time"]