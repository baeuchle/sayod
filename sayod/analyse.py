import datetime
import logging

from .config import Config
from .gitversion import Git
from .mailer import Mailer
from .taggedentry import TaggedEntry
from .taggedlog import TaggedLog

alog = logging.getLogger(__name__)

class _Analyse:
    def __init__(self):
        self.error_log = {
            'NOTIFY': [],
            'WARN': [],
            'ERR': []
        }
        self.content_headlines = {cat: Config.get().find('category_headlines', cat, cat)
                                    for cat in self.error_log }
        self.log_obj = TaggedLog(Config.get().find('status', 'file', ''), 'r')
        self.warn_missing_success = Config.get().find("status", "warn_missing", 9)
        self.now = datetime.datetime.now()
        self.warn_missing_since = self.now - datetime.timedelta(days=int(self.warn_missing_success))
        self.text = ""

    def find_last_success(self):
        last_success = self.log_obj.find_one(subject="SUCCESS", action='last')
        if not last_success:
            last_success = TaggedEntry(
                "Es wurde noch nie ein erfolgreiches Backup gemacht",
                "NEVER"
            )
            alog.info(last_success.content)
            return
        if last_success.date >= self.warn_missing_since:
            return
        msg = Config.get().find("messages", "warn_missing",
            "Last successful backup was before {last_success.date:%Y.%m.%d %H:%M}."
        ).format(
                days=self.warn_missing_success,
                last_success=last_success
            )
        last_start = self.log_obj.find_one(subject="START", since=last_success.date, action='last')
        if last_start:
            msg += "\n\n"
            msg += Config.get().find("messages", "report_last_started",
                "Last backup was at {last_start[0].date:%Y.%m.%d %H:%M}"
            ).format(
                last_start=last_start,
                diff=(self.now - last_start.date)
            )
        else:
            msg += "\n\n"
            msg += Config.get().find("messages", "no_further_tries",
                "No more tries are recorded"
            )
        last_success.content = msg.strip().replace('\n', "\\n")
        self.error_log['WARN'].append(last_success)
        alog.warning(last_success.content)

    def find_new_errors(self):
        last_analysis = self.log_obj.find_one(subjects=["ANALYSE", "MAIL"], action='last')
        if not last_analysis:
            last_date = datetime.datetime.min
        else:
            last_date = last_analysis.date

        for entry in self.log_obj.find(since=last_date, action='list'):
            if entry.subject in (
                'ABORT',
                'ANALYSE',
                'DEADTIME',
                'MAIL',
                'START',
                'SUCCESS'
                    ):
                continue
            self.error_log['ERR'].append(entry)

    @property
    def number_of_messages(self):
        return sum(list(len(x) for x in self.error_log.values()))

    @property
    def has_something_to_report(self):
        return self.number_of_messages > len(self.error_log['NOTIFY'])

    def compose_mail(self):
        if not self.has_something_to_report:
            return
        self.text = Config.get().find('messages', 'opening', "Hallo")
        self.text += "\n"
        self.text += Config.get().find("messages", "analyse_headline",
            "Analysis has found {count} message(s)"
        ).format(
            count=self.number_of_messages
        )
        self.text += "\n"

        for cat, content in self.error_log.items():
            if len(content) == 0:
                continue
            self.text += f" - {len(content)} {self.content_headlines[cat]}\n"

        self.text += "\n"

        for cat in ('ERR', 'WARN', 'NOTIFY'):
            if len(self.error_log[cat]) == 0:
                continue

            self.text += f"###### {self.content_headlines[cat]:s} #####\n"
            for ele in self.error_log[cat]:
                self.text += ele.long_text(prefix='* ')

        self.text += Config.get().find('messages', 'closing', 'Bye')
        self.text += "\n\n--\n"
        self.text += Config.get().find("messages", "version",
            "Created by version {version}"
        ).format(
            version=Git().describe()
        )
        self.text = self.text.strip()

    def send_mail(self):
        can_log = True
        try:
            write_log = TaggedLog(self.log_obj.log_file, 'a+')
        except PermissionError as pe:
            alog.error("Cannot append to log file: %s", pe)
            self.text += "\n\nThe fact that this mail has been written could not be stored."
            can_log = False

        m = Mailer(self.text)
        m.sign(Config.get().find('mail', 'sign', None))
        entry = m.send()

        if can_log:
            write_log.append(entry)

class Analyse:
    @classmethod
    def add_subparser(cls, sp):
        return sp.add_parser('analyse',
            help='Analyses log entries and reports via mail')

    @classmethod
    def standalone(cls, _):
        a = _Analyse()
        a.find_last_success()
        a.find_new_errors()
        a.compose_mail()
        a.send_mail()
