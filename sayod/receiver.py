import logging
import sys

from .config import Config
from .log import Log
from .taggedentry import FromStream
from .taggedlog import TaggedLog
from .version import __version__

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
        return sp.add_parser('receive',
            help='''Reads new log entries from STDIN and adds them to the appropriate log.
            Communication follows text/x-plain-log type''')

    @classmethod
    def standalone(cls, _):
        if cls._instance is None:
            cls._instance = _Receiver('text/x-plain-log')
        cls._instance.run()

    @classmethod
    def init_from_stdin(cls):
        line = sys.stdin.readline().strip()
        content_type = "text/x-plain-log"
        if line.startswith("content-type: "):
            content_type = line[len("content-type: "):]
            rlog.debug("received %s", line)
            line = sys.stdin.readline().strip()
        rlog.debug("received %s", line)
        Log.init(None, "receiver " + line.strip())
        Config.init_file(line)
        cls._instance = _Receiver(content_type)

# entry point for 'receiver' command as created by installing the wheel
def receiver():
    try:
        Log.init_root()
        rlog.info("Executing receiver (v%s)", __version__)
        Receiver.init_from_stdin()
        Receiver.standalone(None)
        rlog.debug("receiver end")
    except Exception:
        rlog.exception("Program failed hard")
