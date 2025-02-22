import datetime
import logging
from .taggedentry import TaggedEntry

tllog = logging.getLogger(__name__)


class TaggedLog:
    def __init__(self, log_file, mode='r'):
        self.log_file = log_file
        self.file_obj = None
        if self.log_file == "":
            raise AttributeError("Cannot find out where log is kept")
        self.file_obj = open(self.log_file, mode, encoding='utf-8')

    def __del__(self):
        if self.file_obj is not None:
            self.file_obj.close()

    def __iter__(self):
        return self

    def __next__(self):
        return TaggedEntry(next(self.file_obj))

    def _find(self, **kwargs):
        opts = {'subjects': [],
                'ret': 'entry',
                'action': 'list',
                'since': datetime.datetime.min,
                'until': datetime.datetime.max,
                }
        if kwargs is not None:
            for key, val in kwargs.items():
                opts[key] = val
            if 'subject' in kwargs:
                opts['subjects'].append(kwargs['subject'])
        opts['action'] = opts['action'].lower()
        tllog.debug("TaggedLog looks for %s in %s", opts['action'], opts['subjects'])
        result = []
        if opts['action'] == 'last':
            result.append(None)
        if opts['action'] == 'count':
            result.append(0)
        for entry in self:
            if entry.date < opts['since']:
                continue
            if opts['until'] < entry.date:
                continue
            if len(opts['subjects']) != 0 and entry.subject not in opts['subjects']:
                continue
            # we've got a match!
            if opts['action'] == 'count':
                result[0] += 1
            if opts['action'] == 'first':
                return [entry]
            if opts['action'] == 'last':
                result[0] = entry
            if opts['action'] == 'list':
                result.append(entry)
        return result

    def find(self, **kwargs):
        # store current position so that we don't interfere with
        # iteration:
        old_position = self.file_obj.tell()
        self.file_obj.seek(0, 0)
        result = self._find(**kwargs)
        self.file_obj.seek(old_position, 0)
        return result

    def find_one(self, **kwargs):
        f = self.find(**kwargs)
        if f:
            return f[0]
        return None

    def append(self, new_entry):
        self.file_obj.seek(0, 2)
        self.file_obj.write(str(new_entry) + "\n")
