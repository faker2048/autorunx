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
        console.print(f"Auto restart: {'Enabled' if service.auto_restart else 'Disabled'}")

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
            (service.command[:50] + "..." if len(service.command) > 50 else service.command),
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
    status_text.append(f"Auto restart: {'Enabled' if service.auto_restart else 'Disabled'}")
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
        services = [s for s in manager.list_services() if s.status == ServiceStatus.STOPPED]
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
        services = [s for s in manager.list_services() if s.status == ServiceStatus.RUNNING]
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
        services = [s for s in manager.list_services() if s.status == ServiceStatus.RUNNING]
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
        services = [s for s in manager.list_services() if s.status == ServiceStatus.PAUSED]
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

    # Check if service is running
    if service.status == ServiceStatus.RUNNING:
        if not force:
            console.print(f"⚠️  Service '{service.name}' is currently running", style="yellow")
            console.print("You need to stop it first before removing:")
            console.print(f"  autostartx stop {service.name}", style="cyan")
            console.print("Or use --force to stop and remove:", style="dim")
            console.print(f"  autostartx remove {service.name} --force", style="dim")
            return
        else:
            console.print(f"🛑 Stopping running service '{service.name}' before removal...")

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
@click.option("--enable-autostart", is_flag=True, help="Enable system autostart after installation")
@click.pass_context
def install(ctx, enable_autostart):
    """Install autostartx to system."""
    import os
    import shutil
    import sys

    # Get the script path
    script_path = sys.argv[0]

    # Determine install location
    if os.access("/usr/local/bin", os.W_OK):
        install_dir = "/usr/local/bin"
    elif os.path.expanduser("~/.local/bin"):
        install_dir = os.path.expanduser("~/.local/bin")
        os.makedirs(install_dir, exist_ok=True)
    else:
        console.print("[red]Error: No writable install directory found[/red]")
        return

    install_path = os.path.join(install_dir, "autostartx")

    try:
        shutil.copy2(script_path, install_path)
        os.chmod(install_path, 0o755)
        console.print(f"[green]Successfully installed autostartx to {install_path}[/green]")
        
        # Ask about autostart if not explicitly specified
        if not enable_autostart:
            import platform
            system = platform.system().lower()
            supported_platforms = ["linux", "windows", "darwin"]
            
            if system in supported_platforms:
                try:
                    platform_name = {"linux": "Linux", "windows": "Windows", "darwin": "macOS"}[system]
                    enable_autostart = click.confirm(
                        f"Do you want to enable system autostart on {platform_name}? (autostartx will start automatically after reboot/login)",
                        default=True
                    )
                except click.Abort:
                    enable_autostart = False
            else:
                console.print(f"[yellow]Note: System autostart is not supported on {system}[/yellow]")
        
        # Setup autostart if requested
        if enable_autostart:
            console.print("\n🚀 Setting up system autostart...")
            # Use the new autostart command with the installed path
            import subprocess
            try:
                # Update PATH to include install directory for the autostart command
                env = os.environ.copy()
                if install_dir not in env.get('PATH', ''):
                    env['PATH'] = f"{install_dir}:{env.get('PATH', '')}"
                
                result = subprocess.run(
                    [install_path, "autostart", "enable"],
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    console.print("[green]✅ Autostart enabled successfully![/green]")
                    console.print("[dim]Autostartx will start automatically after reboot[/dim]")
                else:
                    console.print(f"[yellow]Warning: Could not enable autostart: {result.stderr}[/yellow]")
                    console.print(f"[dim]You can enable it later with: {install_path} autostart enable[/dim]")
            
            except Exception as e:
                console.print(f"[yellow]Warning: Could not enable autostart: {e}[/yellow]")
                console.print(f"[dim]You can enable it later with: {install_path} autostart enable[/dim]")
        
        # Show next steps
        console.print(f"\n[bold green]Installation complete![/bold green]")
        console.print(f"Next steps:")
        console.print(f"1. Add services: [cyan]autostartx add \"your-command\"[/cyan]")
        if not enable_autostart:
            console.print(f"2. Enable autostart: [cyan]autostartx autostart enable[/cyan]")
        console.print(f"3. Start daemon: [cyan]autostartx daemon start[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")


@cli.command()
@click.option(
    "--action",
    type=click.Choice(["enable", "disable", "status"]),
    default="status",
    help="Autostart operation",
)
@click.pass_context
def autostart(ctx, action):
    """Manage system autostart for autostartx daemon."""
    import platform
    import subprocess
    from pathlib import Path

    def get_systemd_service_path():
        return Path.home() / ".config" / "systemd" / "user" / "autostartx.service"

    def create_systemd_service():
        """Create systemd user service file."""
        service_path = get_systemd_service_path()
        service_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get autostartx executable path
        try:
            autostartx_path = subprocess.check_output(["which", "autostartx"], text=True).strip()
        except subprocess.CalledProcessError:
            # Fallback to common paths
            for path in ["/usr/local/bin/autostartx", os.path.expanduser("~/.local/bin/autostartx")]:
                if os.path.exists(path):
                    autostartx_path = path
                    break
            else:
                console.print("[red]Error: autostartx executable not found in PATH[/red]")
                return False

        service_content = f"""[Unit]
Description=Autostartx Service Manager
After=default.target

[Service]
Type=forking
ExecStart={autostartx_path} daemon start
ExecStop={autostartx_path} daemon stop
Restart=always
RestartSec=5
Environment=PATH={os.environ.get('PATH', '')}

[Install]
WantedBy=default.target
"""
        
        try:
            with open(service_path, 'w') as f:
                f.write(service_content)
            console.print(f"[green]Created systemd service: {service_path}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to create systemd service: {e}[/red]")
            return False

    def enable_systemd_autostart():
        """Enable systemd user service."""
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True)
            subprocess.run(["systemctl", "--user", "enable", "autostartx.service"], check=True, capture_output=True)
            console.print("[green]✅ Autostart enabled via systemd[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to enable systemd service: {e}[/red]")
            return False

    def disable_systemd_autostart():
        """Disable systemd user service."""
        try:
            subprocess.run(["systemctl", "--user", "disable", "autostartx.service"], check=True, capture_output=True)
            console.print("[green]🛑 Autostart disabled[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to disable systemd service: {e}[/red]")
            return False

    def check_systemd_status():
        """Check systemd service status."""
        service_path = get_systemd_service_path()
        if not service_path.exists():
            return False, "Service file not found"
        
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-enabled", "autostartx.service"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip() == "enabled":
                return True, "enabled"
            else:
                return False, "disabled"
        except subprocess.CalledProcessError:
            return False, "unknown"

    # Main logic
    system = platform.system().lower()
    
    # Platform-specific implementations
    def handle_windows_autostart(action):
        """Handle Windows autostart via registry."""
        try:
            import winreg
        except ImportError:
            console.print("[red]Error: Windows registry module not available[/red]")
            return False
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        value_name = "Autostartx"
        
        try:
            # Get autostartx executable path
            autostartx_path = None
            try:
                import shutil
                autostartx_path = shutil.which("autostartx")
            except:
                pass
            
            if not autostartx_path:
                for path in [r"C:\Program Files\autostartx\autostartx.exe", 
                           os.path.expanduser(r"~\AppData\Local\Programs\autostartx\autostartx.exe")]:
                    if os.path.exists(path):
                        autostartx_path = path
                        break
                        
            if not autostartx_path:
                console.print("[red]Error: autostartx executable not found[/red]")
                return False
            
            if action == "enable":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, f'"{autostartx_path}" daemon start')
                console.print("[green]✅ Autostart enabled via Windows registry[/green]")
                return True
                
            elif action == "disable":
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, value_name)
                    console.print("[green]🛑 Autostart disabled[/green]")
                    return True
                except FileNotFoundError:
                    console.print("[yellow]Autostart was not enabled[/yellow]")
                    return True
                    
            elif action == "status":
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                        value, _ = winreg.QueryValueEx(key, value_name)
                        return True, "enabled"
                except FileNotFoundError:
                    return False, "disabled"
                    
        except Exception as e:
            console.print(f"[red]Windows registry operation failed: {e}[/red]")
            return False
    
    def handle_macos_autostart(action):
        """Handle macOS autostart via LaunchAgent."""
        from pathlib import Path
        import plistlib
        
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        plist_file = launch_agents_dir / "com.autostartx.daemon.plist"
        
        try:
            # Get autostartx executable path
            autostartx_path = None
            try:
                import shutil
                autostartx_path = shutil.which("autostartx")
            except:
                pass
                
            if not autostartx_path:
                for path in ["/usr/local/bin/autostartx", os.path.expanduser("~/.local/bin/autostartx")]:
                    if os.path.exists(path):
                        autostartx_path = path
                        break
                        
            if not autostartx_path:
                console.print("[red]Error: autostartx executable not found[/red]")
                return False
            
            if action == "enable":
                launch_agents_dir.mkdir(parents=True, exist_ok=True)
                
                plist_content = {
                    "Label": "com.autostartx.daemon",
                    "ProgramArguments": [autostartx_path, "daemon", "start"],
                    "RunAtLoad": True,
                    "KeepAlive": {
                        "SuccessfulExit": False
                    },
                    "StandardOutPath": str(Path.home() / ".local" / "share" / "autostartx" / "logs" / "daemon.log"),
                    "StandardErrorPath": str(Path.home() / ".local" / "share" / "autostartx" / "logs" / "daemon.error.log")
                }
                
                with open(plist_file, 'wb') as f:
                    plistlib.dump(plist_content, f)
                
                # Load the agent
                subprocess.run(["launchctl", "load", str(plist_file)], check=True, capture_output=True)
                console.print("[green]✅ Autostart enabled via macOS LaunchAgent[/green]")
                return True
                
            elif action == "disable":
                if plist_file.exists():
                    try:
                        subprocess.run(["launchctl", "unload", str(plist_file)], capture_output=True)
                        plist_file.unlink()
                        console.print("[green]🛑 Autostart disabled[/green]")
                        return True
                    except Exception as e:
                        console.print(f"[red]Failed to disable LaunchAgent: {e}[/red]")
                        return False
                else:
                    console.print("[yellow]Autostart was not enabled[/yellow]")
                    return True
                    
            elif action == "status":
                if plist_file.exists():
                    try:
                        result = subprocess.run(
                            ["launchctl", "list", "com.autostartx.daemon"],
                            capture_output=True, text=True
                        )
                        if result.returncode == 0:
                            return True, "enabled"
                        else:
                            return False, "disabled"
                    except Exception:
                        return False, "unknown"
                else:
                    return False, "disabled"
                    
        except Exception as e:
            console.print(f"[red]macOS LaunchAgent operation failed: {e}[/red]")
            return False
    
    # Route to appropriate platform handler
    if system == "windows":
        if action == "enable":
            console.print("🚀 Enabling autostartx autostart on Windows...")
            if handle_windows_autostart("enable"):
                console.print("[green]✅ Autostart successfully enabled![/green]")
                console.print("[dim]Autostartx daemon will start automatically after login[/dim]")
            else:
                console.print("[red]❌ Failed to enable autostart[/red]")
            return
        elif action == "disable":
            console.print("🛑 Disabling autostartx autostart on Windows...")
            handle_windows_autostart("disable")
            return
        elif action == "status":
            console.print("📊 Checking autostart status on Windows...")
            enabled, status = handle_windows_autostart("status")
            if enabled:
                console.print("[green]✅ Autostart is enabled[/green]")
            else:
                console.print(f"[yellow]❌ Autostart is disabled ({status})[/yellow]")
            return
    elif system == "darwin":  # macOS
        if action == "enable":
            console.print("🚀 Enabling autostartx autostart on macOS...")
            if handle_macos_autostart("enable"):
                console.print("[green]✅ Autostart successfully enabled![/green]")
                console.print("[dim]Autostartx daemon will start automatically after login[/dim]")
            else:
                console.print("[red]❌ Failed to enable autostart[/red]")
            return
        elif action == "disable":
            console.print("🛑 Disabling autostartx autostart on macOS...")
            handle_macos_autostart("disable")
            return
        elif action == "status":
            console.print("📊 Checking autostart status on macOS...")
            enabled, status = handle_macos_autostart("status")
            if enabled:
                console.print("[green]✅ Autostart is enabled[/green]")
            else:
                console.print(f"[yellow]❌ Autostart is disabled ({status})[/yellow]")
            return
    elif system != "linux":
        console.print(f"[yellow]Autostart is not supported on {system}[/yellow]")
        console.print("[yellow]Supported platforms: Linux (systemd), Windows (registry), macOS (LaunchAgent)[/yellow]")
        return

    if action == "enable":
        console.print("🚀 Enabling autostartx autostart...")
        if create_systemd_service() and enable_systemd_autostart():
            console.print("[green]✅ Autostart successfully enabled![/green]")
            console.print("[dim]Autostartx daemon will start automatically after reboot[/dim]")
        else:
            console.print("[red]❌ Failed to enable autostart[/red]")
    
    elif action == "disable":
        console.print("🛑 Disabling autostartx autostart...")
        if disable_systemd_autostart():
            # Optionally remove service file
            service_path = get_systemd_service_path()
            if service_path.exists():
                try:
                    service_path.unlink()
                    console.print("[dim]Removed systemd service file[/dim]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not remove service file: {e}[/yellow]")
        else:
            console.print("[red]❌ Failed to disable autostart[/red]")
    
    elif action == "status":
        console.print("📊 Checking autostart status...")
        enabled, status = check_systemd_status()
        
        if enabled:
            console.print("[green]✅ Autostart is enabled[/green]")
        else:
            console.print(f"[yellow]❌ Autostart is disabled ({status})[/yellow]")
        
        # Check if daemon is currently running
        daemon = AutostartxDaemon(ctx.obj.get("config_path"))
        try:
            with open(daemon.pidfile) as pf:
                pid = int(pf.read().strip())
            try:
                os.kill(pid, 0)
                console.print("[green]🟢 Daemon is currently running[/green]")
            except OSError:
                console.print("[yellow]🟡 Daemon is not running[/yellow]")
        except (OSError, ValueError):
            console.print("[yellow]🟡 Daemon is not running[/yellow]")

