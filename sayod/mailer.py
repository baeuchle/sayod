import logging
from email.message import EmailMessage
from smtplib import SMTP
from gnupg import GPG

from .config import Config
from .taggedlog import TaggedEntry

mlog = logging.getLogger(__name__)


class Mailer:
    def __init__(self, content):
        self.text = content

    def sign(self, key):
        if not key or not key.startswith('0x'):
            return
        gpg = GPG()
        gpg.encoding = 'utf-8'
        self.text = str(gpg.sign(self.text, clearsign=True, keyid=key))

    def send(self):
        mailprg = Config.get().find('mail', 'type', "echo")
        if mailprg != 'mail':
            # this is the 'echo' option of mail::type
            print(self.text)
            return TaggedEntry('echoed', 'MAIL')
        msg = EmailMessage()
        msg.set_default_type("text/plain; charset=utf-8")
        msg.set_content(self.text)
        msg['To'] = Config.get().find('mail', 'email', 'backup-user@localhost')
        msg['From'] = Config.get().find('mail', 'sender', 'backup-user@localhost')
        msg['Subject'] = Config.get().find('mail', 'subject', 'Backup Script')
        with SMTP('localhost') as s:
            try:
                s.send_message(msg)
            except BaseException as be:  # pylint: disable=broad-except
                mlog.exception()
                return TaggedEntry(str(be), "NOMAIL")
        return TaggedEntry(msg['To'], "MAIL")
