#!/usr/bin/python3

import argparse
import configparser
import os
import sys

def get_config(config_file):
    ini_obj = configparser.ConfigParser()
    if not os.path.exists(config_file):
        return None
    ini_obj.read(config_file)
    return ini_obj

def find_entry(filename, section, key, doesfileexist=False, default=None):
    configuration = get_config(filename)
    if configuration is None:
        return 127, None
    if doesfileexist:
        return 0, None
    if configuration.has_option(section, key):
        return 0, configuration[section][key]
    if default is not None:
        return 0, default
    print("entry {}::{} not found".format(section, key), file=sys.stderr)
    return 1, None

def find_entry_args(args):
    if args.emptydefault:
        args.default = ""
    return find_entry(args.file, args.section, args.key, args.doesfileexist, args.default)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Returns configuration parameters')
    parser.add_argument('--section', required=True, help='Configuration file section')
    parser.add_argument('--key', required=True, help='Configuration section key')
    parser.add_argument('--file', required=True, help='Which file to use')
    parser.add_argument('--emptydefault', required=False, default=False, action='store_true', help='Return empty string if no entry found')
    parser.add_argument('--default', required=False, help='Return this string if no entry found')
    parser.add_argument('--doesfileexist', required=False, default=False, action='store_true', help='Exit 0 if config file exists, 127 otherwise.')
    args = parser.parse_args()
    status, data = find_entry_args(args)
    if data is not None:
        print(data)
    sys.exit(status)
