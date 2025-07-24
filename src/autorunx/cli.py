"""命令行界面."""

import os
import sys
import time
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.panel import Panel

from .service_manager import ServiceManager
from .models import ServiceStatus
from .interactive import select_service, confirm_action
from .daemon import AutoRunXDaemon
from .monitor import AutoRestartManager
from . import __version__


console = Console()


@click.group()
@click.version_option(version=__version__)
@click.option('--config', help='配置文件路径')
@click.pass_context
def cli(ctx, config):
    """AutoRunX - 命令行程序服务化工具."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.command()
@click.argument('command')
@click.option('--name', help='服务名称')
@click.option('--no-auto-restart', is_flag=True, help='禁用自动重启')
@click.option('--working-dir', help='工作目录')
@click.pass_context
def add(ctx, command, name, no_auto_restart, working_dir):
    """添加新服务."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    # 如果没有指定名称，生成一个
    if not name:
        name = f"service-{int(time.time())}"
    
    auto_restart = not no_auto_restart
    working_dir = working_dir or os.getcwd()
    
    try:
        service = manager.add_service(
            name=name,
            command=command,
            auto_restart=auto_restart,
            working_dir=working_dir
        )
        
        console.print(f"✅ 服务已添加: {service.name} ({service.id})")
        console.print(f"命令: {service.command}")
        console.print(f"自动重启: {'开启' if service.auto_restart else '关闭'}")
        
        # 询问是否立即启动
        try:
            if click.confirm("是否立即启动服务?", default=True):
                if manager.start_service(service.id):
                    console.print("🚀 服务已启动")
                else:
                    console.print("❌ 服务启动失败", style="red")
        except click.Abort:
            console.print("跳过启动服务")
                
    except ValueError as e:
        console.print(f"❌ 错误: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ 添加服务失败: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--status', is_flag=True, help='显示详细状态')
@click.pass_context
def list(ctx, status):
    """显示服务列表."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    services = manager.list_services()
    
    if not services:
        console.print("没有找到服务")
        return
    
    table = Table(title="服务列表")
    table.add_column("ID", style="cyan")
    table.add_column("名称", style="magenta")
    table.add_column("状态", justify="center")
    table.add_column("命令", style="blue")
    
    if status:
        table.add_column("PID", justify="right")
        table.add_column("重启次数", justify="right")
        table.add_column("创建时间", style="dim")
    
    for service in services:
        status_style = _get_status_style(service.status)
        status_text = Text(service.status.value, style=status_style)
        
        row = [
            service.id[:8],
            service.name,
            status_text,
            service.command[:50] + "..." if len(service.command) > 50 else service.command,
        ]
        
        if status:
            row.extend([
                str(service.pid) if service.pid else "-",
                str(service.restart_count),
                time.strftime("%Y-%m-%d %H:%M", time.localtime(service.created_at)),
            ])
        
        table.add_row(*row)
    
    console.print(table)


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称')
@click.pass_context
def status(ctx, id, name):
    """显示服务状态."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        # 交互式选择
        services = manager.list_services()
        service = select_service(services, "请选择要查看状态的服务")
        if not service:
            return
        service_identifier = service.id
    
    status_info = manager.get_service_status(service_identifier)
    if not status_info:
        console.print("❌ 服务不存在", style="red")
        return
    
    service = status_info['service']
    process_info = status_info['process']
    uptime = status_info['uptime']
    
    # 创建状态面板
    status_text = []
    status_text.append(f"ID: {service.id}")
    status_text.append(f"名称: {service.name}")
    status_text.append(f"命令: {service.command}")
    status_text.append(f"状态: {service.status.value}")
    status_text.append(f"自动重启: {'开启' if service.auto_restart else '关闭'}")
    status_text.append(f"重启次数: {service.restart_count}")
    status_text.append(f"工作目录: {service.working_dir}")
    
    if process_info:
        status_text.append(f"进程ID: {process_info['pid']}")
        status_text.append(f"CPU使用率: {process_info['cpu_percent']:.1f}%")
        
        mem_mb = process_info['memory']['rss'] / 1024 / 1024
        status_text.append(f"内存使用: {mem_mb:.1f} MB")
        
        if uptime:
            hours, remainder = divmod(int(uptime), 3600)
            minutes, seconds = divmod(remainder, 60)
            status_text.append(f"运行时间: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    status_text.append(f"创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(service.created_at))}")
    status_text.append(f"更新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(service.updated_at))}")
    
    panel = Panel(
        "\n".join(status_text),
        title=f"服务状态 - {service.name}",
        border_style=_get_status_style(service.status)
    )
    console.print(panel)


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称')
@click.pass_context
def start(ctx, id, name):
    """启动服务."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        # 交互式选择停止的服务
        services = [s for s in manager.list_services() if s.status == ServiceStatus.STOPPED]
        service = select_service(services, "请选择要启动的服务")
        if not service:
            return
        service_identifier = service.id
    
    if manager.start_service(service_identifier):
        console.print("🚀 服务已启动")
    else:
        console.print("❌ 服务启动失败", style="red")


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称')
@click.option('--force', is_flag=True, help='强制停止')
@click.pass_context
def stop(ctx, id, name, force):
    """停止服务."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        # 交互式选择运行中的服务
        services = [s for s in manager.list_services() if s.status == ServiceStatus.RUNNING]
        service = select_service(services, "请选择要停止的服务")
        if not service:
            return
        service_identifier = service.id
    
    if manager.stop_service(service_identifier, force):
        console.print("⏹️ 服务已停止")
    else:
        console.print("❌ 服务停止失败", style="red")


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称')
@click.option('--force', is_flag=True, help='强制重启')
@click.pass_context
def restart(ctx, id, name, force):
    """重启服务."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        services = manager.list_services()
        service = select_service(services, "请选择要重启的服务")
        if not service:
            return
        service_identifier = service.id
    
    if manager.restart_service(service_identifier, force):
        console.print("🔄 服务已重启")
    else:
        console.print("❌ 服务重启失败", style="red")


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称')
@click.pass_context
def pause(ctx, id, name):
    """暂停服务."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        services = [s for s in manager.list_services() if s.status == ServiceStatus.RUNNING]
        service = select_service(services, "请选择要暂停的服务")
        if not service:
            return
        service_identifier = service.id
    
    if manager.pause_service(service_identifier):
        console.print("⏸️ 服务已暂停")
    else:
        console.print("❌ 服务暂停失败", style="red")


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称') 
@click.pass_context
def resume(ctx, id, name):
    """恢复服务."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        services = [s for s in manager.list_services() if s.status == ServiceStatus.PAUSED]
        service = select_service(services, "请选择要恢复的服务")
        if not service:
            return
        service_identifier = service.id
    
    if manager.resume_service(service_identifier):
        console.print("▶️ 服务已恢复")
    else:
        console.print("❌ 服务恢复失败", style="red")


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称')
@click.option('--force', is_flag=True, help='强制删除')
@click.pass_context
def remove(ctx, id, name, force):
    """删除服务."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        services = manager.list_services()
        service = select_service(services, "请选择要删除的服务")
        if not service:
            return
        service_identifier = service.name
    
    service = manager.get_service(service_identifier)
    if not service:
        console.print("❌ 服务不存在", style="red")
        return
    
    # 确认删除
    if not force and not confirm_action("删除", service.name):
        console.print("已取消删除")
        return
    
    if manager.remove_service(service_identifier, force):
        console.print(f"🗑️ 服务 '{service.name}' 已删除")
    else:
        console.print("❌ 删除服务失败", style="red")


