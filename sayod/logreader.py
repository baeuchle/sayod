import sys
import logging

from .config import Config
from .log import Log
from .plain_log import PlainLog
from .taggedlog import TaggedLog

lrlog = logging.getLogger(__name__)

def get_subjects(**kwargs):
    if kwargs.get('subject', False):
        return kwargs['subject']
    subject_list = []
    for line in sys.stdin:
        if line.strip() == "":
            break
        subject_list.append(line.strip())
    # this is due to a bug in sayod<=5.2.2 which sent SUCCESS as single letters.
    if all(len(x) == 1 for x in subject_list):
        subject_list = [''.join(subject_list)]
    return subject_list

def get_action(**kwargs):
    if kwargs.get('action', False):
        return kwargs['action']
    action = PlainLog.LIST
    for line in sys.stdin:
        if line.strip():
            action = line.strip()
    return action

def read_log(**kwargs):
    status_file = Config.get().find('status', 'file', None)
    if status_file is None:
        lrlog.warning("Status file cannot be determined")
        raise SystemExit(1)
    log_obj = TaggedLog(status_file, 'r')

    subject_list = get_subjects(**kwargs)
    action = get_action(**kwargs)
    lrlog.info("Looking into TaggedLog for %s on %s", action, subject_list)

    entries = log_obj.find(subjects=subject_list, action=action)
    return entries

class LogReader:
    prog = 'logreader'
    print_result = True

    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser(cls.prog,
                        help='''Read log. Used for remote access mostly''')
        PlainLog.add_options(ap)
        return ap

    @classmethod
    def standalone(cls, **kwargs):
        return '\n'.join(list(str(x) for x in read_log(**kwargs)))

# entry point for 'logreader' command as created by installing the wheel
def logreader():
    Log.init_root()
    lrlog.info("Starting %s", __name__)
    line = sys.stdin.readline().strip()
    content_type = "text/x-plain-ask"
    if line.startswith("content-type: "):
        content_type = line[len("content-type: "):]
        lrlog.debug("received %s", line)
        line = sys.stdin.readline().strip()
    Config.init(configuration_file=line)

    print(LogReader.standalone())
