#!/usr/bin/python3

"""Read backup configuration"""

import argparse
import configparser
import errno
from pathlib import Path
import os
import sys

class Config:
    @classmethod
    def basedir(cls):
        return Path.home() / '.config' / 'backup'

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
                           'info': {'stripped_name': filename.with_suffix('').name}
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
            return self.configuration[section][key]
        return default

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Returns configuration parameters')
    parser.add_argument('--section', required=True, help='Configuration file section')
    parser.add_argument('--key', required=True, help='Configuration section key')
    parser.add_argument('--file', required=True, help='Which file to use')
    parser.add_argument('--default', required=False, default=None,
                        help='Return this string if no entry found')
    args = parser.parse_args()
    if args.section == '.' and args.key == '.' and args.default == '.':
        try:
            cobj = Config(args.file)
            sys.exit(0)
        except FileNotFoundError as fnfe:
            print(str(fnfe), file=sys.stderr)
            sys.exit(2)
    cobj = Config(args.file)
    data = cobj.find(args.section, args.key, args.default)
    if data is not None:
        print(data)
        sys.exit(0)
    else:
        sys.exit(1)
