from datetime import date, timedelta
import logging

from config import Config

slog = logging.getLogger('backup.scope')

class Scope:
    INTO_DEFAULTS = {'monthly': True, 'weekly': False, 'daily': False}

    def __init__(self, scope, keep_previous):
        self.scope = scope
        self.keep_previous = keep_previous
        self.into_last()
        today = date.today()
        self.time_fmt = '%Y-%m-%d'
        if scope == 'monthly':
            self.end_date = today.replace(day=1)
            self.start_date = (self.end_date - timedelta(days=1)).replace(day=1)
        elif scope == 'weekly':
            self.end_date = today - timedelta(days=today.weekday()) # this is last monday midnight
            self.start_date = self.end_date - timedelta(days=7)
        elif scope == 'daily':
            self.end_date = today
            self.start_date = today - timedelta(days=1)
            self.time_fmt = '%Y-%m-%dT%H:%M:%S'
        else:
            slog.error("Unkown scope %s", scope)
            raise ValueError("Unknown scope " + scope)
        slog.debug('Scope %s from %s to %s', scope, self.end_date, self.start_date)

    @property
    def start_string(self):
        return self.start_date.strftime(self.time_fmt)

    @property
    def end_string(self):
        return self.end_date.strftime(self.time_fmt)

    def into_last(self):
        if self.keep_previous is None:
            self.keep_previous = Config.get().find('squash', self.scope,
                                                   Scope.INTO_DEFAULTS[self.scope])
