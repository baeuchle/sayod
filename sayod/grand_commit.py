import datetime
import logging
from pathlib import Path

from .config import Config
from .gitversion import Git
from .notify import Notify

gclog = logging.getLogger(__name__)

class GrandCommit:
    @classmethod
    def add_subparser(cls, sp):
        return sp.add_parser('grandcommit',
            help="""Creates a grand commit

For a given git repository, this takes all changes since tag "stable" and packs them together into
one grand commit.

The purpose is to have a fine-grained short-term backup -- the small commit -- but only a coarser
long-term backup, provided by grand commit.

The grand commit is also mirrored.""")

    @classmethod
    def standalone(cls, **_):
        git = Git(Config.get().find('git', 'directory', Path.cwd()))

        tagname = Config.get().find('git', 'tagname', 'stable')
        if tagname + "\n" in git.commandlines('tag'):
            gclog.info("Resetting to tag %s", tagname)
            git.command('reset', '--soft', tagname)
            if git.there_are_untracked_files():
                msg = Config.get().find('git', 'grand_message', 'Grand backup').format(
                        datetime.datetime.now())
                gclog.info("Committing %s", msg)
                git.command('commit', '-qm', msg)
            else:
                gclog.info("No changes")
            git.command('tag', '-d', tagname)

        gclog.info("Creating new tag %s", tagname)
        git.command('tag', tagname)
        for orig in Config.get().find('git', 'origins', '').split():
            gclog.info('Pushing to origin %s', orig)
            git.command('push', '-q', orig, Config.get().find('git', 'branch', 'main'))

        Notify.get().success("Current commit is", git.hash())
        return git.hash()
