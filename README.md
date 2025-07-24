# AutoRunX - Turn Any Command into a Service

Transform any command-line program into an auto-restarting background service with a single command. Simple, fast, zero configuration.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[中文文档](README_zh.md) | [English](README.md)

## Installation & Quick Start

```bash
# Install from GitHub
git clone https://github.com/faker2048/autorunx.git
cd autorunx
pip install -e .

# Add a service
autorunx add "python -m http.server 8000" --name web

# Check status
autorunx list

# View logs
autorunx logs web -f
```

## Commands

```bash
autorunx add "command"           # Add service
autorunx list                   # Show services
autorunx start/stop/restart     # Control services  
autorunx logs <name> -f         # View logs
autorunx daemon --action start  # Auto-restart daemon
```

## Why AutoRunX?

- **Simple**: One command to turn anything into a service
- **Reliable**: Automatic restarts when processes crash
- **Cross-platform**: Works on Windows, Linux, macOS
- **Zero config**: No setup files needed

Perfect for development servers, background tasks, proxy services.

## License

MIT License