"""Logging management system."""

import gzip
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ConfigManager


class LogManager:
    """Log manager."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup application logging."""
        # Create log directory
        log_dir = Path(self.config_manager.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure main log
        log_file = log_dir / "autostartx.log"

        # Set log format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, self.config_manager.config.log_level))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(
            logging.WARNING
        )  # Only show warnings and errors on console

        # Configure root logger
        root_logger = logging.getLogger("autostartx")
        root_logger.setLevel(getattr(logging, self.config_manager.config.log_level))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Avoid duplicate handlers
        root_logger.propagate = False

    def get_service_log_path(self, service_id: str) -> str:
        """Get service log path."""
        return self.config_manager.get_service_log_path(service_id)

    def read_service_logs(
        self, service_id: str, lines: int = 100, since: Optional[float] = None
    ) -> List[str]:
        """Read service logs."""
        log_path = self.get_service_log_path(service_id)

        if not os.path.exists(log_path):
            return []

        try:
            with open(log_path, encoding="utf-8") as f:
                all_lines = f.readlines()

            # If time filter is specified
            if since:
                filtered_lines = []
                for line in all_lines:
                    # Try to parse timestamp (simplified version)
                    if self._line_is_after_time(line, since):
                        filtered_lines.append(line)
                all_lines = filtered_lines

            # Return last N lines
            return all_lines[-lines:] if lines > 0 else all_lines

        except Exception as e:
            logging.getLogger("autostartx").error(f"Failed to read service logs: {e}")
            return []

    def clear_service_logs(self, service_id: str) -> bool:
        """Clear service logs."""
        log_path = self.get_service_log_path(service_id)

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
            logging.getLogger("autostartx").info(
                f"Cleared logs for service {service_id}"
            )
            return True
        except Exception as e:
            logging.getLogger("autostartx").error(f"Failed to clear service logs: {e}")
            return False

    def rotate_service_logs(self, service_id: str) -> bool:
        """Rotate service logs."""
        log_path = self.get_service_log_path(service_id)

        if not os.path.exists(log_path):
            return True

        try:
            # Check file size
            file_size = os.path.getsize(log_path)
            max_size = self._parse_size(self.config_manager.config.max_log_size)

            if file_size < max_size:
                return True

            # Perform rotation
            timestamp = int(time.time())
            rotated_path = f"{log_path}.{timestamp}"

            # Rename current log file
            os.rename(log_path, rotated_path)

            # Compress old log
            self._compress_log_file(rotated_path)

            # Create new empty log file
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"=== Log rotation: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

            logging.getLogger("autostartx").info(
                f"Rotated logs for service {service_id}"
            )
            return True

        except Exception as e:
            logging.getLogger("autostartx").error(f"Failed to rotate logs: {e}")
            return False

    def cleanup_old_logs(self) -> None:
        """Clean up expired logs."""
        log_dir = Path(self.config_manager.config.log_dir)
        if not log_dir.exists():
            return

        retention_days = self.config_manager.config.log_retention_days
        cutoff_time = time.time() - (retention_days * 24 * 3600)

        try:
            for log_file in log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logging.getLogger("autostartx").info(
                        f"Deleted expired log: {log_file}"
                    )

            # Clean up compressed logs
            for gz_file in log_dir.glob("*.gz"):
                if gz_file.stat().st_mtime < cutoff_time:
                    gz_file.unlink()
                    logging.getLogger("autostartx").info(
                        f"Deleted expired compressed log: {gz_file}"
                    )

        except Exception as e:
            logging.getLogger("autostartx").error(
                f"Failed to clean up expired logs: {e}"
            )

    def get_log_stats(self, service_id: str) -> Dict[str, Any]:
        """Get log statistics."""
        log_path = self.get_service_log_path(service_id)

        if not os.path.exists(log_path):
            return {
                "exists": False,
                "size": 0,
                "lines": 0,
                "last_modified": None,
            }

        try:
            stat = os.stat(log_path)

            # Count lines
            with open(log_path, encoding="utf-8") as f:
                lines = sum(1 for _ in f)

            return {
                "exists": True,
                "size": stat.st_size,
                "size_mb": stat.st_size / 1024 / 1024,
                "lines": lines,
                "last_modified": stat.st_mtime,
                "last_modified_str": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)
                ),
            }

        except Exception as e:
            logging.getLogger("autostartx").error(f"Failed to get log statistics: {e}")
            return {"exists": False, "error": str(e)}

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        size_str = size_str.upper()

        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Assume bytes
            return int(size_str)

    def _compress_log_file(self, file_path: str) -> None:
        """Compress log file."""
        try:
            compressed_path = f"{file_path}.gz"

            with open(file_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    f_out.writelines(f_in)

            # Delete original file
            os.remove(file_path)

        except Exception as e:
            logging.getLogger("autostartx").error(f"Failed to compress log file: {e}")

    def _line_is_after_time(self, line: str, since_time: float) -> bool:
        """Check if log line is after specified time."""
        # This is a simplified version, should parse log timestamps in reality
        # Here assumes log lines don't contain timestamps, or use file modification time
        return True


class ServiceLogRotator:
    """Service log rotator."""

    def __init__(self, log_manager: LogManager):
        self.log_manager = log_manager

    def rotate_if_needed(self, service_id: str) -> bool:
        """Rotate logs if needed."""
        stats = self.log_manager.get_log_stats(service_id)

        if not stats.get("exists"):
            return True

        max_size = self.log_manager._parse_size(
            self.log_manager.config_manager.config.max_log_size
        )

        if stats["size"] >= max_size:
            return self.log_manager.rotate_service_logs(service_id)

        return True

    def rotate_all_services(self, service_ids: List[str]) -> Dict[str, bool]:
        """Rotate logs for all services."""
        results = {}

        for service_id in service_ids:
            results[service_id] = self.rotate_if_needed(service_id)

        return results
