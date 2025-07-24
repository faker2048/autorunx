# AutoRunX Usage Guide

[English](USAGE.md) | [中文](USAGE_zh.md)

## Quick Start

### Installation

#### From GitHub (Current Method)

Since AutoRunX is not yet published to PyPI, install it directly from GitHub:

```bash
# Method 1: Run directly with uvx (recommended)
uvx --from git+https://github.com/faker2048/autorunx autorunx --help

# Method 2: Install with pip
pip install git+https://github.com/faker2048/autorunx.git

# Method 3: Clone and install locally
git clone https://github.com/faker2048/autorunx.git
cd autorunx
pip install -e .
```

#### Development Installation

For development or testing:

```bash
git clone https://github.com/faker2048/autorunx.git
cd autorunx
make install-local  # Installs dependencies
make dev            # Run in development mode
```

#### Future PyPI Installation

Once published to PyPI, you'll be able to install with:

```bash
# This will work after PyPI publication
pip install autorunx
uvx autorunx
```

### Basic Operations

```bash
# Add a service
autorunx add "python -m http.server 8000" --name web-server

# List services
autorunx list

# Start service
autorunx start --name web-server

# Check service status
autorunx status --name web-server

# View real-time logs
autorunx logs --name web-server --follow

# Stop service
autorunx stop --name web-server

# Remove service
autorunx remove --name web-server
```

## Detailed Features

### Service Management

#### Adding Services
```bash
# Basic add
autorunx add "command to run" --name service-name

# Advanced options
autorunx add "uvicorn main:app" \
  --name api-server \
  --working-dir /path/to/project

# Disable auto-restart (for one-time tasks)
autorunx add "backup.sh" --name backup --no-auto-restart
```

#### Service Control
```bash
# Start/stop/restart
autorunx start --name service-name
autorunx stop --name service-name
autorunx restart --name service-name

# Pause/resume (sends SIGSTOP/SIGCONT signals)
autorunx pause --name service-name
autorunx resume --name service-name

# Force operations
autorunx stop --name service-name --force
autorunx restart --name service-name --force
```

#### Status Checking
```bash
# Simple list
autorunx list

# Detailed status
autorunx list --status

# Individual service details
autorunx status --name service-name
```

### Log Management

```bash
# View last 100 lines
autorunx logs --name service-name

# View last 50 lines
autorunx logs --name service-name --tail 50

# Follow logs in real-time
autorunx logs --name service-name --follow

# Clear logs
autorunx logs --name service-name --clear
```

### Background Monitoring

```bash
# Start daemon (background monitoring with auto-restart)
autorunx daemon --action start

# Check daemon status
autorunx daemon --action status

# Stop daemon
autorunx daemon --action stop

# Foreground monitoring mode (for debugging)
autorunx monitor
```

## Interactive Mode

When commands lack required parameters, the tool enters interactive mode:

```bash
# Without specifying service, shows service list for selection
autorunx start
autorunx logs
autorunx remove
```

## Configuration File

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

You can specify a custom config file with the `--config` parameter.

## Use Cases

### Web Services

```bash
# Flask application
autorunx add "flask run --host 0.0.0.0 --port 5000" --name flask-app

# FastAPI application
autorunx add "uvicorn main:app --host 0.0.0.0 --port 8000" --name fastapi-app

# Static file server
autorunx add "python -m http.server 8080" --name static-server
```

### Proxy Services

```bash
# sing-box
autorunx add "sing-box run -c config.json" --name proxy

# v2ray
autorunx add "v2ray run -c config.json" --name v2ray
```

### Background Tasks

```bash
# Data processing script
autorunx add "python process_data.py" --name data-processor

# Scheduled tasks
autorunx add "python cron_job.py" --name scheduler

# Monitoring script
autorunx add "python monitor.py" --name monitor
```

### Development Tools

```bash
# File watching
autorunx add "watchmedo auto-restart --patterns '*.py' python main.py" --name dev-server

# Frontend development server
autorunx add "npm run dev" --name frontend-dev

# Database
autorunx add "redis-server" --name redis
```

## Best Practices

### 1. Service Naming
- Use meaningful names like `web-api`, `background-worker`
- Avoid special characters, use hyphens to separate words

### 2. Working Directory
- Specify `--working-dir` for services that need specific working directories
- Ensure relative paths are correct

### 3. Log Management
- Regularly check and clean logs
- Enable real-time log monitoring for important services
- Adjust log retention days and size limits

### 4. Monitoring and Maintenance
- Enable daemon for automatic monitoring
- Set appropriate restart attempt limits
- Regularly check service status

### 5. Security Considerations
- Don't include sensitive information in commands
- Use environment variables for configuration
- Limit service execution permissions

## Troubleshooting

### Service Fails to Start
1. Check if the command is correct
2. Verify working directory and permissions
3. Check service logs for error information

### Auto-restart Not Working
1. Confirm `auto_restart` is enabled
2. Check if maximum restart attempts reached
3. Verify daemon is running

### Log Files Too Large
1. Adjust `max_log_size` configuration
2. Use `logs --clear` to clear logs
3. Reduce log retention days

### Performance Issues
1. Monitor process resource usage
2. Adjust restart delay time
3. Check system resource limits

## API Usage

You can use AutoRunX directly in Python code:

```python
from autorunx.service_manager import ServiceManager

# Create manager
manager = ServiceManager()

# Add service
service = manager.add_service(
    name="my-service",
    command="python app.py",
    auto_restart=True
)

# Start service
if manager.start_service(service.id):
    print("Service started successfully")

# Get service status
status = manager.get_service_status(service.id)
print(f"Service status: {status['service'].status.value}")
```

For more examples, check the `examples/` directory.

## Advanced Configuration

### Custom Configuration File

```bash
# Use custom config
autorunx --config /path/to/custom.toml add "command" --name service
```

### Environment Variables

```bash
# Set environment variables for the service
export MY_VAR="value"
autorunx add "python app.py" --name my-app
```

### Service Dependencies

While AutoRunX doesn't have built-in dependency management, you can create wrapper scripts:

```bash
# dependency_wrapper.sh
#!/bin/bash
wait-for-it database:5432 -- python app.py

autorunx add "./dependency_wrapper.sh" --name web-app
```

## Integration Examples

### Docker Integration

```bash
# Run as init process in container
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install autorunx
CMD ["autorunx", "add", "python", "app.py", "--name", "main", "&&", "autorunx", "daemon", "--action", "start"]
```

### Systemd Integration

```ini
# /etc/systemd/system/autorunx.service
[Unit]
Description=AutoRunX Service Manager
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/autorunx daemon --action start
ExecStop=/usr/local/bin/autorunx daemon --action stop
Restart=always
User=autorunx

[Install]
WantedBy=multi-user.target
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Deploy with AutoRunX
  run: |
    uvx autorunx add "python app.py" --name production-app
    uvx autorunx daemon --action start
```

This comprehensive guide covers all aspects of using AutoRunX effectively. For specific questions or issues, please check the project's GitHub repository.