#!/usr/bin/python3

"""Read backup configuration"""

import argparse
import configparser
import errno
from pathlib import Path
import os

import log

clog = log.get_logger('config')

class Config:
    @classmethod
    def basedir(cls):
        return Path.home() / '.config' / 'backup'

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
    def get_config(cls, config_file, **kwargs):
        if isinstance(config_file, argparse.Namespace):
            return cls.get_config(config_file.configuration_file, **kwargs)
        try:
            return Config(config_file)
        except FileNotFoundError as fnfe:
            clog.critical("%s %s", fnfe.strerror, fnfe.filename)
            raise SystemExit(kwargs.get('failure_exit', 1))

    def __init__(self, filename):
        if isinstance(filename, str):
            filename = Path(filename)
        if not filename.is_absolute():
            filename = Config.basedir() / filename
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
                        "defaults file {} not found".format(tag),
                        def_file)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Returns configuration parameters')
    parser.add_argument('--section', required=True, help='Configuration file section')
    parser.add_argument('--key', required=True, help='Configuration section key')
    parser.add_argument('--default', required=False, default=None,
                        help='Return this string if no entry found')
    Config.add_options(parser)
    log.add_options(parser)
    args = parser.parse_args()

    clog = log.get_logger('config', args)
    if args.section == '.' and args.key == '.':
        cobj = Config.get_config(args, failure_exit=2)
        raise SystemExit(0)
    cobj = Config.get_config(args)
    data = cobj.find(args.section, args.key, args.default)
    if data is not None:
        print(data)
        raise SystemExit(0)
    else:
        raise SystemExit(1)
