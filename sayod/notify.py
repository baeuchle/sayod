#!/usr/bin/python3

"""Wrapper around notify-send, because libnotify can't be bothered to do
sensible stuff"""

import argparse
import logging
import os
from subprocess import run, Popen, PIPE, DEVNULL
import textwrap

from .config import Config
nlog = logging.getLogger(__name__)


def oneline(text):
    return text.strip().replace('\n', ' ')


class _Notify:
    def __init__(self, **kwargs):
        self.show = kwargs.get('notification_show', False)
        self.friendly = Config.get().find('info', 'friendly_name',
                                          Config.get().find('info', 'stripped_name',
                                                            'UNKNOWN'))
        self.env = os.environ
        if self.show:
            wns = run(['which', 'notify-send'], check=False, stdout=DEVNULL, stderr=DEVNULL)
            if wns.returncode != 0:
                nlog.critical('Kann notify-send nicht finden, bitte installieren')
                raise SystemExit(127)
            if 'XDG_RUNTIME_DIR' not in self.env:
                self.env['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
        self.ssh = {
            'host': Config.get().find('notify', 'host', 'localhost'),
            'user': Config.get().find('notify', 'user', self.env['LOGNAME']),
            'port': Config.get().find('notify', 'port', "22"),
            'pipe': Config.get().find('notify', 'pipe', False),
            'remote': Config.get().find('notify', 'remotekey',
                                        Config.get().find('info', 'stripped_name',
                                                          self.friendly))
        }
        if self.ssh['pipe'] in ('no', 'nein', 'false'):
            self.ssh['pipe'] = False

    def notify_local(self, long_msg, **kwargs):
        msg = textwrap.fill(long_msg, width=72)[0:131071]
        head = kwargs.get('head', "NOTIFICATION").format(self.friendly)
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
                     timeout=Config.get().timeout('fatal', 60*60*1000)
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
                    timeout=Config.get().timeout('success', 4*1000)
                    )

    def fatal(self, *args):
        self.notify(*args,
                    subject='WTF!',
                    urgency='critical',
                    head='Backup-Fehler (Fatal): {}',
                    timeout=Config.get().timeout('fatal', 60*60*1000)
                    )

    def start(self, *args):
        self.notify(*args,
                    subject='START',
                    urgency='low',
                    head='Starte Backup {}',
                    timeout=Config.get().timeout('start', 4*1000)
                    )

    def deadtime(self, *args):
        self.notify(*args,
                    subject='DEADTIME',
                    urgency='low',
                    head='Backup {}: Braucht noch nicht wieder',
                    timeout=Config.get().timeout('deadtime', 2*1000)
                    )

    def abort(self, *args):
        self.notify(*args,
                    subject='ABORT',
                    urgency='normal',
                    head='Backup {} abgebrochen',
                    timeout=Config.get().timeout('abort', 10*1000)
                    )

    def fail(self, *args):
        self.notify(*args,
                    subject='FAIL',
                    urgency='critical',
                    head='Backup {}: Fehler',
                    timeout=Config.get().timeout('fail', 60*1000)
                    )


class Notify:
    _instance = None
    prog = 'notify'

    @classmethod
    def add_options(cls, ap):
        group = ap.add_argument_group('Notification')
        group.add_argument('--notify',
                           action=argparse.BooleanOptionalAction,
                           dest='notification_show',
                           help="Don't show notification on screen",
                           required=False,
                           default=True)

    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser(cls.prog, help='Write Notifications to libnotify and remote server')
        ap.add_argument('--level', required=True,
                        choices='abort deadtime fail fatal start success'.split())
        ap.add_argument('notification_text', nargs='+')
        return ap

    @classmethod
    def init(cls, **kwargs):
        cls._instance = _Notify(**kwargs)

    @classmethod
    def get(cls):
        return cls._instance

    @classmethod
    def standalone(cls, **kwargs):
        getattr(cls._instance, kwargs.get('level', 'start'))(*kwargs.get('notification_text'))
