#!/usr/bin/python3

import argparse
import configparser
from pathlib import Path
import os
import sys

class Config:
    def basedir():
        return Path.home() / '.config' / 'backup'
    
    def __init__(self, filename):
        if isinstance(filename, str):
            filename = Path(filename)
        if not filename.is_absolute():
            filename = Config.basedir() / filename
        ini_obj = configparser.ConfigParser()
        if not filename.exists():
            ini_obj = None
        else:
            ini_obj.read(str(filename))
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
            raise Exception("Bad config")
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
