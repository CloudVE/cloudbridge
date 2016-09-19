import logging
import sys

# Current version of the library
__version__ = '0.1.1'


def get_version():
    """
    Return a string with the current version of the library (e.g., "0.1.0").
    """
    return __version__


def init_logging():
    """
    Temporary workaround for build timeouts by enabling logging to
    stdout so that travis doesn't think the build has hung.
    """
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

log = logging.getLogger('cloudbridge')
log.addHandler(logging.StreamHandler())
