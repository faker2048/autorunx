"""进程监控和自动重启服务."""

import time
import threading
from typing import Dict, List
from .service_manager import ServiceManager
from .models import ServiceStatus


class ServiceMonitor:
    """服务监控器."""
    
    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self._monitoring = False
        self._monitor_thread = None
        self._check_interval = 5  # 检查间隔（秒）
    
    def start_monitoring(self) -> None:
        """开始监控."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("🔍 服务监控已启动")
    
    def stop_monitoring(self) -> None:
        """停止监控."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10)
        print("⏹️ 服务监控已停止")
    
    def _monitor_loop(self) -> None:
        """监控主循环."""
        while self._monitoring:
            try:
                self._check_services()
                time.sleep(self._check_interval)
            except Exception as e:
                print(f"监控服务时发生错误: {e}")
                time.sleep(self._check_interval)
    
    def _check_services(self) -> None:
        """检查所有服务状态."""
        services = self.service_manager.list_services()
        
        for service in services:
            # 只监控应该运行且启用自动重启的服务
            if not service.auto_restart:
                continue
            
            # 检查进程状态
            if service.status == ServiceStatus.RUNNING and service.pid:
                if not self.service_manager.process_manager.is_process_running(service.pid):
                    # 进程意外退出，需要重启
                    self._handle_service_crash(service)
            
            elif service.status == ServiceStatus.STARTING:
                # 检查启动是否超时
                if time.time() - service.updated_at > 30:  # 30秒启动超时
                    service.update_status(ServiceStatus.FAILED)
                    self.service_manager.storage.update_service(service)
                    print(f"⚠️ 服务 {service.name} 启动超时")
    
    def _handle_service_crash(self, service) -> None:
        """处理服务崩溃."""
        print(f"⚠️ 检测到服务 {service.name} 意外退出")
        
        # 更新状态
        service.pid = None
        service.update_status(ServiceStatus.STOPPED)
        
        # 检查重启次数限制
        if service.restart_count >= service.max_restart_attempts:
            print(f"❌ 服务 {service.name} 达到最大重启次数 ({service.max_restart_attempts})")
            service.update_status(ServiceStatus.FAILED)
            self.service_manager.storage.update_service(service)
            return
        
        # 等待重启延迟
        if service.restart_delay > 0:
            print(f"⏳ 等待 {service.restart_delay} 秒后重启服务 {service.name}")
            time.sleep(service.restart_delay)
        
        # 尝试重启
        print(f"🔄 正在重启服务 {service.name} (第 {service.restart_count + 1} 次)")
        
        service.update_status(ServiceStatus.STARTING)
        self.service_manager.storage.update_service(service)
        
        if self.service_manager.process_manager.start_service(service):
            service.increment_restart_count()
            print(f"✅ 服务 {service.name} 重启成功")
        else:
            service.update_status(ServiceStatus.FAILED)
            print(f"❌ 服务 {service.name} 重启失败")
        
        self.service_manager.storage.update_service(service)


class AutoRestartManager:
    """自动重启管理器 - 可独立运行的监控服务."""
    
    def __init__(self, config_path: str = None):
        self.service_manager = ServiceManager(config_path)
        self.monitor = ServiceMonitor(self.service_manager)
        self._running = False
    
    def start(self) -> None:
        """启动自动重启管理器."""
        if self._running:
            return
        
        print("🚀 Autostartx 自动重启管理器启动")
        self._running = True
        
        try:
            # 启动监控
            self.monitor.start_monitoring()
            
            # 主循环
            while self._running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n收到中断信号，正在关闭...")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """停止自动重启管理器."""
        if not self._running:
            return
        
        print("🛑 正在停止自动重启管理器...")
        self._running = False
        self.monitor.stop_monitoring()
        print("✅ 自动重启管理器已停止")
    
    def status(self) -> Dict[str, any]:
        """获取监控状态."""
        services = self.service_manager.list_services()
        
        status_info = {
            "monitoring": self.monitor._monitoring,
            "total_services": len(services),
            "running_services": len([s for s in services if s.status == ServiceStatus.RUNNING]),
            "failed_services": len([s for s in services if s.status == ServiceStatus.FAILED]),
            "auto_restart_enabled": len([s for s in services if s.auto_restart]),
        }
        
        return status_info
    
    def get_service_health(self) -> List[Dict[str, any]]:
        """获取服务健康状态."""
        services = self.service_manager.list_services()
        health_info = []
        
        for service in services:
            status_info = self.service_manager.get_service_status(service.id)
            process_info = status_info.get('process') if status_info else None
            
            health = {
                "id": service.id,
                "name": service.name,
                "status": service.status.value,
                "auto_restart": service.auto_restart,
                "restart_count": service.restart_count,
                "healthy": service.status == ServiceStatus.RUNNING and process_info is not None,
            }
            
            if process_info:
                health.update({
                    "cpu_percent": process_info.get("cpu_percent", 0),
                    "memory_mb": process_info.get("memory", {}).get("rss", 0) / 1024 / 1024,
                })
            
            health_info.append(health)
        
        return health_info