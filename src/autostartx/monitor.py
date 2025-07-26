"""Process monitoring and auto-restart service."""

import threading
import time
from typing import Dict, List

from .models import ServiceStatus
from .service_manager import ServiceManager


class ServiceMonitor:
    """Service monitor."""

    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self._monitoring = False
        self._monitor_thread = None
        self._check_interval = 5  # Check interval (seconds)

    def start_monitoring(self) -> None:
        """Start monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("🔍 Service monitoring started")

    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10)
        print("⏹️ Service monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._check_services()
                time.sleep(self._check_interval)
            except Exception as e:
                print(f"Error occurred while monitoring services: {e}")
                time.sleep(self._check_interval)

    def _check_services(self) -> None:
        """Check all service statuses."""
        services = self.service_manager.list_services()

        for service in services:
            # Only monitor services that should be running and have auto-restart enabled
            if not service.auto_restart:
                continue

            # Check process status
            if service.status == ServiceStatus.RUNNING and service.pid:
                if not self.service_manager.process_manager.is_process_running(service.pid):
                    # Process unexpectedly exited, needs restart
                    self._handle_service_crash(service)

            elif service.status == ServiceStatus.STARTING:
                # Check if startup timed out
                if time.time() - service.updated_at > 30:  # 30 second startup timeout
                    service.update_status(ServiceStatus.FAILED)
                    self.service_manager.storage.update_service(service)
                    print(f"⚠️ Service {service.name} startup timeout")

    def _handle_service_crash(self, service) -> None:
        """Handle service crash."""
        print(f"⚠️ Detected unexpected exit of service {service.name}")

        # Update status
        service.pid = None
        service.update_status(ServiceStatus.STOPPED)

        # Check restart attempt limit
        if service.restart_count >= service.max_restart_attempts:
            print(
                f"❌ Service {service.name} reached maximum restart attempts "
                f"({service.max_restart_attempts})"
            )
            service.update_status(ServiceStatus.FAILED)
            self.service_manager.storage.update_service(service)
            return

        # Wait for restart delay
        if service.restart_delay > 0:
            print(
                f"⏳ Waiting {service.restart_delay} seconds before restarting "
                f"service {service.name}"
            )
            time.sleep(service.restart_delay)

        # Attempt restart
        print(f"🔄 Restarting service {service.name} (attempt {service.restart_count + 1})")

        service.update_status(ServiceStatus.STARTING)
        self.service_manager.storage.update_service(service)

        if self.service_manager.process_manager.start_service(service):
            service.increment_restart_count()
            print(f"✅ Service {service.name} restarted successfully")
        else:
            service.update_status(ServiceStatus.FAILED)
            print(f"❌ Service {service.name} restart failed")

        self.service_manager.storage.update_service(service)


class AutoRestartManager:
    """Auto-restart manager - standalone monitoring service."""

    def __init__(self, config_path: str = None):
        self.service_manager = ServiceManager(config_path)
        self.monitor = ServiceMonitor(self.service_manager)
        self._running = False

    def start(self) -> None:
        """Start auto-restart manager."""
        if self._running:
            return

        print("🚀 Autostartx auto-restart manager started")
        
        # Auto-recovery: restart services that should be running
        self._auto_recover_services()
        
        self._running = True

        try:
            # Start monitoring
            self.monitor.start_monitoring()

            # Main loop
            while self._running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nReceived interrupt signal, shutting down...")
        finally:
            self.stop()

    def _auto_recover_services(self) -> None:
        """Auto-recover services that should be running after system restart."""
        print("🔄 Checking for services to auto-recover...")
        
        try:
            services = self.service_manager.list_services()
            recovery_candidates = []
            
            for service in services:
                # Find services that should be auto-recovered:
                # 1. Have auto_restart enabled
                # 2. Status is RUNNING but process doesn't exist (system restart scenario)
                if (service.auto_restart and 
                    service.status == ServiceStatus.RUNNING and 
                    service.pid and 
                    not self.service_manager.process_manager.is_process_running(service.pid)):
                    recovery_candidates.append(service)
            
            if not recovery_candidates:
                print("✅ No services need recovery")
                return
            
            print(f"🔧 Found {len(recovery_candidates)} service(s) to recover:")
            for service in recovery_candidates:
                print(f"   - {service.name}")
            
            # Recover services
            recovered_count = 0
            failed_count = 0
            
            for service in recovery_candidates:
                print(f"🔄 Recovering service: {service.name}")
                
                # Reset service state
                service.pid = None
                service.update_status(ServiceStatus.STOPPED)
                self.service_manager.storage.update_service(service)
                
                # Attempt to start the service
                if self.service_manager.start_service(service.id):
                    print(f"✅ Successfully recovered: {service.name}")
                    recovered_count += 1
                else:
                    print(f"❌ Failed to recover: {service.name}")
                    failed_count += 1
                    
                # Small delay between recoveries
                time.sleep(1)
            
            print(f"🎯 Recovery complete: {recovered_count} succeeded, {failed_count} failed")
            
        except Exception as e:
            print(f"⚠️ Error during auto-recovery: {e}")
            # Continue with normal monitoring even if recovery fails

    def stop(self) -> None:
        """Stop auto-restart manager."""
        if not self._running:
            return

        print("🛑 Stopping auto-restart manager...")
        self._running = False
        self.monitor.stop_monitoring()
        print("✅ Auto-restart manager stopped")

    def status(self) -> Dict[str, any]:
        """Get monitoring status."""
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
        """Get service health status."""
        services = self.service_manager.list_services()
        health_info = []

        for service in services:
            status_info = self.service_manager.get_service_status(service.id)
            process_info = status_info.get("process") if status_info else None

            health = {
                "id": service.id,
                "name": service.name,
                "status": service.status.value,
                "auto_restart": service.auto_restart,
                "restart_count": service.restart_count,
                "healthy": service.status == ServiceStatus.RUNNING and process_info is not None,
            }

            if process_info:
                health.update(
                    {
                        "cpu_percent": process_info.get("cpu_percent", 0),
                        "memory_mb": process_info.get("memory", {}).get("rss", 0) / 1024 / 1024,
                    }
                )

            health_info.append(health)

        return health_info
