#!/usr/bin/python3

import argparse
import configparser
import os
import sys

CLIENT_CONFIG = 'rc.ini'
SERVER_CONFIG = 'analyse.rc'

def default_config():
    ini_obj = configparser.ConfigParser()
    ini_obj['notify'] = {}
    ini_obj['notify']['log'] = 'ssh frankfurtium.de cat >> backup_status'
    ini_obj['notify']['pipe'] = 'yes'
    ini_obj['target'] = {}
    ini_obj['target']['path'] = "{}/.backup/data/".format(os.environ['HOME'])
    ini_obj['target']['provide'] = ""
    ini_obj['source'] = {}
    ini_obj['source']['path'] = os.environ['HOME']
    ini_obj['source']['exclude_file'] = '{}/.config/backup/exclude'.format(os.environ['HOME'])
    return ini_obj

def default_server_config():
    ini_obj = configparser.ConfigParser()
    ini_obj['status'] = {}
    ini_obj['status']['file'] = 'backup_status'
    ini_obj['status']['stale_errors'] = '1'
    ini_obj['status']['warn_missing'] = '7' # warn if seven days fail
    ini_obj['mail'] = {} # the notification channel
    ini_obj['mail']['cmd'] = 'echo'
    ini_obj['mail']['subject'] = 'Backup-Script Report'
    ini_obj['mail']['email'] = '{}@localhost'.format(os.environ['USER'])
    ini_obj['mail']['sign'] = 'no'
    ini_obj['mail']['opening'] = 'Lieber Backup-Benutzer!'
    ini_obj['mail']['closing'] = 'Grüße vom Backup-Analyse-Script'
    return ini_obj

def get_config(config_dir, config_file):
    config_path = "{}/{}".format(config_dir, config_file)
    ini_obj = configparser.ConfigParser()
    if not os.path.exists(config_path):
        if not os.path.exists(config_dir):
            print("Creating configuration directory", config_dir, file=sys.stderr)
            os.mkdir(config_dir)
        print("Creating configuration file", config_path, file=sys.stderr)
        with open(config_path, "w") as c_file:
            if config_file == SERVER_CONFIG:
                default_server_config().write(c_file)
            else:
                default_config().write(c_file)
    ini_obj.read(config_path)
    return ini_obj

parser = argparse.ArgumentParser(description='Returns configuration parameters')
parser.add_argument('--path', required=True, help='Configuration directory')
parser.add_argument('--section', required=True, help='Configuration file section')
parser.add_argument('--key', required=True, help='Configuration section key')
parser.add_argument('--file', required=False, default=CLIENT_CONFIG, help='Which file to use')
parser.add_argument('--no-default', required=False, default=False, action='store_true', help='Return default if value is not found')
args = parser.parse_args()

configuration = get_config(args.path, args.file)
if configuration.has_option(args.section, args.key):
    print(configuration[args.section][args.key])
    sys.exit(0)
else:
    print("entry {}::{} not found".format(args.section, args.key), file=sys.stderr)
    sys.exit(1)
