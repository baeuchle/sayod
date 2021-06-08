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

def oneline(text):
    return text.replace('\n', '')

class Notify:
    @classmethod
    def add_options(cls, ap, **kwargs):
        group = ap.add_argument_group('Notification')
        group.add_argument('--no-notify',
                            action='store_true',
                            dest='notification_dontshow',
                            help="Don't show notification on screen",
                            required=False)

    def __init__(self, config, logger, **kwargs):
        self.show = kwargs.get('show', False)
        self.config = config
        self.friendly = self.config.find('info', 'friendly_name',
                             self.config.find('info', 'stripped_name',
                                'UNKNOWN'))
        self.log = logger
        self.env = os.environ
        if self.show:
            wns = run(['which', 'notify-send'], check=False, stdout=DEVNULL, stderr=DEVNULL)
            if wns.returncode != 0:
                logger.critical('Kann notify-send nicht finden, bitte installieren')
                sys.exit(127)
            if not 'XDG_RUNTIME_DIR' in self.env:
                self.env['XDG_RUNTIME_DIR'] = '/run/user/{}'.format(os.getuid())
        self.ssh = {
            'host': self.config.find('notify', 'host', 'localhost'),
            'user': self.config.find('notify', 'user', self.env['LOGNAME']),
            'port': self.config.find('notify', 'port', 22),
            'pipe': self.config.find('notify', 'pipe', False),
            'remote': self.config.find('notify', 'remotekey',
                self.config.find('info', 'stripped_name', self.friendly))
        }
        if self.ssh['pipe'] in ('no', 'nein', 'false'):
            self.ssh['pipe'] = False

    def notify_local(self, long_msg, **kwargs):
        msg = textwrap.fill(long_msg, width=72)[0:131071]
        head = kwargs.get('head', "NOTIFICATION")
        if self.show:
            run(['notify-send',
                 '-u', kwargs.get('urgency', 'low'),
                 '-t', str(kwargs.get('timeout', 10000)),
                 head, msg],
                env=self.env,
                check=False,
                stdout=DEVNULL,
                stderr=DEVNULL)
        self.log.info('NOTIFY-SEND {}'.format(head))
        self.log.info(long_msg)

    def notify(self, *msg_args, **kwargs):
        msg = " ".join(msg_args)
        self.notify_local(msg, **kwargs)
        if self.ssh['pipe']:
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
                     head='Backup-Fehler {}'.format(self.friendly),
                     urgency='critical',
                     timeout=self.config.find('timeout', 'fatal', 3600000)
                     )
        else:
            self.log.info('content-type: text/x-plain-log')
            self.log.info(self.ssh['remote'])
            self.log.info(kwargs.get('subject', ''))
            self.log.info(msg)

    def success(self, *args):
        self.notify(*args,
               subject='SUCCESS',
               urgency='low',
               head='Backup {}: Erfolg'.format(self.friendly),
               timeout=int(self.config.find('timeout', 'success',
                           self.config.find('notify', 'timeout', 4000)))
              )

    # TODO remaining levels ABORT, DEADTIME, FAIL, FATAL, START, *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Show and send a notification""")
    Config.add_options(parser)
    log.add_options(parser)
    parser.add_argument('--no-notify', '-N', required=False, default=False, action='store_true')
    # parser.add_argument('--subject', required=True)
    parser.add_argument('notification_text', nargs='+')
    cmdopts = parser.parse_args()

    log = log.get_logger('notify', cmdopts)
    config_ = Config(cmdopts.config, log)
    notify = Notify(config_, log, show=not cmdopts.no_notify)
    # TODO notification severity from cmd line
    notify.success(*cmdopts.notification_text)
