#!/usr/bin/python3

"""Read backup configuration"""

import argparse
import configparser
import errno
from pathlib import Path
import os
import sys

import log

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
    def get_config(cls, config_file, log, **kwargs):
        if isinstance(config_file, argparse.Namespace):
            return cls.get_config(config_file.configuration_file, log, **kwargs)
        try:
            return Config(config_file)
        except FileNotFoundError as fnfe:
            log.critical("%s %s", fnfe.strerror, fnfe.filename)
            sys.exit(kwargs.get('failure_exit', 1))

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

    def find(self, section, key, default):
        if self.configuration.has_option(section, key):
            log.debug("Found option %s::%s = %s" % (section, key, self.configuration[section][key]))
            return self.configuration[section][key]
        log.debug("Option %s::%s not found" % (section, key))
        return default

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Returns configuration parameters')
    parser.add_argument('--section', required=True, help='Configuration file section')
    parser.add_argument('--key', required=True, help='Configuration section key')
    parser.add_argument('--default', required=False, default=None,
                        help='Return this string if no entry found')
    Config.add_options(parser)
    log.add_options(parser)
    args = parser.parse_args()

    log = log.getLogger('config', args)
    if args.section == '.' and args.key == '.':
        cobj = Config.get_config(args, log, failure_exit=2)
        sys.exit(0)
    cobj = Config.get_config(args, log)
    data = cobj.find(args.section, args.key, args.default)
    if data is not None:
        print(data)
        sys.exit(0)
    else:
        sys.exit(1)
