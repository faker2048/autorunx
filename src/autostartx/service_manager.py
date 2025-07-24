"""Service manager - core class integrating all functionality."""

import time
from typing import Any, Dict, List, Optional

from .config import ConfigManager
from .models import ServiceInfo, ServiceStatus
from .process_manager import ProcessManager
from .storage import ServiceStorage


class ServiceManager:
    """Service manager."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.storage = ServiceStorage(self.config_manager)
        self.process_manager = ProcessManager(self.config_manager)

    def add_service(
        self,
        name: str,
        command: str,
        auto_restart: bool = True,
        working_dir: str = "",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> ServiceInfo:
        """Add new service."""
        service = self.storage.add_service(
            name=name,
            command=command,
            auto_restart=auto_restart,
            working_dir=working_dir,
            env_vars=env_vars,
        )
        return service

    def start_service(self, service_id_or_name: str) -> bool:
        """Start service."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False

        success = self.process_manager.start_service(service)
        if success:
            self.storage.update_service(service)
        return success

    def stop_service(self, service_id_or_name: str, force: bool = False) -> bool:
        """Stop service."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False

        success = self.process_manager.stop_service(service, force)
        if success:
            self.storage.update_service(service)
        return success

    def restart_service(self, service_id_or_name: str, force: bool = False) -> bool:
        """Restart service."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False

        success = self.process_manager.restart_service(service, force)
        if success:
            service.increment_restart_count()
            self.storage.update_service(service)
        return success

    def pause_service(self, service_id_or_name: str) -> bool:
        """Pause service."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False

        success = self.process_manager.pause_service(service)
        if success:
            self.storage.update_service(service)
        return success

    def resume_service(self, service_id_or_name: str) -> bool:
        """Resume service."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False

        success = self.process_manager.resume_service(service)
        if success:
            self.storage.update_service(service)
        return success

    def remove_service(self, service_id_or_name: str, force: bool = False) -> bool:
        """Remove service."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return False

        # If service is running, stop it first
        if service.status == ServiceStatus.RUNNING:
            if not force:
                return False  # Need force delete to remove running service
            self.stop_service(service.id, force=True)

        return self.storage.remove_service(service.id)

    def get_service(self, service_id_or_name: str) -> Optional[ServiceInfo]:
        """Get service information."""
        return self.storage.find_service(service_id_or_name)

    def list_services(self) -> List[ServiceInfo]:
        """Get all services list."""
        services = self.storage.get_all_services()

        # Update service status
        for service in services:
            self._update_service_status(service)

        return services

    def get_service_status(self, service_id_or_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed service status."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return None

        # Update status
        self._update_service_status(service)

        # Get process information
        process_info = self.process_manager.get_process_info(service)

        status_info = {
            "service": service,
            "process": process_info,
            "uptime": self._calculate_uptime(service, process_info),
        }

        return status_info

    def get_service_logs(
        self, service_id_or_name: str, lines: int = 100
    ) -> Optional[List[str]]:
        """Get service logs."""
        service = self.storage.find_service(service_id_or_name)
        if not service:
            return None

        log_path = self.config_manager.get_service_log_path(service.id)

        try:
            with open(log_path, encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if lines > 0 else all_lines
        except FileNotFoundError:
            return []
        except Exception:
            return None

    def clear_service_logs(self, service_id_or_name: str) -> bool:
        """Clear service logs."""
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
        """Update service status."""
        if service.pid:
            if self.process_manager.is_process_running(service.pid):
                # Process exists and status is not running, update status
                if (
                    service.status != ServiceStatus.RUNNING
                    and service.status != ServiceStatus.PAUSED
                ):
                    service.update_status(ServiceStatus.RUNNING)
                    self.storage.update_service(service)
            else:
                # Process doesn't exist, update status
                service.pid = None
                service.update_status(ServiceStatus.STOPPED)
                self.storage.update_service(service)
        else:
            # No PID and status is not stopped, update status
            if service.status != ServiceStatus.STOPPED:
                service.update_status(ServiceStatus.STOPPED)
                self.storage.update_service(service)

    def _calculate_uptime(
        self, service: ServiceInfo, process_info: Optional[Dict[str, Any]]
    ) -> Optional[float]:
        """Calculate service uptime."""
        if not process_info or not process_info.get("create_time"):
            return None

        return time.time() - process_info["create_time"]
