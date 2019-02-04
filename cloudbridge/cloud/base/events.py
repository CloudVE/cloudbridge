import bisect
import collections
import fnmatch
import logging
import re

from ..interfaces.events import EventDispatcher
from ..interfaces.exceptions import HandlerException

log = logging.getLogger(__name__)


class InterceptingEventHandler(object):

    def __init__(self, event_name, priority, callback):
        self.dispatcher = None
        self.event_name = event_name
        self.priority = priority
        self.callback = callback

    def __lt__(self, other):
        # This is required for the bisect module to insert
        # event handlers sorted by priority
        return self.priority < other.priority

    def get_next_handler(self, full_event_name):
        handler_list = self.dispatcher.handler_cache.get(full_event_name, [])
        # find position of this handler
        pos = bisect.bisect_left(handler_list, self)
        assert handler_list[pos] == self
        if pos < len(handler_list)-1:
            return handler_list[pos+1]
        else:
            return None

    def invoke(self, **kwargs):
        kwargs.pop('next_handler', None)
        next_handler = self.get_next_handler(kwargs.get('event_name', None))
        # callback is responsible for invoking the next_handler and
        # controlling the result value
        return self.callback(next_handler=next_handler, **kwargs)


class ObservingEventHandler(InterceptingEventHandler):

    def __init__(self, event_name, priority, callback):
        super(ObservingEventHandler, self).__init__(event_name, priority,
                                                    callback)

    def invoke(self, **kwargs):
        # Notify listener. Ignore result from observable handler
        kwargs.pop('next_handler', None)
        self.callback(**kwargs)
        # Kick off the handler chain
        next_handler = self.get_next_handler(kwargs.get('event_name', None))
        if next_handler:
            return next_handler.invoke(**kwargs)
        else:
            return None


class SimpleEventDispatcher(EventDispatcher):

    def __init__(self):
        # The dict key is event_name.
        # The dict value is a list of handlers for the event, sorted by event
        # priority
        self.__events = collections.OrderedDict({})
        self.__handler_cache = {}

    @property
    def handler_cache(self):
        return self.__handler_cache

    def _create_handler_cache(self, event_name):
        cache_list = []
        # sort from most specific to least specific
        for key in self.__events.keys():
            if re.search(fnmatch.translate(key), event_name):
                cache_list.extend(self.__events[key])
        cache_list.sort(key=lambda h: h.priority)

        # Make sure all priorities are unique
        priority_list = [h.priority for h in cache_list]
        if len(set(priority_list)) != len(priority_list):
            guilty_prio = None
            for prio in priority_list:
                if prio == guilty_prio:
                    break
                guilty_prio = prio

            # guilty_prio should never be none since we checked for
            # duplicates before iterating
            guilty_names = [h.callback.__name__ for h in cache_list
                            if h.priority == guilty_prio]

            message = "Event '{}' has multiple subscribed handlers " \
                      "at priority '{}', with function names [{}]. " \
                      "Each priority must only have a single " \
                      "corresponding handler." \
                .format(event_name, guilty_prio, ", ".join(guilty_names))
            raise HandlerException(message)
        return cache_list

    def _subscribe(self, event_handler):
        """
        subscribe an event handler to this dispatcher
        """
        event_handler.dispatcher = self
        handler_list = self.__events.get(event_handler.event_name, [])
        handler_list.append(event_handler)
        self.__events[event_handler.event_name] = handler_list

    def observe(self, event_name, priority, callback):
        handler = ObservingEventHandler(event_name, priority, callback)
        self._subscribe(handler)

    def intercept(self, event_name, priority, callback):
        handler = InterceptingEventHandler(event_name, priority, callback)
        self._subscribe(handler)

    def emit(self, sender, event_name, **kwargs):
        handlers = self.handler_cache.get(event_name)
        if handlers is None:
            self.__handler_cache[event_name] = self._create_handler_cache(
                event_name)
            handlers = self.handler_cache.get(event_name)

        if handlers:
            # only kick off first handler in chain
            return handlers[0].invoke(sender=sender, event_name=event_name,
                                      **kwargs)
        else:
            message = "Event '{}' has no subscribed handlers.".\
                format(event_name)
            log.warning(message)
            return None
