"""Base implementation of a provider interface."""
import fnmatch
import functools
import logging
import os
import re
from copy import deepcopy
from os.path import expanduser
try:
    from configparser import ConfigParser
except ImportError:  # Python 2
    from ConfigParser import SafeConfigParser as ConfigParser

import six

from cloudbridge.cloud.interfaces import CloudProvider
from cloudbridge.cloud.interfaces.exceptions import HandlerException
from cloudbridge.cloud.interfaces.exceptions import ProviderConnectionException
from cloudbridge.cloud.interfaces.provider import HandlerType
from cloudbridge.cloud.interfaces.resources import Configuration

log = logging.getLogger(__name__)

DEFAULT_RESULT_LIMIT = 50
DEFAULT_WAIT_TIMEOUT = 600
DEFAULT_WAIT_INTERVAL = 5

# By default, use two locations for CloudBridge configuration
CloudBridgeConfigPath = '/etc/cloudbridge.ini'
CloudBridgeConfigLocations = [CloudBridgeConfigPath]
UserConfigPath = os.path.join(expanduser('~'), '.cloudbridge')
CloudBridgeConfigLocations.append(UserConfigPath)


class BaseConfiguration(Configuration):

    def __init__(self, user_config):
        self.update(user_config)

    @property
    def default_result_limit(self):
        """
        Get the maximum number of results to return for a
        list method

        :rtype: ``int``
        :return: The maximum number of results to return
        """
        log.debug("Maximum number of results for list methods %s",
                  DEFAULT_RESULT_LIMIT)
        return self.get('default_result_limit', DEFAULT_RESULT_LIMIT)

    @property
    def default_wait_timeout(self):
        """
        Gets the default wait timeout for LifeCycleObjects.
        """
        log.debug("Default wait timeout for LifeCycleObjects %s",
                  DEFAULT_WAIT_TIMEOUT)
        return self.get('default_wait_timeout', DEFAULT_WAIT_TIMEOUT)

    @property
    def default_wait_interval(self):
        """
        Gets the default wait interval for LifeCycleObjects.
        """
        log.debug("Default wait interfal for LifeCycleObjects %s",
                  DEFAULT_WAIT_INTERVAL)
        return self.get('default_wait_interval', DEFAULT_WAIT_INTERVAL)

    @property
    def debug_mode(self):
        """
        A flag indicating whether CloudBridge is in debug mode. Setting
        this to True will cause the underlying provider's debug
        output to be turned on.

        The flag can be toggled by sending in the cb_debug value via
        the config dictionary, or setting the CB_DEBUG environment variable.

        :rtype: ``bool``
        :return: Whether debug mode is on.
        """
        return self.get('cb_debug', os.environ.get('CB_DEBUG', False))


class EventDispatcher(object):
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
        """
        Subscribe a handler by event name to the dispatcher.

        :type event_name: str
        :param event_name: The name of the event to which you are subscribing
        the callback function.
        :type priority: int
        :param priority: The priority that this handler should be given.
        When the event is emitted, all handlers will be run in order of
        priority.
        :type callback: function
        :param callback: The callback function that should be called with
        the parameters given at when the even is emitted.
        """
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


class BaseCloudProvider(CloudProvider):
    def __init__(self, config):
        self._config = BaseConfiguration(config)
        self._config_parser = ConfigParser()
        self._config_parser.read(CloudBridgeConfigLocations)
        self._events = EventDispatcher()

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return str(self.__class__.__name__)

    @property
    def events(self):
        return self._events

    def authenticate(self):
        """
        A basic implementation which simply runs a low impact command to
        check whether cloud credentials work. Providers should override with
        more efficient implementations.
        """
        log.debug("Checking if cloud credential works...")
        try:
            self.security.key_pairs.list()
            return True
        except Exception as e:
            log.exception("ProviderConnectionException occurred")
            raise ProviderConnectionException(
                "Authentication with cloud provider failed: %s" % (e,))

    def _deepgetattr(self, obj, attr):
        """Recurses through an attribute chain to get the ultimate value."""
        return functools.reduce(getattr, attr.split('.'), obj)

    def has_service(self, service_type):
        """
        Checks whether this provider supports a given service.

        :type service_type: str or :class:``.CloudServiceType``
        :param service_type: Type of service to check support for.

        :rtype: bool
        :return: ``True`` if the service type is supported.
        """
        log.info("Checking if provider supports %s", service_type)
        try:
            if self._deepgetattr(self, service_type):
                log.info("This provider supports %s",
                         service_type)
                return True
        except AttributeError:
            pass  # Undefined service type
        except NotImplementedError:
            pass  # service not implemented
        log.info("This provider doesn't support %s",
                 service_type)
        return False

    def _get_config_value(self, key, default_value):
        """
        A convenience method to extract a configuration value.

        :type key: str
        :param key: a field to look for in the ``self.config`` field

        :type default_value: anything
        :param default_value: the default value to return if a value for the
                              ``key`` is not available

        :return: a configuration value for the supplied ``key``
        """
        log.debug("Getting config key %s, with supplied default value: %s",
                  key, default_value)
        value = default_value
        if isinstance(self.config, dict) and self.config.get(key):
            value = self.config.get(key, default_value)
        elif hasattr(self.config, key) and getattr(self.config, key):
            value = getattr(self.config, key)
        elif (self._config_parser.has_option(self.PROVIDER_ID, key) and
              self._config_parser.get(self.PROVIDER_ID, key)):
            value = self._config_parser.get(self.PROVIDER_ID, key)
        if isinstance(value, six.string_types) and not isinstance(
                value, six.text_type):
            return six.u(value)
        return value
