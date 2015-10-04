import logging
import sys


def init_logging():
    """
    Temporary workaround for build timeouts by enabling logging to
    stdout so that travis doesn't think the build has hung.
    """
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger(__name__).setLevel(logging.DEBUG)
