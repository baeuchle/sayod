#!/usr/bin/python3

"""Wrapper around notify-send, because libnotify can't be bothered to do
sensible stuff"""

import argparse
import os
from subprocess import run, Popen, PIPE, DEVNULL
import sys
import textwrap

from config import Config
import log
nlog = log.get_logger('notify')

def oneline(text):
    return text.replace('\n', '')

class Notify:
    @classmethod
    def add_options(cls, ap):
        group = ap.add_argument_group('Notification')
        group.add_argument('--no-notify',
                            action='store_true',
                            dest='notification_dontshow',
                            help="Don't show notification on screen",
                            required=False)

    def __init__(self, config, **kwargs):
        self.show = kwargs.get('show', False)
        self.config = config
        self.friendly = self.config.find('info', 'friendly_name',
                             self.config.find('info', 'stripped_name',
                                'UNKNOWN'))
        self.env = os.environ
        if self.show:
            wns = run(['which', 'notify-send'], check=False, stdout=DEVNULL, stderr=DEVNULL)
            if wns.returncode != 0:
                nlog.critical('Kann notify-send nicht finden, bitte installieren')
                sys.exit(127)
            if not 'XDG_RUNTIME_DIR' in self.env:
                self.env['XDG_RUNTIME_DIR'] = '/run/user/{}'.format(os.getuid())
        self.ssh = {
            'host': self.config.find('notify', 'host', 'localhost'),
            'user': self.config.find('notify', 'user', self.env['LOGNAME']),
            'port': self.config.find('notify', 'port', 22),
            'pipe': self.config.find('notify', 'pipe', False),
            'remote': self.config.find('notify', 'remotekey',
                self.config.find('info', 'stripped_name',
                    self.config.friendly))
        }
        if self.ssh['pipe'] in ('no', 'nein', 'false'):
            self.ssh['pipe'] = False

    def notify_local(self, long_msg, **kwargs):
        msg = textwrap.fill(long_msg, width=72)[0:131071]
        head = kwargs.get('head', "NOTIFICATION").format(self.config.friendly)
        if self.show:
            run(['notify-send',
                 '-u', kwargs.get('urgency', 'low'),
                 '-t', str(kwargs.get('timeout', 10*1000)),
                 head, msg],
                env=self.env,
                check=False,
                stdout=DEVNULL,
                stderr=DEVNULL)
        nlog.info('NOTIFY-SEND %s', head)
        nlog.info(long_msg)

    def notify(self, *msg_args, **kwargs):
        msg = " ".join(msg_args)
        self.notify_local(msg, **kwargs)
        if self.ssh['pipe']:
            nlog.debug("sshing()")
            returncode = False
            with Popen(['ssh',
                '-l', self.ssh['user'],
                      self.ssh['host'],
                '-p', self.ssh['port'],
                'receiver'
                ],
                text=True,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE) as proc:
                proc.stdin.write('content-type: text/x-plain-log\n')
                proc.stdin.write(self.ssh['remote'] + "\n")
                proc.stdin.write(kwargs.get('subject', '') + "\n")
                proc.stdin.write(msg)
                proc.stdin.close()
                returncode = proc.wait()
                errs = proc.stderr.read()
            if returncode != 0:
                self.notify_local(
                     'Kann Meldungen nicht auf dem Server schreiben:\n'
                     + oneline(errs),
                     head='Backup-Fehler {}',
                     urgency='critical',
                     timeout=self.config.timeout('fatal', 60*60*1000)
                     )
        else:
            nlog.info('content-type: text/x-plain-log')
            nlog.info(self.ssh['remote'])
            nlog.info(kwargs.get('subject', ''))
            nlog.info(msg)

    def success(self, *args):
        self.notify(*args,
            subject='SUCCESS',
            urgency='low',
            head='Backup {}: Erfolg',
            timeout=self.config.timeout('success', 4*1000)
            )

    def fatal(self, *args):
        self.notify(*args,
            subject='WTF!',
            urgency='critical',
            head='Backup-Fehler (Fatal): {}',
            timeout=self.config.timeout('fatal', 60*60*1000)
            )

    def start(self, *args):
        self.notify(*args,
            subject='START',
            urgency='low',
            head='Starte Backup {}',
            timeout=self.config.timeout('start', 4*1000)
            )

    def deadtime(self, *args):
        self.notify(*args,
            subject='DEADTIME',
            urgency='low',
            head='Backup {}: Braucht noch nicht wieder',
            timeout=self.config.timeout('deadtime', 2*1000)
            )

    # TODO remaining level ABORT
    # TODO remaining level FAIL
    # TODO remaining level *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Show and send a notification""")
    Config.add_options(parser)
    log.add_options(parser)
    parser.add_argument('--no-notify', '-N', required=False, default=False, action='store_true')
    # parser.add_argument('--subject', required=True)
    parser.add_argument('notification_text', nargs='+')
    cmdopts = parser.parse_args()

    nlog = log.get_logger('notify', cmdopts)
    config_ = Config(cmdopts.config)
    notify = Notify(config_, show=not cmdopts.no_notify)
    # TODO notification severity from cmd line
    notify.success(*cmdopts.notification_text)
