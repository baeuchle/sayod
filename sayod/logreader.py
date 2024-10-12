import sys
import logging

from .config import Config
from .log import Log
from .plain_log import PlainLog
from .taggedlog import TaggedLog

lrlog = logging.getLogger(__name__)

def get_subjects(args):
    if args is None:
        subject_list = []
        for line in sys.stdin:
            if line.strip() == "":
                break
            subject_list.append(line.strip())
        return subject_list
    return args.subject

def get_action(args):
    if args is None:
        action = PlainLog.LIST
        for line in sys.stdin:
            action = line.strip()
        return action
    return args.action

def read_log(args):
    status_file = Config.get().find('status', 'file', None)
    if status_file is None:
        lrlog.warning("Status file cannot be determined")
        raise SystemExit(1)
    log_obj = TaggedLog(status_file, 'r')

    subject_list = get_subjects(args)
    action = get_action(args)
    lrlog.info("Looking into TaggedLog for %s on %s", action, subject_list)

    entries = log_obj.find(subjects=subject_list, action=action)
    return entries

class LogReader:
    print_result = True

    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser('logreader',
                        help='''Read log. Used for remote access mostly''')
        PlainLog.add_options(ap)
        return ap

    @classmethod
    def standalone(cls, args):
        return '\n'.join(list(str(x) for x in read_log(args)))

# entry point for 'logreader' command as created by installing the wheel
def logreader():
    Log.init_root()
    lrlog.info("Starting %s", __name__)
    line = sys.stdin.readline().strip()
    content_type = "text/x-plain-ask"
    if line.startswith("content-type: "):
        content_type = line[len("content-type: "):]
        line = sys.stdin.readline().strip()
    Config.init_file(line)

    print(LogReader.standalone(None))
