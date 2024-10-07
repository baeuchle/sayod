"""provide cmd line option and retrieval for a python logger"""

import logging
from systemd.journal import JournalHandler

root_log = logging.getLogger('backup')

class Log:
    @classmethod
    def add_options(cls, ap, **kwargs):
        default_level = kwargs.get('default_loglevel', 'WARNING')
        group = ap.add_argument_group('Logging')
        group.add_argument('--log-level',
                            action='store',
                            dest='log_level',
                            default=default_level,
                            choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                            help='Sets the logging level',
                            required=False
                           )
        cls.init_root()

    @classmethod
    def init_root(cls):
        root_log.setLevel(logging.DEBUG)
        jh = JournalHandler(SYSLOG_IDENTIFIER='backup')
        jf = logging.Formatter('%(name)s: %(message)s')
        jh.setFormatter(jf)
        root_log.addHandler(jh)

    @classmethod
    def init(cls, args):
        sh = logging.StreamHandler()
        sh.setLevel(args.log_level)
        root_log.addHandler(sh)
