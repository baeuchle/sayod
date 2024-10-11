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

def backup():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    Log.add_options(parser)
    Config.add_options(parser)
    Notify.add_options(parser)
    sp = parser.add_subparsers(help="""This program gives an easy entry point to all backup scripts.
    Choose which one you want to use.""",
                               dest="subcommand")
    Analyse.add_subparser(sp)
    Copy.add_subparser(sp)
    Config.add_subparser(sp)
    Database.add_subparser(sp)
    GrandCommit.add_subparser(sp)
    Notify.add_subparser(sp)
    LogReader.add_subparser(sp)
    Receiver.add_subparser(sp)
    RemoteReader.add_subparser(sp)
    ReplaceGit.add_subparser(sp)
    SmallCommit.add_subparser(sp)
    Squasher.add_subparser(sp)
    ZippedGit.add_subparser(sp)
    args = parser.parse_args()

    Config.init_args(args)
    Log.init(args, Config.get().find('info', 'stripped_name', None))
    Notify.init(show=args.notification_show)

    blog.info("Executing sayod-backup (v%s) with %s", __version__, args.subcommand)
    if args.subcommand == "analyse":
        Analyse.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "copy":
        Copy.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "config":
        data = Config.standalone(args)
        if data is not None:
            print(data)
            raise SystemExit(0)
        raise SystemExit(1)
    if args.subcommand == "database":
        Database.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "grandcommit":
        GrandCommit.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "notify":
        Notify.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "logreader":
        data = LogReader.standalone(args)
        print(data)
        raise SystemExit(0)
    if args.subcommand == "receive":
        Receiver.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "remotereader":
        data = RemoteReader.standalone(args)
        if data is not None:
            print(data)
            raise SystemExit(0)
        raise SystemExit(1)
    if args.subcommand == "replace-git":
        ReplaceGit.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "smallcommit":
        SmallCommit.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "squasher":
        Squasher.standalone(args)
        raise SystemExit(0)
    if args.subcommand == "zipped-git":
        ZippedGit.standalone(args)
        raise SystemExit(0)
    print(args)
