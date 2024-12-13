import datetime
import logging
from textwrap import TextWrapper

telog = logging.getLogger(__name__)

class TaggedEntry:
    timeformat = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, content, subject=None, date=None):
        """subject is the "tag", e.g., DEADTIME or SUCCESS"""
        telog.debug("Creating TaggedEntry from %s", content.strip())
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

def _FromPlainLog(stream):
    result = TaggedEntry("")
    for line in stream:
        if line.strip() == "":
            continue
        result.subject = line.strip()
        break
    result.content = stream.read().strip()
    return result

def FromStream(stream, content_type='text/x-plain-log'):
    if content_type == "text/x-plain-log":
        return _FromPlainLog(stream)
    raise AttributeError("Cannot read data of type " + content_type)
