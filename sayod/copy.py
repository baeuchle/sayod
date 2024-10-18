import logging

from .config import Config
from .notify import Notify
from .rsync import RSync

clog = logging.getLogger(__name__)

def find_sources():
    source = Config.get().find('source', 'path', None)
    if source:
        return [source]
    source_list = Config.get().find('source', 'list', None)
    if not source_list:
        Notify.get().fatal(
                'Kann Quellpfad nicht bestimmen (sollte in source::path oder source::list stehen)')
        clog.critical('source::path or source::list should be present')
        raise SystemExit(127)
    try:
        sls = Config.get().find_section(source_list)
    except KeyError as ke:
        Notify.get().fatal(f'Kann Quellenliste nicht finden ({source_list}::*)')
        clog.critical('[%s] should be present in configuration', source_list)
        raise SystemExit(127) from ke
    return list(sls.values())

def do_copy():
    Notify.get().start("Starte Backup")
    sources = find_sources()
    target = Config.get().find('target', 'path', None)
    if not target:
        Notify.get().fatal('Kann Zielpfad nicht bestimmen (sollte in target::path stehen')
        raise SystemExit(127)

    exclude_file = Config.get().find('source', 'exclude_file', None)
    if exclude_file:
        clog.warning("Exclude file should be defined in [rsync]")
        Config.get().find_section('rsync')['exclude_file'] = exclude_file
    clog.info("Sources %s", '; '.join(sources))
    clog.info("Target %s", target)

    rsync = RSync()
    rsync.run(sources=sources, target=target)
    rsync.wrapup()

class Copy:
    prog = 'copy'

    @classmethod
    def add_subparser(cls, sp):
        return sp.add_parser(cls.prog,
            help="Creates Backups by rsync'ing and notifies about the success of failure thereof."
        )

    @classmethod
    def standalone(cls, **_):
        do_copy()
