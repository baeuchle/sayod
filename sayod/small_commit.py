#!/usr/bin/python3

"""Creates a small git commit"""

from datetime import datetime
import logging
from pathlib import Path

from .gitversion import Git
from .config import Config
from .notify import Notify

sclog = logging.getLogger(__name__)


def make_small_commit(gitobj, addables):
    for pattern in Config.get().find('git', 'add', '').split():
        path = gitobj.cwd / Path(pattern)
        sclog.info("Adding files from %s", path)
        addables.extend(path.parent.glob(path.name))
    for curr_file in addables:
        sclog.info("Adding %s", curr_file)
        gitobj.command('add', curr_file)
    if Config.get().find('git', 'add_all', False):
        sclog.info("Adding all tracked files")
        gitobj.command('add', '-u')

    if gitobj.there_are_untracked_files():
        msg = Config.get().find('git', 'small_message', 'small backup').format(datetime.now())
        sclog.info("Commiting %s", msg)
        gitobj.command('commit', '-qm', msg)

    Notify.get().success("Current commit is", gitobj.hash())


class SmallCommit:
    prog = 'smallcommit'

    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser(cls.prog, help="""Creates a small commit""")
        ap.add_argument('--add', '-a',
                        action='append',
                        required=False,
                        default=[]
                        )
        return ap

    @classmethod
    def standalone(cls, **kwargs):
        git = Git(Config.get().find('git', 'directory', Path.cwd()))
        make_small_commit(git, kwargs.get('add', []))
        return git.hash()
