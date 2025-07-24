"""守护进程模块."""

import os
import sys
import signal
import atexit
from pathlib import Path
from .monitor import AutoRestartManager


class Daemon:
    """守护进程基类."""
    
    def __init__(self, pidfile: str):
        self.pidfile = pidfile
    
    def daemonize(self) -> None:
        """守护进程化."""
        try:
            # 第一次fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # 父进程退出
        except OSError as e:
            sys.stderr.write(f"fork #1 failed: {e}\n")
            sys.exit(1)
        
        # 脱离父进程环境
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        try:
            # 第二次fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # 第一个子进程退出
        except OSError as e:
            sys.stderr.write(f"fork #2 failed: {e}\n")
            sys.exit(1)
        
        # 重定向标准文件描述符
        sys.stdout.flush()
        sys.stderr.flush()
        
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')
        
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        # 写入pid文件
        atexit.register(self.delpid)
        
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write(f"{pid}\n")
    
    def delpid(self) -> None:
        """删除pid文件."""
        try:
            os.remove(self.pidfile)
        except OSError:
            pass
    
    def start(self) -> None:
        """启动守护进程."""
        # 检查pid文件是否存在
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except (IOError, ValueError):
            pid = None
        
        if pid:
            # 检查进程是否还在运行
            try:
                os.kill(pid, 0)  # 发送信号0检查进程是否存在
                print(f"守护进程已在运行，PID: {pid}")
                sys.exit(1)
            except OSError:
                # 进程不存在，删除旧的pid文件
                self.delpid()
        
        # 启动守护进程
        self.daemonize()
        self.run()
    
    def stop(self) -> None:
        """停止守护进程."""
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except (IOError, ValueError):
            pid = None
        
        if not pid:
            print("守护进程未运行")
            return
        
        # 尝试终止进程
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                import time
                time.sleep(0.1)
        except OSError as err:
            if "No such process" in str(err):
                self.delpid()
                print("守护进程已停止")
            else:
                print(f"停止守护进程失败: {err}")
                sys.exit(1)
    
    def restart(self) -> None:
        """重启守护进程."""
        self.stop()
        self.start()
    
    def status(self) -> None:
        """查看守护进程状态."""
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except (IOError, ValueError):
            print("守护进程未运行")
            return
        
        try:
            os.kill(pid, 0)
            print(f"守护进程正在运行，PID: {pid}")
        except OSError:
            print("守护进程未运行（pid文件存在但进程不存在）")
            self.delpid()
    
    def run(self) -> None:
        """运行守护进程 - 子类需要重写此方法."""
        raise NotImplementedError


class AutostartxDaemon(Daemon):
    """Autostartx 守护进程."""
    
    def __init__(self, config_path: str = None):
        # 设置pid文件路径
        config_dir = Path.home() / ".config" / "autostartx"
        config_dir.mkdir(parents=True, exist_ok=True)
        pidfile = str(config_dir / "autostartx.pid")
        
        super().__init__(pidfile)
        self.config_path = config_path
        self.manager = None
    
    def run(self) -> None:
        """运行自动重启管理器."""
        self.manager = AutoRestartManager(self.config_path)
        
        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # 启动管理器
        self.manager.start()
    
    def _signal_handler(self, signum, frame) -> None:
        """信号处理器."""
        if self.manager:
            self.manager.stop()
        sys.exit(0)