#!/usr/bin/python3

"""Reads request for log find task from STDIN and prints the lines that
were found"""

import argparse
import datetime
from subprocess import Popen, PIPE

from config import Config
import log
from notify import oneline, Notify

lrlog = log.get_logger('logreader')

LAST = "last"

def remote(config, notify, subject, command):
    results = []
    ssh = notify.ssh
    with Popen(['ssh',
        '-l', ssh['user'],
              ssh['host'],
        '-p', ssh['port'],
        'logreader'
        ],
        text=True,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE) as proc:
        proc.stdin.write('content-type: text/x-plain-ask\n')
        proc.stdin.write(ssh['remote'] + "\n")
        proc.stdin.write(subject + "\n\n")
        proc.stdin.write(command)
        proc.stdin.close()
        returncode = proc.wait()
        err = proc.stderr.read()
        if returncode != 0:
            notify.notify_local(f"Kann entferntes Log nicht lesen:\n{oneline(err)}",
                head='Backup-Fehler {}')
            return 0
        for line in proc.stdout.readlines():
            results.append(line.split()[0])
    try:
        if command == LAST:
            return datetime.datetime.fromisoformat(results[-1])
    except ValueError:
        pass
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Show and send a notification""")
    Config.add_options(parser)
    log.add_options(parser)
    parser.add_argument('--no-notify', '-N', required=False, default=False, action='store_true')
    parser.add_argument('--subject', required=True)
    parser.add_argument('--command', required=True)
    args = parser.parse_args()
    lrlog = log.get_logger('logreader', args)
    config_ = Config(args.configuration_file)
    notify_ = Notify(config_, show=not args.no_notify)
    print(remote(config_, notify_, args.subject, args.command))
