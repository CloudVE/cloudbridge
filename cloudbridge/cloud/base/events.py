import fnmatch
import re
from copy import deepcopy
from enum import Enum

from ..interfaces.events import EventDispatcher
from ..interfaces.exceptions import HandlerException


class HandlerType(Enum):
    """
    Handler Types.
    """
    SUBSCRIPTION = 'subscription'
    INTERCEPTION = 'intercept'


class SimpleEventDispatcher(EventDispatcher):

    def __init__(self):
        self.__events = {}
        self.__initialized = {}

    def get_handlers(self, event_name):
        return self.__events.get(event_name)

    def check_initialized(self, event_name):
        return self.__initialized.get(event_name) or False

    def mark_initialized(self, event_name):
        self.__initialized[event_name] = True

    def subscribe(self, event_name, priority, callback):
        handler = EventHandler(HandlerType.SUBSCRIPTION, callback, priority)
        if not self.__events.get(event_name):
            self.__events[event_name] = list()
        self.__events[event_name].append((priority, handler))

    def intercept(self, event_name, priority, callback):
        handler = EventHandler(HandlerType.INTERCEPTION, callback, priority)
        if not self.__events.get(event_name):
            self.__events[event_name] = list()
        self.__events[event_name].append((priority, handler))

    def call(self, event_name, priority, callback, **kwargs):
        handler = EventHandler(HandlerType.SUBSCRIPTION, callback, priority)
        if not self.__events.get(event_name):
            self.__events[event_name] = list()
        # Although handler object has priority property, keep it a pair to not
        # access each handler when sorting
        self.__events[event_name].append((priority, handler))
        try:
            ret_obj = self._emit(event_name, **kwargs)
        finally:
            self.__events[event_name].remove((priority, handler))
        return ret_obj

    def _emit(self, event_name, **kwargs):

        def _match_and_sort(event_name):
            new_list = []
            for key in self.__events.keys():
                if re.search(fnmatch.translate(key), event_name):
                    new_list.extend(deepcopy(self.__events[key]))
            new_list.sort(key=lambda x: x[0])
            # Make sure all priorities are unique
            priority_list = [x[0] for x in new_list]
            if len(set(priority_list)) != len(priority_list):

                guilty_prio = None
                for prio in priority_list:
                    if prio == guilty_prio:
                        break
                    guilty_prio = prio

                # guilty_prio should never be none since we checked for
                # duplicates before iterating
                guilty_names = [x[1].callback.__name__
                                for x in new_list
                                if x[0] == guilty_prio]

                message = "Event '{}' has multiple subscribed handlers " \
                          "at priority '{}', with function names [{}]. " \
                          "Each priority must only have a single " \
                          "corresponding handler." \
                    .format(event_name, priority, ", ".join(guilty_names))
                raise HandlerException(message)

            return new_list

        if not self.__events.get(event_name):
            message = "Event '{}' has no subscribed handlers.".\
                format(event_name)
            raise HandlerException(message)

        prev_handler = None
        first_handler = None
        for (priority, handler) in _match_and_sort(event_name):
            if not first_handler:
                first_handler = handler
            if prev_handler:
                prev_handler.next_handler = handler
            prev_handler = handler
        return first_handler.invoke(**kwargs)


class EventHandler(object):
    def __init__(self, handler_type, callback, priority):
        self.handler_type = handler_type
        self.callback = callback
        self._next_handler = None
        self.priority = priority

    @property
    def next_handler(self):
        return self._next_handler

    @next_handler.setter
    def next_handler(self, new_handler):
        self._next_handler = new_handler

    def invoke(self, **kwargs):
        if self.handler_type == HandlerType.SUBSCRIPTION:
            result = self.callback(**kwargs)

            next = self.next_handler
            if next:
                if next.handler_type == HandlerType.SUBSCRIPTION:
                    if result or not kwargs.get('callback_result', None):
                        kwargs['callback_result'] = result
                    new_result = next.invoke(**kwargs)
                elif next.handler_type == HandlerType.INTERCEPTION:
                    new_result = next.invoke(**kwargs)

                if new_result:
                    result = new_result

            self.next_handler = None

        elif self.handler_type == HandlerType.INTERCEPTION:
            kwargs.pop('next_handler', None)
            result = self.callback(next_handler=self.next_handler, **kwargs)
            self.next_handler = None

        return result

    def skip(self, **kwargs):
        if self.next_handler:
            self.next_handler.invoke(**kwargs)
            self.next_handler = None

    def skip_to_name(self, function_name, **kwargs):
        if self.callback.__name__ == function_name:
            self.invoke(**kwargs)
        elif self.next_handler:
            self.next_handler.skip_to_name(function_name, **kwargs)
            self.next_handler = None

    def skip_to_priority(self, priority, **kwargs):
        if self.priority == priority:
            self.invoke(**kwargs)
        elif self.next_handler:
            self.next_handler.skip_to_priority(priority, **kwargs)
            self.next_handler = None

    def skip_rest(self):
        if self.next_handler:
            self.next_handler.skip_rest()
            self.next_handler = None
