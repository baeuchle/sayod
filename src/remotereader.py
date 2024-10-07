#!/usr/bin/python3

"""Reads request for log find task from STDIN and prints the lines that
were found"""

import datetime
import logging
from subprocess import Popen, PIPE

from notify import Notify, oneline

lrlog = logging.getLogger('backup.remotereader')

LAST = "last"

def remote(subject, command):
    results = []
    ssh = Notify.get().ssh
    lrlog.info("Connecting to ssh -> logreader")
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
            Notify.get().notify_local(f"Kann entferntes Log nicht lesen:\n{oneline(err)}",
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

class RemoteReader:
    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser('remotereader', help='read data from remote log')
        ap.add_argument('--subject', required=True)
        ap.add_argument('--command', required=True)

    @classmethod
    def standalone(cls, args):
        return remote(args.subject, args.command)
