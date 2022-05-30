"""
    Tasks for providing source and target(s).
"""

import os
from pathlib import Path
try:
    from PySide2.QtWidgets import QMessageBox, QApplication
    from PySide2.QtCore import QTimer
except ImportError:
    QApplication = None
import select
import subprocess
import sys

import log

from tester import TesterFactory

plog = log.get_logger('pyb.provider')

class ProvideError(Exception):
    pass

class PostrequisiteError(ProvideError):
    pass

class Provider:
    """Provides sources, targets, etc
        Base class, provides testing and releasing.
    """
    def __init__(self, name, config):
        self.name = name
        plog.debug("Provider %s", name)
        self.goal = TesterFactory(config.get('unless', ''))
        if 'postrequisite' in config:
            self.post = TesterFactory(config['postrequisite'])
        else:
            self.post = self.goal.default_postrequisite()
        plog.debug("Provider %s created", name)
        self.provided = False

    def __enter__(self):
        if self.goal.test():
            plog.info("No need to provide %s", self.name)
            return self
        aqresult = self.acquire()
        if aqresult and aqresult.returncode == 0:
            plog.info("Provided %s", self.name)
            self.provided = True
        else:
            plog.error("Acquiring %s failed. Exit %d stderr <%s>",
                    self.name, aqresult.returncode, aqresult.stderr.strip())
            raise ProvideError(self.name)
        if not self.post.test():
            plog.error("Postrequisite for %s failed", self.name)
            raise PostrequisiteError(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.provided:
            plog.info("Not releasing unacquired %s", self.name)
            return False
        rlresult = self.release()
        if rlresult.returncode == 0:
            self.provided = False
        else:
            plog.error("Releasing %s failed. Exit %d Output %s",
                    self.name, rlresult.returncode, rlresult.stderr)
        # is exc_type a ProvideError or a derivative of ProvideError?
        return not exc_type or ProvideError in exc_type.__mro__

    def acquire(self):
        plog.info("Acquiring %s", self.name)
        return self.success()

    def release(self):
        plog.info("Releasing %s", self.name)
        return self.success()

    @classmethod
    def success(cls):
        return subprocess.CompletedProcess(args=['true'], returncode=0, stdout="", stderr="")

    @classmethod
    def failure(cls, reason=""):
        return subprocess.CompletedProcess(args=['false'], returncode=1, stdout="", stderr=reason)

class DirectoryProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.dir = Path(config.get('dir', ''))

    def acquire(self):
        try:
            self.dir.mkdir(exist_ok=False)
            return self.success()
        except FileExistsError as fee:
            return self.failure(str(fee))

    def release(self):
        try:
            self.dir.rmdir()
            return self.success()
        except OSError as oe:
            return self.failure(str(oe))

class ManualProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.message = config.get('message', f'Bitte {name} bereitstellen')
        self.title = config.get('title', 'Manueller Eingriff erforderlich')
        self.timeout = float(config.get('timeout', 60))

    def acquire(self):
        if not super().acquire():
            return self.failure()
        if QApplication and os.environ.get('DISPLAY', False):
            return self.dialog_()
        return self.commandline_()

    def dialog_(self):
        app = QApplication(['ManualProvider'])
        QTimer.singleShot(self.timeout * 1000, app.closeAllWindows)
        button = QMessageBox.question(None, self.title, self.message)
        if button == QMessageBox.Yes:
            plog.info("Manual dialog Yes")
            return self.success()
        plog.info("Manual dialog No or Timeout")
        return self.failure("Manual abort")

    def commandline_(self):
        print(self.title)
        print(self.message + " [yes or ja to confirm]")
        i, _, _ = select.select([sys.stdin], [], [], self.timeout)
        if i:
            inp = sys.stdin.readline().strip().lower()
            if inp and inp[0] in 'yj':
                return self.success()
            return self.failure("Manual abort")
        return self.failure("Timeout")

class SshFsProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.user = config.get('user', '')
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('remote_port', '22')
        self.local_path = config.get('local_path', '/home')
        self.mountopts = config.get('mountopts', '').split()

    def acquire(self):
        if not super().acquire():
            return self.failure()
        host = self.host + ':'
        if self.user:
            host = f'{self.user}@{host}'
        command = ['sshfs', host, '-p', self.port, self.local_path]
        for mo in self.mountopts:
            command.append('-o')
            command.append(mo)
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def release(self):
        if not super().release():
            return self.failure()
        command = ['fusermount', '-u', self.local_path]
        return subprocess.run(command, text=True, capture_output=True, check=False)

def ProviderFactory(name, config):
    action = config.find(name, 'action', '')
    if action == 'manual':
        return ManualProvider(name, config.find_section(name))
    if action == 'sshfs':
        return SshFsProvider(name, config.find_section(name))
    if action == 'mkdir':
        return DirectoryProvider(name, config.find_section(name))
    raise NotImplementedError(f"Provider for {action}")
