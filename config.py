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

parser = argparse.ArgumentParser(description='Returns configuration parameters')
parser.add_argument('--section', required=True, help='Configuration file section')
parser.add_argument('--key', required=True, help='Configuration section key')
parser.add_argument('--file', required=True, help='Which file to use')
parser.add_argument('--emptydefault', required=False, default=False, action='store_true', help='Return empty string if no entry found')
parser.add_argument('--default', required=False, help='Return this string if no entry found')
parser.add_argument('--doesfileexist', required=False, default=False, action='store_true', help='Exit 0 if config file exists, 127 otherwise.')
args = parser.parse_args()

configuration = get_config(args.file)
if configuration is None:
    sys.exit(127)
if args.doesfileexist:
    sys.exit(0)
if configuration.has_option(args.section, args.key):
    print(configuration[args.section][args.key])
    sys.exit(0)
elif args.emptydefault:
    print("")
    sys.exit(0)
elif args.default is not None:
    print(args.default)
    sys.exit(0)
else:
    print("entry {}::{} not found".format(args.section, args.key), file=sys.stderr)
    sys.exit(1)
