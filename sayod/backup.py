import argparse
import logging

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

blog = logging.getLogger('sayod.exe')

def _backup():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    Log.add_options(parser)
    Config.add_options(parser)
    Notify.add_options(parser)
    sp = parser.add_subparsers(help="""This program gives an easy entry point to all backup scripts.
    Choose which one you want to use.""",
                               dest="subcommand")
    klasses = (Analyse, Copy, Config, Database, GrandCommit, Notify, LogReader, Receiver,
               RemoteReader, ReplaceGit, SmallCommit, Squasher, ZippedGit)
    subparsers = [klass.add_subparser(sp) for klass in klasses]
    args = parser.parse_args()

    Config.init(**args.__dict__)
    Log.init(**args.__dict__, name=Config.get().find('info', 'stripped_name', None))
    Notify.init(**args.__dict__)

    blog.info("Executing sayod-backup (v%s) with %s", __version__, args.subcommand)
    for klass, subp in zip(klasses, subparsers):
        if f'{parser.prog} {args.subcommand}' == subp.prog:
            result = klass.standalone(**args.__dict__)
            if getattr(klass, 'print_result', False) and result:
                if isinstance(result, list):
                    result = '\n'.join([str(x) for x in result])
                blog.info("Result: %s", result)
                print(result)
            if getattr(klass, 'fail_empty_result', False) and not result:
                blog.error("Program failed; no output")
                raise SystemExit(1)
            blog.info("Program succeeded")
            raise SystemExit(0)
    blog.error("Unkown subcommand in %s", str(args))

def backup():
    try:
        _backup()
    except Exception:
        blog.exception("Program failed hard")
