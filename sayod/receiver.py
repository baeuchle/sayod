import logging
import sys

from .config import Config
from .log import Log
from .taggedlog import TaggedLog, FromStream

rlog = logging.getLogger(__name__)

class _Receiver:
    def __init__(self, content_type):
        self.content_type = content_type

    def run(self):
        status_file = Config.get().find('status', 'file', None)
        if status_file is None:
            rlog.warning("Status file cannot be determined")
            raise SystemExit(1)
        log_obj = TaggedLog(status_file, 'a+')
        entry = FromStream(sys.stdin, self.content_type)
        log_obj.append(entry)

class Receiver:
    _instance = None

    @classmethod
    def add_subparser(cls, sp):
        _ = sp.add_parser('receive',
            help='''Reads new log entries from STDIN and adds them to the appropriate log.
            Communication follows text/x-plain-log type''')

    @classmethod
    def standalone(cls, _):
        if _instance is None:
            _instance = _Receiver('text/x-plain-log')
        _instance.run()

    @classmethod
    def init_from_stdin(cls):
        line = sys.stdin.readline().strip()
        content_type = "text/x-plain-log"
        if line.startswith("content-type: "):
            content_type = line[len("content-type: "):]
            line = sys.stdin.readline().strip()
        Config.init_file(line)
        _instance = _Receiver(content_type)

# entry point for 'receiver' command as created by installing the wheel
def receiver():
    Log.init_root()
    Receiver.init_from_stdin()
    Receiver.standalone(None)
