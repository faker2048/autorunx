# AutoRunX - Turn Any Command into a Service

Transform any command-line program into an auto-restarting background service with a single command. Designed for developers who need simple, intuitive process management and monitoring. Zero configuration required.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org) [![UV](https://img.shields.io/badge/built_with-uv-green.svg)](https://github.com/astral-sh/uv) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[中文文档](README_zh.md) | [English](README.md)

## Quick Start

### Installation

```bash
# Run directly with uvx from GitHub (recommended)
uvx --from git+https://github.com/faker2048/autorunx autorunx add "python -m http.server 8000" --name my-web

# Or install from GitHub with pip
pip install git+https://github.com/faker2048/autorunx.git

# Or clone and install locally
git clone https://github.com/faker2048/autorunx.git
cd autorunx
pip install -e .
```

> **Note**: AutoRunX is not yet published to PyPI. Use the GitHub installation methods above.
> 
> 📋 **For detailed installation instructions and troubleshooting, see [INSTALL.md](INSTALL.md)**

### Basic Usage

```bash
# Add a service
autorunx add "python -m http.server 8000" --name web-server

# List services
autorunx list

# View logs
autorunx logs --name web-server --follow

# Control services
autorunx start --name web-server
autorunx stop --name web-server
autorunx restart --name web-server
```

### Common Use Cases

```bash
# Web applications
autorunx add "uvicorn main:app --host 0.0.0.0 --port 8000" --name api-server

# Proxy services
autorunx add "sing-box run -c config.json" --name proxy

# Background scripts
autorunx add "python process_data.py" --name data-processor

# One-time tasks (disable auto-restart)
autorunx add "backup.sh" --name backup --no-auto-restart
```

## Features

- **Auto-restart** - Automatically restart crashed processes
- **Process monitoring** - Real-time CPU and memory usage tracking
- **Log management** - Automatic log collection with rotation
- **Interactive control** - User-friendly command-line interface
- **Zero configuration** - Works out of the box
- **Cross-platform** - Windows, Linux, and macOS support

## Commands

| Command | Description |
|---------|-------------|
| `add` | Add a new service |
| `list` | Show all services |
| `start/stop/restart` | Control service lifecycle |
| `pause/resume` | Pause/resume services |
| `status` | Show detailed service information |
| `logs` | View and follow service logs |
| `remove` | Delete services |
| `daemon` | Manage background monitoring |

## Comparison

| Feature | AutoRunX | systemd | PM2 | supervisor |
|---------|----------|---------|-----|------------|
| **Learning curve** | Low | High | Medium | High |
| **Platform support** | Cross-platform | Linux only | Cross-platform | Cross-platform |
| **Configuration** | Zero config | Config files | Medium config | Complex config |
| **Target users** | Developers | System admins | Node.js devs | DevOps engineers |

## Background Monitoring

AutoRunX can run as a daemon to automatically monitor and restart your services:

```bash
# Start background monitoring
autorunx daemon --action start

# Check daemon status
autorunx daemon --action status

# Stop daemon
autorunx daemon --action stop
```

## Configuration

Default config location: `~/.config/autorunx/config.toml`

```toml
[general]
log_level = "INFO"
max_log_size = "10MB"
log_retention_days = 7

[services]
auto_restart = true
restart_delay = 5
max_restart_attempts = 3

[ui]
interactive_mode = true
color_output = true
```

## Development

```bash
# Install dependencies
make install-local

# Run tests
make test

# Run demo
make demo

# Development mode
make dev
```

## API Usage

You can also use AutoRunX programmatically:

```python
from autorunx.service_manager import ServiceManager

# Create manager
manager = ServiceManager()

# Add service
service = manager.add_service(
    name="my-app",
    command="python app.py",
    auto_restart=True
)

# Start service
manager.start_service(service.id)

# Get status
status = manager.get_service_status(service.id)
```

## Why AutoRunX?

Sometimes you just want to run a simple command as a service without learning systemd unit files, PM2 configurations, or supervisor settings. AutoRunX fills that gap with:

- **Simplicity** - One command to turn anything into a service
- **Reliability** - Automatic restarts and monitoring
- **Visibility** - Easy status checking and log viewing
- **Portability** - Works the same across all platforms

Perfect for development servers, background tasks, proxy services, and any command that should keep running.

## Contributing

We welcome contributions! Please:

- Submit issues for bugs or feature requests
- Send pull requests to improve the code
- Star the project to show your support

## License

MIT License - see [LICENSE](LICENSE) file for details.