"""Read backup configuration"""

import configparser
import errno
import logging
import os
from pathlib import Path

clog = logging.getLogger('backup.config')

class _Config:
    @classmethod
    def basedir(cls):
        return Path.home() / '.config' / 'backup'

    def __init__(self, filename):
        if isinstance(filename, str):
            filename = Path(filename)
        if not filename.is_absolute():
            filename = _Config.basedir() / filename
        ini_obj = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation()
        )
        variants = (
            str(filename),
            str(filename.with_suffix('')),
            str(filename.with_suffix(".rc")),
            str(filename.with_suffix(".ini"))
        )
        ini_obj.read(variants)
        if len(ini_obj.sections()) == 0:
            raise FileNotFoundError(errno.ENOENT, "Configuration file not found", str(filename))
        # add environment variables to [env]; this allows to use them in
        # interpolation directives.
        ini_obj.read_dict({'env': os.environ,
                           'info': {'stripped_name': filename.stem}
                          })
        # if there is a section [defaults], then use each value as a
        # file to be loaded:
        if 'defaults' in ini_obj:
            for tag, def_file in ini_obj['defaults'].items():
                path = Path(def_file)
                if def_file[0] != '/':
                    path = filename.parents[0] / def_file
                if len(ini_obj.read(str(path))) == 0:
                    raise FileNotFoundError(errno.ENOENT,
                        f"defaults file {tag} not found", def_file)
        # re-read original file to override defaults:
        ini_obj.read(variants)
        self.configuration = ini_obj

    @property
    def friendly(self):
        return self.find('info', 'friendly_name',
                    self.find('info', 'stripped_name',
                        'UNKNOWN BACKUP JOB'))

    def timeout(self, subject, default):
        return int(self.find('timeout', subject, default))

    def find(self, section, key, default):
        if self.configuration.has_option(section, key):
            # logging what has been found may leak passwords.
            return self.configuration[section][key]
        clog.debug("Option %s::%s not found", section, key)
        return default

    def find_section(self, section):
        return self.configuration[section]

class Config:
    _instance = None

    @classmethod
    def add_options(cls, ap, **kwargs):
        group = ap.add_argument_group('Configuration')
        optname = kwargs.get('optname', 'config')
        group.add_argument('--' + optname,
                            action='store',
                            dest='configuration_file',
                            help='name of the configuration file',
                            required=True)

    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser('config', help='directly read values from configuration')
        ap.add_argument('--section', required=True, help='Configuration file section')
        ap.add_argument('--key', required=True, help='Configuration section key')
        ap.add_argument('--default', required=False, default=None,
                        help='Return this string if no entry found')

    @classmethod
    def init_file(cls, path):
        cls._instance = _Config(path)

    @classmethod
    def init_args(cls, args):
        cls.init_file(args.configuration_file)

    @classmethod
    def get(cls):
        return cls._instance

    @classmethod
    def standalone(cls, args):
        return cls.get().find(args.section, args.key, args.default)
