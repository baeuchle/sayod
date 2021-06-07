import logging
import argparse

def add_options(ap, **kwargs):
    default_level = kwargs.get('default_loglevel', 'WARNING')
    group = ap.add_argument_group('Logging')
    meg = group.add_mutually_exclusive_group(required=False)
    meg.add_argument('--verbosity', '-v',
                        action='store_true',
                        dest='log_verbosity',
                        default=False,
                        help='Sets loglevel to one step more than {}'.format(default_level),
                        required=False
                       )
    meg.add_argument('--log-level',
                        action='store',
                        dest='log_level',
                        default=default_level,
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        help='Sets the logging level',
                        required=False
                       )

def getLogger(name, level):
    if isinstance(level, argparse.Namespace):
        numeric_level = getattr(logging, level.log_level)
        if level.log_verbosity:
            numeric_level -= 10
        return getLogger(name, numeric_level)
    logging.basicConfig(
        level=level,
        style='{'
    )
    return logging.getLogger(name)
