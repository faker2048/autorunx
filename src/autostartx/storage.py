"""Service data storage management."""

import json
import os
import uuid
from typing import Dict, List, Optional

from .config import ConfigManager
from .models import ServiceInfo, ServiceStatus


class ServiceStorage:
    """Service data storage manager."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.db_path = config_manager.get_services_db_path()
        self._services: Dict[str, ServiceInfo] = {}
        self.load_services()

    def load_services(self) -> None:
        """Load service data from file."""
        if not os.path.exists(self.db_path):
            self._services = {}
            return

        try:
            with open(self.db_path, encoding="utf-8") as f:
                data = json.load(f)

            self._services = {}
            for service_id, service_data in data.items():
                try:
                    service = ServiceInfo.from_dict(service_data)
                    self._services[service_id] = service
                except Exception as e:
                    print(f"Warning: Failed to load service {service_id}: {e}")

        except Exception as e:
            print(f"Warning: Failed to load service data: {e}")
            self._services = {}

    def save_services(self) -> None:
        """Save service data to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            data = {}
            for service_id, service in self._services.items():
                data[service_id] = service.to_dict()

            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error: Failed to save service data: {e}")

    def add_service(
        self,
        name: str,
        command: str,
        auto_restart: bool = True,
        working_dir: str = "",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> ServiceInfo:
        """Add new service."""
        service_id = self._generate_service_id()

        # Check name conflict
        if self.get_service_by_name(name):
            raise ValueError(f"Service name '{name}' already exists")

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
        """Get service by ID."""
        return self._services.get(service_id)

    def get_service_by_name(self, name: str) -> Optional[ServiceInfo]:
        """Get service by name."""
        for service in self._services.values():
            if service.name == name:
                return service
        return None

    def get_all_services(self) -> List[ServiceInfo]:
        """Get all services."""
        return list(self._services.values())

    def update_service(self, service: ServiceInfo) -> None:
        """Update service information."""
        if service.id in self._services:
            self._services[service.id] = service
            self.save_services()
        else:
            raise ValueError(f"Service {service.id} does not exist")

    def remove_service(self, service_id: str) -> bool:
        """Remove service."""
        if service_id in self._services:
            del self._services[service_id]
            self.save_services()
            return True
        return False

    def find_service(self, service_id_or_name: str) -> Optional[ServiceInfo]:
        """Find service by ID or name."""
        # First try to find by ID
        service = self.get_service(service_id_or_name)
        if service:
            return service

        # Then try to find by name
        return self.get_service_by_name(service_id_or_name)

    def get_services_by_status(self, status: ServiceStatus) -> List[ServiceInfo]:
        """Get service list by status."""
        return [
            service for service in self._services.values() if service.status == status
        ]

    def _generate_service_id(self) -> str:
        """Generate unique service ID."""
        while True:
            service_id = str(uuid.uuid4())[:8]
            if service_id not in self._services:
                return service_id
