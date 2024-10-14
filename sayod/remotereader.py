"""Reads request for log find task from STDIN and prints the lines that
were found"""

import logging
from subprocess import Popen, PIPE

from .notify import Notify, oneline
from .plain_log import PlainLog
from .taggedentry import TaggedEntry

lrlog = logging.getLogger(__name__)

def remote(subjects, action):
    results = []
    ssh = Notify.get().ssh
    lrlog.info("Connecting to ssh -> logreader for %s on %s", action, subjects)
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
        # first, choose the configuration file:
        proc.stdin.write(ssh['remote'] + "\n")
        # then, tell the remote which part of the log to look at
        # (DEADTIME etc.):
        for s in subjects:
            proc.stdin.write(s + "\n")
        proc.stdin.write("\n")
        # finally, what about this subject do we want to know?
        # count/last/first/list
        proc.stdin.write(action)
        proc.stdin.close()
        returncode = proc.wait()
        err = proc.stderr.read()
        if returncode != 0:
            Notify.get().notify_local(f"Kann entferntes Log nicht lesen:\n{oneline(err)}",
                head='Backup-Fehler {}')
            raise RuntimeError(err)
        for line in proc.stdout.readlines():
            if line.strip():
                results.append(TaggedEntry(line))
    if not results:
        raise ValueError("No results received")
    if action == PlainLog.FIRST:
        return results[0]
    if action == PlainLog.LAST:
        return results[-1]
    if action == PlainLog.COUNT:
        return len(results)
    return results

class RemoteReader:
    print_result = True
    fail_empty_result = True

    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser('remotereader', help='read data from remote log')
        PlainLog.add_options(ap)
        return ap

    @classmethod
    def standalone(cls, **kwargs):
        return remote(kwargs.get('subject', []), kwargs.get('action', 'list'))
