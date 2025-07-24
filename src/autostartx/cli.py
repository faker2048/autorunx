"""Command Line Interface."""

import os
import sys
import time

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .daemon import AutostartxDaemon
from .interactive import confirm_action, select_service
from .models import ServiceStatus
from .monitor import AutoRestartManager
from .service_manager import ServiceManager

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.option("--config", help="Configuration file path")
@click.pass_context
def cli(ctx, config):
    """Autostartx - Command-line program service management tool."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@cli.command()
@click.argument("command")
@click.option("--name", help="Service name")
@click.option("--no-auto-restart", is_flag=True, help="Disable auto restart")
@click.option("--working-dir", help="Working directory")
@click.pass_context
def add(ctx, command, name, no_auto_restart, working_dir):
    """Add new service."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    # If no name specified, generate one
    if not name:
        name = f"service-{int(time.time())}"

    auto_restart = not no_auto_restart
    working_dir = working_dir or os.getcwd()

    try:
        service = manager.add_service(
            name=name,
            command=command,
            auto_restart=auto_restart,
            working_dir=working_dir,
        )

        console.print(f"✅ Service added: {service.name} ({service.id})")
        console.print(f"Command: {service.command}")
        console.print(
            f"Auto restart: {'Enabled' if service.auto_restart else 'Disabled'}"
        )

        # Ask if start immediately
        try:
            if click.confirm("Start service now?", default=True):
                if manager.start_service(service.id):
                    console.print("🚀 Service started")
                else:
                    console.print("❌ Service failed to start", style="red")
        except click.Abort:
            console.print("Skipped starting service")

    except ValueError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Failed to add service: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--status", is_flag=True, help="Show detailed status")
