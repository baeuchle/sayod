from context import Context
import deadtime
from rsync import RSync
import log

clog = log.get_logger('copy')

def find_sources(config, notify):
    source = config.find('source', 'path', None)
    if source:
        return [source]
    source_list = config.find('source', 'list', None)
    if not source_list:
        notify.fatal('Kann Quellpfad nicht bestimmen (sollte in source::path oder source::list stehen)')
        clog.critical('source::path or source::list should be present')
        raise SystemExit(127)
    try:
        sls = config.find_section(source_list)
    except KeyError as ke:
        notify.fatal(f'Kann Quellenliste nicht finden ({source_list}::*)')
        clog.critical('[%s] should be present in configuration', source_list)
        raise SystemExit(127) from ke
    return [path for path in sls.values()]

def do_copy(config, notify, **kwargs):
    if not deadtime.test_deadtime(kwargs.get('force', False), config, notify):
        raise SystemExit(0)
    notify.start("Starte Backup")
    sources = find_sources(config, notify)
    target = config.find('target', 'path', None)
    if not target:
        notify.fatal('Kann Zielpfad nicht bestimmen (sollte in target::path stehen')
        raise SystemExit(127)
    
    exclude_file = config.find('source', 'exclude_file', None)
    if exclude_file:
        clog.warning("Exclude file should be defined in [rsync]")
        config.find_section('rsync')['exclude_file'] = exclude_file
    clog.info("Sources %s", '; '.join(sources))
    clog.info("Target %s", target)
    
    rsync = RSync(config)
    with Context(config, config.find('rsync', 'providers', '').split()) as pc:
        rsync.run(sources=sources, target=target)
    rsync.wrapup(notify)
