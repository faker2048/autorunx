"""Configuration management module."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import toml


@dataclass
class Config:
    """Configuration class."""

    # General configuration
    log_level: str = "INFO"
    max_log_size: str = "10MB"
    log_retention_days: int = 7

    # Service configuration
    auto_restart: bool = True
    restart_delay: int = 5
    max_restart_attempts: int = 3

    # UI configuration
    interactive_mode: bool = True
    color_output: bool = True

    # Path configuration
    config_dir: str = field(default_factory=lambda: str(Path.home() / ".config" / "autostartx"))
    data_dir: str = field(
        default_factory=lambda: str(Path.home() / ".local" / "share" / "autostartx")
    )
    log_dir: str = field(
        default_factory=lambda: str(Path.home() / ".local" / "share" / "autostartx" / "logs")
    )


class ConfigManager:
    """Configuration manager."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = Config()
        self.config_path = config_path or os.path.join(self.config.config_dir, "config.toml")
        self._ensure_directories()
        self.load_config()

    def _ensure_directories(self) -> None:
        """Ensure necessary directories exist."""
        directories = [
            self.config.config_dir,
            self.config.data_dir,
            self.config.log_dir,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def load_config(self) -> None:
        """Load configuration from config file."""
        if not os.path.exists(self.config_path):
            self.save_config()  # Create default config file
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config_data = toml.load(f)

            # Update configuration
            if "general" in config_data:
                general = config_data["general"]
                self.config.log_level = general.get("log_level", self.config.log_level)
                self.config.max_log_size = general.get("max_log_size", self.config.max_log_size)
                self.config.log_retention_days = general.get(
                    "log_retention_days", self.config.log_retention_days
                )

            if "services" in config_data:
                services = config_data["services"]
                self.config.auto_restart = services.get("auto_restart", self.config.auto_restart)
                self.config.restart_delay = services.get("restart_delay", self.config.restart_delay)
                self.config.max_restart_attempts = services.get(
                    "max_restart_attempts", self.config.max_restart_attempts
                )

            if "ui" in config_data:
                ui = config_data["ui"]
                self.config.interactive_mode = ui.get(
                    "interactive_mode", self.config.interactive_mode
                )
                self.config.color_output = ui.get("color_output", self.config.color_output)

        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
            print("Using default configuration")

    def save_config(self) -> None:
        """Save configuration to file."""
        config_data = {
            "general": {
                "log_level": self.config.log_level,
                "max_log_size": self.config.max_log_size,
                "log_retention_days": self.config.log_retention_days,
            },
            "services": {
                "auto_restart": self.config.auto_restart,
                "restart_delay": self.config.restart_delay,
                "max_restart_attempts": self.config.max_restart_attempts,
            },
            "ui": {
                "interactive_mode": self.config.interactive_mode,
                "color_output": self.config.color_output,
            },
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)
        except Exception as e:
            print(f"Error: Failed to save config file: {e}")

    def get_services_db_path(self) -> str:
        """Get service database path."""
        return os.path.join(self.config.data_dir, "services.json")

    def get_service_log_path(self, service_id: str) -> str:
        """Get service log path."""
        return os.path.join(self.config.log_dir, f"{service_id}.log")
