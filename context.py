from contextlib import ExitStack
import logging

from config import Config
from provider import ProviderFactory, ProvideError

clog = logging.getLogger('backup.context')

class Context:
    def __init__(self, provider_list = None):
        if provider_list is None:
            provider_list = []
        self.es_obj = ExitStack()
        self.es = None
        self.providers = provider_list
        self.providers.extend(Config.get().find('context', 'providers', '').split())

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