@cli.command()
@click.option('--id', help='服务ID')
@click.option('--name', help='服务名称')
@click.option('--follow', '-f', is_flag=True, help='实时跟踪日志')
@click.option('--tail', default=100, help='显示最后N行日志')
@click.option('--clear', is_flag=True, help='清空日志')
@click.pass_context
def logs(ctx, id, name, follow, tail, clear):
    """查看服务日志."""
    manager = ServiceManager(ctx.obj.get('config_path'))
    
    service_identifier = id or name
    if not service_identifier:
        services = manager.list_services()
        service = select_service(services, "请选择要查看日志的服务")
        if not service:
            return
        service_identifier = service.id
    
    service = manager.get_service(service_identifier)
    if not service:
        console.print("❌ 服务不存在", style="red")
        return
    
    if clear:
        if manager.clear_service_logs(service_identifier):
            console.print("🧹 日志已清空")
        else:
            console.print("❌ 清空日志失败", style="red")
        return
    
    log_lines = manager.get_service_logs(service_identifier, tail)
    if log_lines is None:
        console.print("❌ 无法读取日志", style="red")
        return
    
    if not log_lines:
        console.print("📝 暂无日志")
        return
    
    # 显示历史日志
    for line in log_lines:
        console.print(line.rstrip())
    
    # 实时跟踪模式
    if follow:
        console.print("\n--- 实时日志 (Ctrl+C 退出) ---")
        try:
            log_path = manager.config_manager.get_service_log_path(service.id)
            with open(log_path, 'r', encoding='utf-8') as f:
                # 移动到文件末尾
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        console.print(line.rstrip())
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            console.print("\n已停止日志跟踪")
        except Exception as e:
            console.print(f"❌ 日志跟踪失败: {e}", style="red")


@cli.command()
@click.option('--action', type=click.Choice(['start', 'stop', 'restart', 'status']), 
              default='status', help='守护进程操作')
@click.pass_context
def daemon(ctx, action):
    """管理 autorunx 守护进程."""
    daemon = AutoRunXDaemon(ctx.obj.get('config_path'))
    
    if action == 'start':
        console.print("🚀 启动 autorunx 守护进程...")
        daemon.start()
    elif action == 'stop':
        console.print("🛑 停止 autorunx 守护进程...")
        daemon.stop()
    elif action == 'restart':
        console.print("🔄 重启 autorunx 守护进程...")
        daemon.restart()
    elif action == 'status':
        daemon.status()


@cli.command()
@click.pass_context
def monitor(ctx):
    """启动监控模式（前台运行）."""
    console.print("🔍 启动 AutoRunX 监控模式...")
    console.print("按 Ctrl+C 停止监控")
    
    try:
        manager = AutoRestartManager(ctx.obj.get('config_path'))
        manager.start()
    except KeyboardInterrupt:
        console.print("\n监控已停止")


def _get_status_style(status: ServiceStatus) -> str:
    """获取状态样式."""
    styles = {
        ServiceStatus.RUNNING: "green",
        ServiceStatus.STOPPED: "red",
        ServiceStatus.PAUSED: "yellow",
        ServiceStatus.FAILED: "bright_red",
        ServiceStatus.STARTING: "cyan",
    }
    return styles.get(status, "white")


def main():
    """主入口函数."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n已取消操作")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ 发生错误: {e}", style="red")
        sys.exit(1)


if __name__ == '__main__':
    main()