@cli.command()
@click.option("--remove-config", is_flag=True, help="Also remove configuration and data files")
@click.pass_context
def uninstall(ctx, remove_config):
    """Uninstall autostartx from system."""
    import subprocess
    from pathlib import Path
    
    console.print("🗑️ Uninstalling autostartx...")
    
    # First, disable autostart
    try:
        result = subprocess.run(
            ["autostartx", "autostart", "disable"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            console.print("[green]✅ Autostart disabled[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not disable autostart: {e}[/yellow]")
    
    # Stop daemon if running
    try:
        daemon = AutostartxDaemon(ctx.obj.get("config_path"))
        daemon.stop()
        console.print("[green]✅ Daemon stopped[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not stop daemon: {e}[/yellow]")
    
    # Remove executable
    removed_paths = []
    for path in ["/usr/local/bin/autostartx", os.path.expanduser("~/.local/bin/autostartx")]:
        if os.path.exists(path):
            try:
                os.remove(path)
                removed_paths.append(path)
                console.print(f"[green]✅ Removed: {path}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Failed to remove {path}: {e}[/red]")
    
    if not removed_paths:
        console.print("[yellow]⚠️ No autostartx executable found to remove[/yellow]")
    
    # Optionally remove config and data
    if remove_config:
        config_dirs = [
            Path.home() / ".config" / "autostartx",
            Path.home() / ".local" / "share" / "autostartx"
        ]
        
        for config_dir in config_dirs:
            if config_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(config_dir)
                    console.print(f"[green]✅ Removed: {config_dir}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Failed to remove {config_dir}: {e}[/red]")
    else:
        console.print("[dim]Configuration and data files preserved[/dim]")
        console.print("[dim]Use --remove-config to remove all data[/dim]")
    
    console.print("\n[bold green]Uninstallation complete![/bold green]")


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
