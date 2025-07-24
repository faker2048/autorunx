"""Process management module."""

import os
import signal
import subprocess
import time
from typing import Any, Dict, List, Optional

import psutil

from .config import ConfigManager
from .models import ServiceInfo, ServiceStatus


class ProcessInfo:
    """Process information class."""

    def __init__(self, pid: int):
        self.pid = pid
        self._process = psutil.Process(pid) if psutil.pid_exists(pid) else None

    @property
    def exists(self) -> bool:
        """Whether process exists."""
        return self._process is not None and self._process.is_running()

    @property
    def status(self) -> str:
        """Process status."""
        if not self.exists:
            return "not_found"
        try:
            return self._process.status()
        except psutil.NoSuchProcess:
            return "not_found"

    @property
    def memory_info(self) -> Dict[str, int]:
        """Memory usage information."""
        if not self.exists:
            return {"rss": 0, "vms": 0}
        try:
            mem = self._process.memory_info()
            return {"rss": mem.rss, "vms": mem.vms}
        except psutil.NoSuchProcess:
            return {"rss": 0, "vms": 0}

    @property
    def cpu_percent(self) -> float:
        """CPU usage rate."""
        if not self.exists:
            return 0.0
        try:
            return self._process.cpu_percent()
        except psutil.NoSuchProcess:
            return 0.0

    @property
    def create_time(self) -> float:
        """Process creation time."""
        if not self.exists:
            return 0.0
        try:
            return self._process.create_time()
        except psutil.NoSuchProcess:
            return 0.0

    def terminate(self) -> bool:
        """Gracefully terminate process."""
        if not self.exists:
            return True

        try:
            self._process.terminate()
            # Wait for process to end
            self._process.wait(timeout=10)
            return True
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            return self.kill()

    def kill(self) -> bool:
        """Force kill process."""
        if not self.exists:
            return True

        try:
            self._process.kill()
            self._process.wait(timeout=5)
            return True
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            # Process may have ended or cannot be killed
            return not self.exists


class ProcessManager:
    """Process manager."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def start_service(self, service: ServiceInfo) -> bool:
        """Start service."""
        if service.pid and self.is_process_running(service.pid):
            return False  # Process already running

        try:
            # Get log file path
            log_path = self.config_manager.get_service_log_path(service.id)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # Start process
            with open(log_path, "a", encoding="utf-8") as log_file:
                # Write startup log
                log_file.write(
                    f"\n=== Service started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                )
                log_file.flush()

                # Parse command
                cmd_parts = self._parse_command(service.command)

                # Set environment variables
                env = os.environ.copy()
                env.update(service.env_vars)

                # Start process
                process = subprocess.Popen(
                    cmd_parts,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=service.working_dir or os.getcwd(),
                    env=env,
                    start_new_session=True,  # Create new process group
                )

                service.pid = process.pid
                service.update_status(ServiceStatus.RUNNING)
                return True

        except Exception as e:
            print(f"Failed to start service: {e}")
            service.update_status(ServiceStatus.FAILED)
            return False

    def stop_service(self, service: ServiceInfo, force: bool = False) -> bool:
        """Stop service."""
        if not service.pid:
            service.update_status(ServiceStatus.STOPPED)
            return True

        process_info = ProcessInfo(service.pid)
        if not process_info.exists:
            service.pid = None
            service.update_status(ServiceStatus.STOPPED)
            return True

        # Stop process
        success = process_info.kill() if force else process_info.terminate()

        if success:
            service.pid = None
            service.update_status(ServiceStatus.STOPPED)

            # Write stop log
            log_path = self.config_manager.get_service_log_path(service.id)
            try:
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(
                        f"\n=== Service stopped: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                    )
            except Exception:
                pass  # Ignore log write errors

        return success

    def restart_service(self, service: ServiceInfo, force: bool = False) -> bool:
        """Restart service."""
        # First stop
        if not self.stop_service(service, force):
            return False

        # Wait a moment
        time.sleep(1)

        # Then start
        return self.start_service(service)

    def pause_service(self, service: ServiceInfo) -> bool:
        """Pause service."""
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
        """Resume service."""
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
        """Get process information."""
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
        """Check if process is running."""
        return ProcessInfo(pid).exists

    def _parse_command(self, command: str) -> List[str]:
        """Parse command string."""
        # Simple command parsing, supports quotes
        import shlex

        return shlex.split(command)
