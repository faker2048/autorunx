# Autostartx - Turn Any Command into a Service

Transform any command-line program into an auto-restarting background service with a single command. Simple, fast, zero configuration.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[中文文档](README_zh.md) | [English](README.md)

## Installation & Quick Start

```bash
# Install from GitHub
git clone https://github.com/faker2048/autostartx.git
cd autostartx
pip install -e .

# Or install directly with uvx
uvx --from git+https://github.com/faker2048/autostartx.git autostartx add "python -m http.server 8000" --name web

# Add a service
autostartx add "python -m http.server 8000" --name web

# Check status
autostartx list

# View logs
autostartx logs web -f
```

## Commands

```bash
autostartx add "command"           # Add service
autostartx list                   # Show services
autostartx start/stop/restart     # Control services  
autostartx logs <name> -f         # View logs
autostartx daemon --action start  # Auto-restart daemon
```

## Why Autostartx?

- **Simple**: One command to turn anything into a service
- **Reliable**: Automatic restarts when processes crash
- **Cross-platform**: Works on Windows, Linux, macOS
- **Zero config**: No setup files needed

Perfect for development servers, background tasks, proxy services.

## License

MIT License