@click.pass_context
def list(ctx, status):
    """Show service list."""
    manager = ServiceManager(ctx.obj.get("config_path"))
    services = manager.list_services()

    if not services:
        console.print("No services found")
        return

    table = Table(title="Service List")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Command", style="blue")

    if status:
        table.add_column("PID", justify="right")
        table.add_column("Restart Count", justify="right")
        table.add_column("Created", style="dim")

    for service in services:
        status_style = _get_status_style(service.status)
        status_text = Text(service.status.value, style=status_style)

        row = [
            service.id[:8],
            service.name,
            status_text,
            (
                service.command[:50] + "..."
                if len(service.command) > 50
                else service.command
            ),
        ]

        if status:
            row.extend(
                [
                    str(service.pid) if service.pid else "-",
                    str(service.restart_count),
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(service.created_at)),
                ]
            )

        table.add_row(*row)

    console.print(table)


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.pass_context
def status(ctx, id, name):
    """Show service status."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        # Interactive selection
        services = manager.list_services()
        service = select_service(services, "Please select service to view status")
        if not service:
            return
        service_identifier = service.id

    status_info = manager.get_service_status(service_identifier)
    if not status_info:
        console.print("❌ Service not found", style="red")
        return

    service = status_info["service"]
    process_info = status_info["process"]
    uptime = status_info["uptime"]

    # Create status panel
    status_text = []
    status_text.append(f"ID: {service.id}")
    status_text.append(f"Name: {service.name}")
    status_text.append(f"Command: {service.command}")
    status_text.append(f"Status: {service.status.value}")
    status_text.append(
        f"Auto restart: {'Enabled' if service.auto_restart else 'Disabled'}"
    )
    status_text.append(f"Restart count: {service.restart_count}")
    status_text.append(f"Working directory: {service.working_dir}")

    if process_info:
        status_text.append(f"Process ID: {process_info['pid']}")
        status_text.append(f"CPU usage: {process_info['cpu_percent']:.1f}%")

        mem_mb = process_info["memory"]["rss"] / 1024 / 1024
        status_text.append(f"Memory usage: {mem_mb:.1f} MB")

        if uptime:
            hours, remainder = divmod(int(uptime), 3600)
            minutes, seconds = divmod(remainder, 60)
            status_text.append(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")

    status_text.append(
        f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(service.created_at))}"
    )
    status_text.append(
        f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(service.updated_at))}"
    )

    panel = Panel(
        "\n".join(status_text),
        title=f"Service Status - {service.name}",
        border_style=_get_status_style(service.status),
    )
    console.print(panel)


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.pass_context
def start(ctx, id, name):
    """Start service."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        # Interactive selection of stopped services
        services = [
            s for s in manager.list_services() if s.status == ServiceStatus.STOPPED
        ]
        service = select_service(services, "Please select service to start")
        if not service:
            return
        service_identifier = service.id

    if manager.start_service(service_identifier):
        console.print("🚀 Service started")
    else:
        console.print("❌ Service failed to start", style="red")


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.option("--force", is_flag=True, help="Force stop")
@click.pass_context
def stop(ctx, id, name, force):
    """Stop service."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        # Interactive selection of running services
        services = [
            s for s in manager.list_services() if s.status == ServiceStatus.RUNNING
        ]
        service = select_service(services, "Please select service to stop")
        if not service:
            return
        service_identifier = service.id

    if manager.stop_service(service_identifier, force):
        console.print("⏹️ Service stopped")
    else:
        console.print("❌ Service failed to stop", style="red")


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.option("--force", is_flag=True, help="Force restart")
@click.pass_context
def restart(ctx, id, name, force):
    """Restart service."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        services = manager.list_services()
        service = select_service(services, "Please select service to restart")
        if not service:
            return
        service_identifier = service.id

    if manager.restart_service(service_identifier, force):
        console.print("🔄 Service restarted")
    else:
        console.print("❌ Service failed to restart", style="red")


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.pass_context
def pause(ctx, id, name):
    """Pause service."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        services = [
            s for s in manager.list_services() if s.status == ServiceStatus.RUNNING
        ]
        service = select_service(services, "Please select service to pause")
        if not service:
            return
        service_identifier = service.id

    if manager.pause_service(service_identifier):
        console.print("⏸️ Service paused")
    else:
        console.print("❌ Service failed to pause", style="red")


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.pass_context
def resume(ctx, id, name):
    """Resume service."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        services = [
            s for s in manager.list_services() if s.status == ServiceStatus.PAUSED
        ]
        service = select_service(services, "Please select service to resume")
        if not service:
            return
        service_identifier = service.id

    if manager.resume_service(service_identifier):
        console.print("▶️ Service resumed")
    else:
        console.print("❌ Service failed to resume", style="red")


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.option("--force", is_flag=True, help="Force remove")
@click.pass_context
def remove(ctx, id, name, force):
    """Remove service."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        services = manager.list_services()
        service = select_service(services, "Please select service to remove")
        if not service:
            return
        service_identifier = service.name

    service = manager.get_service(service_identifier)
    if not service:
        console.print("❌ Service not found", style="red")
        return

    # Confirm removal
    if not force and not confirm_action("remove", service.name):
        console.print("Removal cancelled")
        return

    if manager.remove_service(service_identifier, force):
        console.print(f"🗑️ Service '{service.name}' removed")
    else:
        console.print("❌ Failed to remove service", style="red")


@cli.command()
@click.option("--id", help="Service ID")
@click.option("--name", help="Service name")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--tail", default=100, help="Show last N lines of log")
@click.option("--clear", is_flag=True, help="Clear logs")
@click.pass_context
def logs(ctx, id, name, follow, tail, clear):
    """View service logs."""
    manager = ServiceManager(ctx.obj.get("config_path"))

    service_identifier = id or name
    if not service_identifier:
        services = manager.list_services()
        service = select_service(services, "Please select service to view logs")
        if not service:
            return
        service_identifier = service.id

    service = manager.get_service(service_identifier)
    if not service:
        console.print("❌ Service not found", style="red")
        return

    if clear:
        if manager.clear_service_logs(service_identifier):
            console.print("🧹 Logs cleared")
        else:
            console.print("❌ Failed to clear logs", style="red")
        return

    log_lines = manager.get_service_logs(service_identifier, tail)
    if log_lines is None:
        console.print("❌ Unable to read logs", style="red")
        return

    if not log_lines:
        console.print("📝 No logs available")
        return

    # Display historical logs
    for line in log_lines:
        console.print(line.rstrip())

    # Real-time follow mode
    if follow:
        console.print("\n--- Live logs (Ctrl+C to exit) ---")
        try:
            log_path = manager.config_manager.get_service_log_path(service.id)
            with open(log_path, encoding="utf-8") as f:
                # Move to end of file
                f.seek(0, 2)

                while True:
                    line = f.readline()
                    if line:
                        console.print(line.rstrip())
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            console.print("\nLog following stopped")
        except Exception as e:
            console.print(f"❌ Log following failed: {e}", style="red")


@cli.command()
@click.option(
    "--action",
    type=click.Choice(["start", "stop", "restart", "status"]),
    default="status",
    help="Daemon operation",
)
@click.pass_context
def daemon(ctx, action):
    """Manage autostartx daemon."""
    daemon = AutostartxDaemon(ctx.obj.get("config_path"))

    if action == "start":
        console.print("🚀 Starting autostartx daemon...")
        daemon.start()
    elif action == "stop":
        console.print("🛑 Stopping autostartx daemon...")
        daemon.stop()
    elif action == "restart":
        console.print("🔄 Restarting autostartx daemon...")
        daemon.restart()
    elif action == "status":
        daemon.status()


@cli.command()
@click.pass_context
def monitor(ctx):
    """Start monitoring mode (foreground)."""
    console.print("🔍 Starting Autostartx monitoring mode...")
    console.print("Press Ctrl+C to stop monitoring")

    try:
        manager = AutoRestartManager(ctx.obj.get("config_path"))
        manager.start()
    except KeyboardInterrupt:
        console.print("\nMonitoring stopped")

@cli.command()
@click.pass_context
def install(ctx):
    """Install autostartx to system."""
    import shutil
    import sys
    import os
    
    # Get the script path
    script_path = sys.argv[0]
    
    # Determine install location
    if os.access('/usr/local/bin', os.W_OK):
        install_dir = '/usr/local/bin'
    elif os.path.expanduser('~/.local/bin'):
        install_dir = os.path.expanduser('~/.local/bin')
        os.makedirs(install_dir, exist_ok=True)
    else:
        console.print("[red]Error: No writable install directory found[/red]")
        return
    
    install_path = os.path.join(install_dir, 'autostartx')
    
    try:
        shutil.copy2(script_path, install_path)
        os.chmod(install_path, 0o755)
        console.print(f"[green]Successfully installed autostartx to {install_path}[/green]")
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")


def _get_status_style(status: ServiceStatus) -> str:
    """Get status style."""
    styles = {
        ServiceStatus.RUNNING: "green",
        ServiceStatus.STOPPED: "red",
        ServiceStatus.PAUSED: "yellow",
        ServiceStatus.FAILED: "bright_red",
        ServiceStatus.STARTING: "cyan",
    }
    return styles.get(status, "white")


def main():
    """Main entry function."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\nOperation cancelled")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Error occurred: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
