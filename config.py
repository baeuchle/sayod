#!/usr/bin/python3

import argparse
import configparser
import errno
from pathlib import Path
import os
import sys

class Config:
    def basedir():
        return Path.home() / '.config' / 'backup'
    
    def __init__(self, filename, **kwargs):
        if isinstance(filename, str):
            filename = Path(filename)
        if not filename.is_absolute():
            filename = Config.basedir() / filename
        ini_obj = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation()
        )
        rc_found = False
        variants = (
            str(filename),
            str(filename.with_suffix(".rc")),
            str(filename.with_suffix(".ini"))
        )
        ini_obj.read(variants)
        if 'defaults' in ini_obj:
            for tag, def_file in ini_obj['defaults'].items():
                path = Path(def_file)
                if def_file[0] != '/':
                    path = filename.parents[0] / def_file
                if len(ini_obj.read(str(path))) == 0:
                    raise FileNotFoundError(errno.ENOENT,
                        "defaults file {} not found".format(tag),
                        def_file)
        ini_obj.read(variants)
        if len(ini_obj.sections()) == 0:
            if kwargs.get("fail_on_missing_file", False):
                raise FileNotFoundError(errno.ENOENT, "Configuration file not found", str(filename))
            ini_obj = None
        self.configuration = ini_obj

    def find_entry(self, section, key, doesfileexist=False, default=None):
        if self.configuration is None:
            return 127, None
        if doesfileexist:
            return 0, None
        if self.configuration.has_option(section, key):
            return 0, self.configuration[section][key]
        if default is not None:
            return 0, default
        print("entry {}::{} not found".format(section, key), file=sys.stderr)
        return 1, None

    def find(self, section, key, default):
        result = self.find_entry(section, key, False, default)
        if result[0] != 0:
            raise Exception("{}::{} cannot be found in config: {}".format(section, key, str(result[0])))
        return result[1]

    def find_entry_args(self, args):
        if args.emptydefault:
            args.default = ""
        return self.find_entry(args.section, args.key, args.doesfileexist, args.default)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Returns configuration parameters')
    parser.add_argument('--section', required=True, help='Configuration file section')
    parser.add_argument('--key', required=True, help='Configuration section key')
    parser.add_argument('--file', required=True, help='Which file to use')
    parser.add_argument('--emptydefault', required=False, default=False, action='store_true', help='Return empty string if no entry found')
    parser.add_argument('--default', required=False, help='Return this string if no entry found')
    parser.add_argument('--doesfileexist', required=False, default=False, action='store_true', help='Exit 0 if config file exists, 127 otherwise.')
    args = parser.parse_args()
    cobj = Config(args.file)
    status, data = cobj.find_entry_args(args)
    if data is not None:
        print(data)
    sys.exit(status)
