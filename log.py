#!/usr/bin/python3

import datetime
from textwrap import TextWrapper

class TaggedEntry:
    timeformat = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, content, subject=None, date=None):
        # sensible default in many branches:
        self.date = datetime.datetime.now()
        self.content = ""
        # only one parameters? Use it as line.
        if date is None and subject is None:
            words = content.strip().split(' ', 3)
            # one word only? It's the subject.
            if len(words) == 1:
                self.subject = words[0]
            # two words? It's date + subject or subject + content.
            else:
                # at least three words:
                try:
                    self.date = datetime.datetime.strptime(words[0], TaggedEntry.timeformat)
                    self.subject = words[1]
                    if len(words) > 2:
                        self.content = ' '.join(words[2:])
                except:
                    self.subject = words[0]
                    self.content = ' '.join(words[1:])
        else:
            self.content = content
            if subject is None:
                self.subject = "NONE"
            else:
                self.subject = subject
        self.content = self.content.replace('\\n', "\n")
        return

    def __str__(self):
        return ("{:" + TaggedEntry.timeformat + "} {} {}").format(
            self.date,
            self.subject.upper(),
            self.content.replace("\n", '\\n'))

    def long_text(self, **kwargs):
        opts = { 'linestart': '',
                 'prefix': '',
                 'linelength': 72,
                 'dateformat': TaggedEntry.timeformat,
               }
        if kwargs is not None:
            for key, val in kwargs.items():
                opts[key] = val
        result = ("* {:" + opts['dateformat'] + "} ({})\n").format(
            self.date,
            self.subject.upper()
            )
        wrapper = TextWrapper(
            width=opts['linelength'],
            break_long_words=True,
            initial_indent = ('{:' + str(len(opts['prefix'])) + 's}').format(' '),
            subsequent_indent = ('{:' + str(len(opts['prefix'])) + 's}').format(' '),
        )
        for paragraph in self.content.strip().split('\\n\\n'):
            result += wrapper.fill(paragraph.replace('\\n', ' '))
            result += "\n\n"
        return result

class TaggedLog:
    def __init__(self, log_file, mode='r'):
        self.log_file = log_file
        if self.log_file == "":
            self.file_obj = None
            raise Exception("Cannot find out where log is kept")
        self.file_obj = open(self.log_file, mode)

    def __del__(self):
        if self.file_obj is not None:
            self.file_obj.close()

    def __iter__(self):
        return self

    def __next__(self):
        return TaggedEntry(next(self.file_obj))

    def _find(self, **kwargs):
        opts = { 'subjects': [],
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
        result = []
        if opts['action'] == 'last':
            result = None
        if opts['action'] == 'count':
            result = 0
        for entry in self:
            if entry.date < opts['since']:
                continue
            if opts['until'] < entry.date:
                continue
            if len(opts['subjects']) != 0 and not entry.subject in opts['subjects']:
                continue
            # we've got a match!
            if opts['action'] == 'count':
                result += 1
            if opts['action'] == 'first':
                return entry
            if opts['action'] == 'last':
                result = entry
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

    def append(self, new_entry):
        self.file_obj.seek(0, 2)
        self.file_obj.write(str(new_entry) + "\n")
