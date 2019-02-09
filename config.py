#!/usr/bin/python3

import argparse
import configparser
import os
import sys

def default_config():
    ini_obj = configparser.ConfigParser()
    ini_obj['notify'] = {}
    ini_obj['notify']['remote_0'] = 'ssh frankfurtium.de cat >> backup_status'
    ini_obj['notify']['remote_1'] = 'ssh frankfurtium.de cat >> backup_status'
    ini_obj['notify']['remote_2'] = 'ssh frankfurtium.de cat >> backup_status'
    ini_obj['notify']['local_0'] = 'notify-send -u critical '
    ini_obj['notify']['local_1'] = 'notify-send -u normal '
    ini_obj['notify']['local_2'] = 'notify-send -u low '
    ini_obj['target'] = {}
    ini_obj['target']['path'] = "{}/.backup/data/".format(os.environ['HOME'])
    ini_obj['target']['provide'] = ""
    ini_obj['source'] = {}
    ini_obj['source']['path'] = os.environ['HOME']
    ini_obj['source']['exclude_file'] = '../backup/exclude'
    return ini_obj

def get_config(config_dir):
    config_file = "{}/rc.ini".format(config_dir)
    ini_obj = configparser.ConfigParser()
    if not os.path.exists(config_file):
        if not os.path.exists(config_dir):
            print("Creating configuration directory", config_dir, file=sys.stderr)
            os.mkdir(config_dir)
        print("Creating configuration file", config_file, file=sys.stderr)
        with open(config_file, "w") as c_file:
            default_config().write(c_file)
    ini_obj.read(config_file)
    return ini_obj

parser = argparse.ArgumentParser(description='Returns configuration parameters')
parser.add_argument('--path', required=True, help='Configuration directory')
parser.add_argument('--section', required=True, help='Configuration file section')
parser.add_argument('--key', required=True, help='Configuration section key')
args = parser.parse_args()

configuration = get_config(args.path)
if configuration.has_option(args.section, args.key):
    print(configuration[args.section][args.key])
    sys.exit(0)
else:
    print("entry {}::{} not found".format(args.section, args.key), file=sys.stderr)
    sys.exit(1)
