import datetime
import logging

from .config import Config
from .gitversion import Git
from .notify import Notify

rglog = logging.getLogger(__name__)

class ReplaceGit:
    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser('replace-git',
                           help='''Replaces all files inside a git repository with the current
                           working directory's content and creates a new commit'''
                          )
        ap.add_argument('--directory', required=False)

    @classmethod
    def standalone(cls, args):
        git = Git(Config.get().find('target', 'path', args.directory))
        rglog.debug('running in %s', args.directory)
        git.command('add', '.')
        git.command('commit', '-m', f'BACKUP {datetime.datetime.now()}')
        Notify.get().success("New commit created")
