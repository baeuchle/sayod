"""provide cmd line option and retrieval for a python logger"""

import logging
import argparse

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

def get_logger(name, level=None):
    if level is not None:
        numeric_level = getattr(logging, level.log_level)
        if level.log_verbosity:
            numeric_level -= 10
        return get_logger(name, numeric_level)
    return logging.getLogger(name)
