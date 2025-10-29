"""
    Tasks for providing source and target(s).
"""

import logging
import os
from pathlib import Path
try:
    from PySide6.QtWidgets import QMessageBox, QApplication
    from PySide6.QtCore import QTimer
except ImportError:
    try:
        from PySide2.QtWidgets import QMessageBox, QApplication
        from PySide2.QtCore import QTimer
    except ImportError:
        QApplication = None
import select
import subprocess
import sys

from .arguments import Arguments
from .config import Config
from .tester import TesterFactory

plog = logging.getLogger(__name__)
all_providers = {}


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
        self.failed_acquire_loglevel = logging.ERROR
        self.failed_release_loglevel = logging.ERROR

    def __enter__(self):
        if self.goal.test():
            plog.info("No need to provide %s", self.name)
            return self
        aqresult = self.acquire()
        if aqresult and aqresult.returncode == 0:
            plog.info("Provided %s", self.name)
            self.provided = True
        else:
            plog.log(self.failed_acquire_loglevel,
                     "Acquiring %s failed. Exit %d stderr <%s>",
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
        rlresult = self.release(exc_type is not None)
        if rlresult.returncode == 0:
            self.provided = False
        else:
            plog.log(self.failed_release_loglevel,
                     "Releasing %s failed. Exit %d Output %s",
                     self.name, rlresult.returncode, rlresult.stderr)
        # is exc_type a ProvideError or a derivative of ProvideError?
        return not exc_type or ProvideError in exc_type.__mro__

    def acquire(self):
        plog.info("Acquiring %s", self.name)
        return self.success()

    def release(self, _):
        plog.info("Releasing %s", self.name)
        return self.success()

    @classmethod
    def success(cls):
        return subprocess.CompletedProcess(args=['true'], returncode=0, stdout="", stderr="")

    @classmethod
    def failure(cls, reason=""):
        return subprocess.CompletedProcess(args=['false'], returncode=1, stdout="", stderr=reason)


class SemaphoreProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.target = Path(config.get('file', '/tmp/semaphore'))
        self.if_exists = True
        self.execute_if_present = config.get('if_present', 'no') == 'yes'
        self.toggle_after_success = config.get('toggle', 'yes') == 'yes'
        # semaphore not present is not an error.
        self.failed_acquire_loglevel = logging.INFO

    def acquire(self):
        if not super().acquire():
            return self.failure()
        if self.execute_if_present and not self.target.exists():
            plog.info("Semaphore file doesn't exist, aborting")
            return self.failure()
        if not self.execute_if_present and self.target.exists():
            plog.info("Semaphore file already exists, aborting")
            return self.failure()
        return self.success()

    def release(self, is_exception):
        if not super().release(is_exception):
            return self.failure()
        if is_exception:
            return self.success()  # *this* release succeeded even if others didn't.
        # unlink if the target existed at the beginning:
        if self.execute_if_present and self.target.exists():
            self.target.unlink()
        # touch if the target didn't exist at the beginning:
        if not self.execute_if_present and not self.target.exists():
            self.target.touch()
        # it doesn't really matter if the file unexpectedly exists or unexpectedly doesn't exist
        # anymore, only then we don't have to worry about cleaning up.
        return self.success()


all_providers['semaphore'] = SemaphoreProvider


class SayodProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.command = config.pop('command', '')
        if not self.command:
            raise ProvideError(f'Cannot find ActionProvider {name}::command')
        self.command_klass = Arguments.combine_dict.get(self.command, False)
        if not self.command_klass:
            if self.command in Arguments.command_dict:
                raise ProvideError(f'Command {self.command} cannot be used as Action!')
            raise ProvideError(f'Command {self.command} not found!')
        plog.info("subcommand results in class %s", self.command_klass)
        self.run_before = config.get('before', 'yes') != 'no'

    def run(self):
        try:
            result = self.command_klass.standalone()
            return self.success() if result else self.failure()
        except Exception as e:  # pylint: disable=broad-exception-caught
            return self.failure(str(e))

    def acquire(self):
        if not self.run_before:
            return self.success()
        return self.run()

    def release(self, is_exception):
        if not super().release(is_exception):
            return self.failure()
        if is_exception:
            return self.failure("Not running because main task failed")
        if self.run_before:
            return self.success()
        return self.run()


all_providers['sayod'] = SayodProvider


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

    def release(self, is_exception):
        if not super().release(is_exception):
            return self.failure()
        try:
            self.dir.rmdir()
            return self.success()
        except OSError as oe:
            return self.failure(str(oe))


all_providers['mkdir'] = DirectoryProvider


class ManualProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.message = config.get('message', f'Bitte {name} bereitstellen')
        self.title = config.get('title', 'Manueller Eingriff erforderlich')
        self.timeout = float(config.get('timeout', 60))
        self.dialog_timed_out = False

    def acquire(self):
        if not super().acquire():
            return self.failure()
        if QApplication and os.environ.get('DISPLAY', False):
            return self.dialog_()
        return self.commandline_()

    def dialog_closer_(self, app):
        app.closeAllWindows()
        self.dialog_timed_out = True

    def dialog_(self):
        if not QApplication.instance():
            app = QApplication(['ManualProvider'])
        else:
            app = QApplication.instance()
        QTimer.singleShot(self.timeout * 1000, lambda: self.dialog_closer_(app))
        button = QMessageBox.question(None, self.title, self.message)
        if button == QMessageBox.Yes:
            plog.info("Manual dialog Yes")
            return self.success()
        if self.dialog_timed_out:
            plog.info("Manual dialog Timeout")
            return self.failure("Manual timeout")
        self.failed_acquire_loglevel = logging.INFO
        return self.failure("Manual abort")

    def commandline_(self):
        print(self.title)
        print(self.message + " [yes or ja to confirm]")
        i, _, _ = select.select([sys.stdin], [], [], self.timeout)
        if i:
            inp = sys.stdin.readline().strip().lower()
            if inp and inp[0] in 'yj':
                return self.success()
            # manual abort does not require error logging
            self.failed_acquire_loglevel = logging.INFO
            return self.failure("Manual abort")
        self.dialog_timed_out = True
        return self.failure("Timeout")


all_providers['manual'] = ManualProvider


class MountProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.local_path = config.get('local_path', '/home')

    def release(self, is_exception):
        if not super().release(is_exception):
            return self.failure()
        command = ['fusermount', '-u', self.local_path]
        return subprocess.run(command, text=True, capture_output=True, check=False)


class SshFsProvider(MountProvider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.user = config.get('user', '')
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('remote_port', '22')
        self.remote_path = config.get('remote_path', None)
        self.mountopts = config.get('mountopts', '').split()

    def acquire(self):
        if not super().acquire():
            return self.failure()
        host = self.host + ':'
        if self.remote_path:
            host = f'{host}{self.remote_path}'
        if self.user:
            host = f'{self.user}@{host}'
        command = ['sshfs', host, '-p', self.port, self.local_path]
        for mo in self.mountopts:
            command.append('-o')
            command.append(mo)
        return subprocess.run(command, text=True, capture_output=True, check=False)


all_providers['sshfs'] = SshFsProvider


class AdbProvider(Provider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.device = config.get('device', None)

    def acquire(self):
        command = ['adb', 'connect', self.device]
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def release(self, is_exception):
        if not super().release(is_exception):
            return self.failure()
        command = ['adb', 'disconnect', self.device]
        return subprocess.run(command, text=True, capture_output=True, check=False)


all_providers['adb'] = AdbProvider


class AdbFsProvider(MountProvider):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.mountopts = config.get('mountopts', '').split()
        self.device = config.get('device', None)

    def acquire(self):
        if not super().acquire():
            return self.failure()
        command = ['adbfs']
        for mo in self.mountopts:
            command.append('-o')
            command.append(mo)
        command.append(self.local_path)
        env_args = os.environ
        if self.device:
            env_args['ANDROID_SERIAL'] = self.device
        return subprocess.run(command, text=True, capture_output=True, check=False, env=env_args)


all_providers['adbfs'] = AdbFsProvider


def ProviderFactory(name):
    action = Config.get().find(name, 'action', '')
    section = Config.get().find_section(name)
    plog.debug("Creating provider for %s", action)
    cls = all_providers.get(action, None)
    if cls is None:
        raise NotImplementedError(f"Provider for {action}")
    return cls(name, section)
