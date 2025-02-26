from contextlib import ExitStack
import datetime
import logging

from .config import Config
from .notify import Notify
from .plain_log import PlainLog
from .provider import ProviderFactory, ProvideError
from .remotereader import remote

clog = logging.getLogger(__name__)


class Context:
    @classmethod
    def test_deadtime(cls, **kwargs):
        deadtime = int(Config.get().find('rsync', 'deadtime', 0))
        if deadtime <= 0:
            clog.debug("No deadtime given, going ahead")
            return True
        last_success = remote(['SUCCESS'], PlainLog.LAST).date
        clog.debug("Last success was %s", last_success)
        tage = (datetime.datetime.today() - last_success).days
        if tage > deadtime:
            clog.info("Deadtime is over")
            return True
        if not kwargs.get('context_force', False):
            Notify.get().deadtime(
                                  f"Letztes erfolgreiches Backup war vor weniger als {deadtime} "
                                  f"Tagen ({last_success:%d.%m.%Y})")
            return False
        clog.info("Deadtime ignored because --force was specified")
        return True

    def __init__(self, subcommand='copy'):
        self.es_obj = ExitStack()
        self.es = None
        if subcommand in ['analyse']:
            self.providers = []
        else:
            self.providers = Config.get().find('context', 'providers', '').split()

    def __enter__(self):
        clog.info("Entering provider contexts...")
        self.es = self.es_obj.__enter__()
        for prv in self.providers:
            try:
                self.es.enter_context(ProviderFactory(prv))
            except ProvideError as pe:
                clog.info("ProvideError: %s", pe)
                raise SystemExit(1) from pe
        clog.info("All contexts successfully acquired")

    def __exit__(self, exc_type, exc_val, exc_tb):
        clog.info("Getting out of the argument")
        self.es.__exit__(exc_type, exc_val, exc_tb)
