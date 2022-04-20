"""
    Tests prerequisites for backups (mounted disks, present directories)
"""

from pathlib import Path
import log

tlog = log.get_logger('pyb.tester')

# pylint: disable=too-few-public-methods

class Tester:
    """Tests if something exists already"""
    def __init__(self, command):
        self.command = command

    def test(self):
        tlog.info("testing %s", self.command)
        return True

    def default_postrequisite(self):
        return self

class NoneTester(Tester):
    def __init__(self):
        super().__init__("<None>")

class AlwaysTester(Tester):
    def __init__(self):
        super().__init__("<Always>")

    def test(self):
        return False

    def default_postrequisite(self):
        return NoneTester()

class MountpointTester(Tester):
    def __init__(self, path):
        super().__init__("mountpoint")
        self.path = Path(path)

    def test(self):
        tlog.info("testing mountpoint of %s", str(self.path))
        return self.path.is_mount()

class DirectoryTester(Tester):
    def __init__(self, path):
        super().__init__("directory")
        self.path = Path(path)

    def test(self):
        tlog.info("testing is %s a directory", str(self.path))
        return self.path.is_dir()

def TesterFactory(command):
    words = command.split()
    if not words or words[0].lower() == "none":
        return NoneTester()
    if words[0].lower() == 'always':
        return AlwaysTester()
    if words[0] == 'mountpoint':
        return MountpointTester(' '.join(words[1:]))
    if words[0] == 'is_dir':
        return DirectoryTester(' '.join(words[1:]))
    raise NotImplementedError(f"Tester class {words[0]} not implemented")
