"""进程管理模块."""

import os
import signal
import subprocess
import time
import psutil
from typing import Optional, Dict, Any, List
from .models import ServiceInfo, ServiceStatus
from .config import ConfigManager


class ProcessInfo:
    """进程信息类."""
    
    def __init__(self, pid: int):
        self.pid = pid
        self._process = psutil.Process(pid) if psutil.pid_exists(pid) else None
    
    @property
    def exists(self) -> bool:
        """进程是否存在."""
        return self._process is not None and self._process.is_running()
    
    @property
    def status(self) -> str:
        """进程状态."""
        if not self.exists:
            return "not_found"
        try:
            return self._process.status()
        except psutil.NoSuchProcess:
            return "not_found"
    
    @property
    def memory_info(self) -> Dict[str, int]:
        """内存使用信息."""
        if not self.exists:
            return {"rss": 0, "vms": 0}
        try:
            mem = self._process.memory_info()
            return {"rss": mem.rss, "vms": mem.vms}
        except psutil.NoSuchProcess:
            return {"rss": 0, "vms": 0}
    
    @property
    def cpu_percent(self) -> float:
        """CPU使用率."""
        if not self.exists:
            return 0.0
        try:
            return self._process.cpu_percent()
        except psutil.NoSuchProcess:
            return 0.0
    
    @property
    def create_time(self) -> float:
        """进程创建时间."""
        if not self.exists:
            return 0.0
        try:
            return self._process.create_time()
        except psutil.NoSuchProcess:
            return 0.0
    
    def terminate(self) -> bool:
        """优雅终止进程."""
        if not self.exists:
            return True
        
        try:
            self._process.terminate()
            # 等待进程结束
            self._process.wait(timeout=10)
            return True
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            return self.kill()
    
    def kill(self) -> bool:
        """强制杀死进程."""
        if not self.exists:
            return True
            
        try:
            self._process.kill()
            self._process.wait(timeout=5)
            return True
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            # 进程可能已经结束或者无法杀死
            return not self.exists


class ProcessManager:
    """进程管理器."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def start_service(self, service: ServiceInfo) -> bool:
        """启动服务."""
        if service.pid and self.is_process_running(service.pid):
            return False  # 进程已在运行
        
        try:
            # 获取日志文件路径
            log_path = self.config_manager.get_service_log_path(service.id)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            # 启动进程
            with open(log_path, "a", encoding="utf-8") as log_file:
                # 写入启动日志
                log_file.write(f"\n=== 服务启动: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                log_file.flush()
                
                # 解析命令
                cmd_parts = self._parse_command(service.command)
                
                # 设置环境变量
                env = os.environ.copy()
                env.update(service.env_vars)
                
                # 启动进程
                process = subprocess.Popen(
                    cmd_parts,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=service.working_dir or os.getcwd(),
                    env=env,
                    start_new_session=True,  # 创建新的进程组
                )
                
                service.pid = process.pid
                service.update_status(ServiceStatus.RUNNING)
                return True
                
        except Exception as e:
            print(f"启动服务失败: {e}")
            service.update_status(ServiceStatus.FAILED)
            return False
    
    def stop_service(self, service: ServiceInfo, force: bool = False) -> bool:
        """停止服务."""
        if not service.pid:
            service.update_status(ServiceStatus.STOPPED)
            return True
        
        process_info = ProcessInfo(service.pid)
        if not process_info.exists:
            service.pid = None
            service.update_status(ServiceStatus.STOPPED)
            return True
        
        # 停止进程
        success = process_info.kill() if force else process_info.terminate()
        
        if success:
            service.pid = None
            service.update_status(ServiceStatus.STOPPED)
            
            # 写入停止日志
            log_path = self.config_manager.get_service_log_path(service.id)
            try:
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"\n=== 服务停止: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            except Exception:
                pass  # 忽略日志写入错误
        
        return success
    
    def restart_service(self, service: ServiceInfo, force: bool = False) -> bool:
        """重启服务."""
        # 先停止
        if not self.stop_service(service, force):
            return False
        
        # 等待一下
        time.sleep(1)
        
        # 再启动
        return self.start_service(service)
    
    def pause_service(self, service: ServiceInfo) -> bool:
        """暂停服务."""
        if not service.pid:
            return False
        
        process_info = ProcessInfo(service.pid)
        if not process_info.exists:
            service.pid = None
            service.update_status(ServiceStatus.STOPPED)
            return False
        
        try:
            os.kill(service.pid, signal.SIGSTOP)
            service.update_status(ServiceStatus.PAUSED)
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def resume_service(self, service: ServiceInfo) -> bool:
        """恢复服务."""
        if not service.pid:
            return False
        
        process_info = ProcessInfo(service.pid)
        if not process_info.exists:
            service.pid = None
            service.update_status(ServiceStatus.STOPPED)
            return False
        
        try:
            os.kill(service.pid, signal.SIGCONT)
            service.update_status(ServiceStatus.RUNNING)
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def get_process_info(self, service: ServiceInfo) -> Optional[Dict[str, Any]]:
        """获取进程信息."""
        if not service.pid:
            return None
        
        process_info = ProcessInfo(service.pid)
        if not process_info.exists:
            return None
        
        return {
            "pid": service.pid,
            "status": process_info.status,
            "cpu_percent": process_info.cpu_percent,
            "memory": process_info.memory_info,
            "create_time": process_info.create_time,
        }
    
    def is_process_running(self, pid: int) -> bool:
        """检查进程是否在运行."""
        return ProcessInfo(pid).exists
    
    def _parse_command(self, command: str) -> List[str]:
        """解析命令字符串."""
        # 简单的命令解析，支持引号
        import shlex
        return shlex.split(command)