import argparse

from .analyse import Analyse
from .copy import Copy
from .config import Config
from .database import Database
from .grand_commit import GrandCommit
from .log import Log
from .notify import Notify
from .logreader import LogReader
from .receiver import Receiver
from .remotereader import RemoteReader
from .replacegit import ReplaceGit
from .small_commit import SmallCommit
from .squasher import Squasher
from .zippedgit import ZippedGit
from .version import __version__

class SayodCommandNotFound(ValueError):
    pass

class Arguments:
    _klasses = (Analyse, Copy, Config, Database, GrandCommit, Notify, LogReader, Receiver,
                RemoteReader, ReplaceGit, SmallCommit, Squasher, ZippedGit)
    # classes whose standalone can only be called directly:
    _single_klasses = (Config, Notify, LogReader, Receiver, RemoteReader, Squasher)
    # classes whose standalone can be called as context action:
    _combine_klasses = (Analyse, Copy, Database, GrandCommit, ReplaceGit, SmallCommit, ZippedGit)

    command_dict = {}
    combine_dict = {}

    @classmethod
    def add_context_options(cls, parser):
        # putting this here so we don't have to import Context
        parser.add_argument('--force', '-f',
                            default=False,
                            action='store_true',
                            required=False,
                            help="Ignore deadtime and force action",
                            dest="context_force")

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
        Log.add_options(self.parser)
        Config.add_options(self.parser)
        Notify.add_options(self.parser)
        self.add_context_options(self.parser)
        sp = self.parser.add_subparsers(help="""Different sayod tasks are available:""",
                                   dest="subcommand")
        for klass in Arguments._single_klasses:
            klass.add_subparser(sp)
            Arguments.command_dict[klass.prog] = klass
        for klass in Arguments._combine_klasses:
            klass.add_subparser(sp)
            Arguments.command_dict[klass.prog] = klass
            Arguments.combine_dict[klass.prog] = klass
        self.args = None

    def get_arguments(self):
        if not self.args:
            self.args = self.parser.parse_args()
        return self.args.__dict__
