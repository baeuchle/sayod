try:
    from ._version import __version__, __version_tuple__
except ImportError:
    from .gitversion import Git
    _g = Git()
    __version__ = _g.describe()
    __version_tuple__ = __version__.split('.')
