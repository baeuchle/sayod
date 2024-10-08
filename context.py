from contextlib import ExitStack

import log
from provider import ProviderFactory, ProvideError

clog = log.get_logger('context')

class Context:
    def __init__(self, config, provider_list = []):
        self.es_obj = ExitStack()
        self.es = None
        self.config = config
        self.providers = provider_list
        self.providers.extend(config.find('context', 'providers', '').split())

    def __enter__(self):
        clog.info("Entering provider contexts...")
        self.es = self.es_obj.__enter__()
        for prv in self.providers:
            try:
                self.es.enter_context(ProviderFactory(prv, self.config))
            except ProvideError as pe:
                clog.info("ProvideError: %s", pe)
                raise SystemExit(1) from pe
        clog.info("All contexts successfully acquired")

    def __exit__(self, exc_type, exc_val, exc_tb):
        clog.info("Getting out of the argument")
        self.es.__exit__(exc_type, exc_val, exc_tb)
