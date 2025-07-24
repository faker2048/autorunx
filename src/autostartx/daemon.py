"""Daemon process module."""

import atexit
import os
import signal
import sys
from pathlib import Path

from .monitor import AutoRestartManager


class Daemon:
    """Daemon process base class."""

    def __init__(self, pidfile: str):
        self.pidfile = pidfile

    def daemonize(self) -> None:
        """Daemonize process."""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Parent process exits
        except OSError as e:
            sys.stderr.write(f"fork #1 failed: {e}\n")
            sys.exit(1)

        # Detach from parent process environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # First child process exits
        except OSError as e:
            sys.stderr.write(f"fork #2 failed: {e}\n")
            sys.exit(1)

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        si = open(os.devnull)
        so = open(os.devnull, "a+")
        se = open(os.devnull, "a+")

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Write pid file
        atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self.pidfile, "w+") as f:
            f.write(f"{pid}\n")

    def delpid(self) -> None:
        """Delete pid file."""
        try:
            os.remove(self.pidfile)
        except OSError:
            pass

    def start(self) -> None:
        """Start daemon process."""
        # Check if pid file exists
        try:
            with open(self.pidfile) as pf:
                pid = int(pf.read().strip())
        except (OSError, ValueError):
            pid = None

        if pid:
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Send signal 0 to check if process exists
                print(f"Daemon already running, PID: {pid}")
                sys.exit(1)
            except OSError:
                # Process doesn't exist, delete old pid file
                self.delpid()

        # Start daemon process
        self.daemonize()
        self.run()

    def stop(self) -> None:
        """Stop daemon process."""
        try:
            with open(self.pidfile) as pf:
                pid = int(pf.read().strip())
        except (OSError, ValueError):
            pid = None

        if not pid:
            print("Daemon not running")
            return

        # Try to terminate process
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                import time

                time.sleep(0.1)
        except OSError as err:
            if "No such process" in str(err):
                self.delpid()
                print("Daemon stopped")
            else:
                print(f"Failed to stop daemon: {err}")
                sys.exit(1)

    def restart(self) -> None:
        """Restart daemon process."""
        self.stop()
        self.start()

    def status(self) -> None:
        """Check daemon process status."""
        try:
            with open(self.pidfile) as pf:
                pid = int(pf.read().strip())
        except (OSError, ValueError):
            print("Daemon not running")
            return

        try:
            os.kill(pid, 0)
            print(f"Daemon is running, PID: {pid}")
        except OSError:
            print("Daemon not running (pid file exists but process doesn't exist)")
            self.delpid()

    def run(self) -> None:
        """Run daemon process - subclasses need to override this method."""
        raise NotImplementedError


class AutostartxDaemon(Daemon):
    """Autostartx daemon process."""

    def __init__(self, config_path: str = None):
        # Set pid file path
        config_dir = Path.home() / ".config" / "autostartx"
        config_dir.mkdir(parents=True, exist_ok=True)
        pidfile = str(config_dir / "autostartx.pid")

        super().__init__(pidfile)
        self.config_path = config_path
        self.manager = None

    def run(self) -> None:
        """Run auto-restart manager."""
        self.manager = AutoRestartManager(self.config_path)

        # Set signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Start manager
        self.manager.start()

    def _signal_handler(self, signum, frame) -> None:
        """Signal handler."""
        if self.manager:
            self.manager.stop()
        sys.exit(0)
