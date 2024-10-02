"""provide cmd line option and retrieval for a python logger"""

import argparse
import logging
from pathlib import Path
try:
    from systemd.journal import JournalHandler
except ImportError:
    pass

def add_options(ap, **kwargs):
    default_level = kwargs.get('default_loglevel', 'WARNING')
    group = ap.add_argument_group('Logging')
    meg = group.add_mutually_exclusive_group(required=False)
    meg.add_argument('--log-level',
                        action='store',
                        dest='log_level',
                        default=default_level,
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        help='Sets the logging level',
                        required=False
                       )

def add_handler_if_new(logger, hClass, *args, **kwargs):
    for h in logger.handlers:
        if isinstance(h, hClass):
            return h
    new_handler = hClass(*args, **kwargs)
    logger.addHandler(new_handler)
    return new_handler

def get_logger(name, level=None):
    root_log = logging.getLogger('backup')
    root_log.setLevel(logging.DEBUG)
    sh = add_handler_if_new(root_log, logging.StreamHandler)
    jh = add_handler_if_new(root_log, JournalHandler, SYSLOG_IDENTIFIER='backup')
    if level is not None:
        if isinstance(level, int):
            numeric_level = level
        else:
            numeric_level = getattr(logging, level.log_level)
        sh.setLevel(numeric_level)
    jf = logging.Formatter('%(name)s: %(message)s')
    jh.setFormatter(jf)
    return logging.getLogger('backup.' + name)
