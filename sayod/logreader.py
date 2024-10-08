import sys
import logging

from .config import Config
from .log import Log
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
        action = 'list'
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

    entries = log_obj.find(subjects=subject_list, action=action)
    return entries

class LogReader:
    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser('readlog',
                        help='''Read log. Used for remote access mostly''')
        ap.add_argument('--action',
                        help='specify which action should be read from the log',
                        default='list',
                        choices='last count first list'.split())
        ap.add_argument('--subject', nargs='+',
                        help='for which subjects should the action be taken?')
    @classmethod
    def standalone(cls, args):
        return read_log(args)

# entry point for 'logreader' command as created by installing the wheel
def logreader():
    Log.init_root()
    line = sys.stdin.readline().strip()
    content_type = "text/x-plain-ask"
    if line.startswith("content-type: "):
        content_type = line[len("content-type: "):]
        line = sys.stdin.readline().strip()
    Config.init_file(line)

    print(LogReader.standalone(None))
