import logging
import sys

from pyeventsystem.middleware import dispatch as pyevent_dispatch
from pyeventsystem.middleware import intercept
from pyeventsystem.middleware import observe

import six

from ..interfaces.exceptions import CloudBridgeBaseException

log = logging.getLogger(__name__)


dispatch = pyevent_dispatch


class EventDebugLoggingMiddleware(object):
    """
    Logs all event parameters. This middleware should not be enabled other
    than for debugging, as it could log sensitive parameters such as
    access keys.
    """
    @observe(event_pattern="*", priority=100)
    def pre_log_event(self, event_args, *args, **kwargs):
        log.debug("Event: {0}, args: {1} kwargs: {2}".format(
            event_args.get("event"), args, kwargs))

    @observe(event_pattern="*", priority=4900)
    def post_log_event(self, event_args, *args, **kwargs):
        log.debug("Event: {0}, result: {1}".format(
            event_args.get("event"), event_args.get("result")))


class ExceptionWrappingMiddleware(object):
    """
    Wraps all unhandled exceptions in cloudbridge exceptions.
    """
    @intercept(event_pattern="*", priority=1050)
    def wrap_exception(self, event_args, *args, **kwargs):
        next_handler = event_args.pop("next_handler")
        if not next_handler:
            return
        try:
            return next_handler.invoke(event_args, *args, **kwargs)
        except Exception as e:
            if isinstance(e, CloudBridgeBaseException):
                raise
            else:
                ex_type, ex_value, traceback = sys.exc_info()
                cb_ex = CloudBridgeBaseException(
                    "CloudBridgeBaseException: {0} from exception type: {1}"
                    .format(ex_value, ex_type))
                if sys.version_info >= (3, 0):
                    six.raise_from(cb_ex, e)
                else:
                    six.reraise(CloudBridgeBaseException, cb_ex, traceback)
