import importlib
import inspect
import logging
import pkgutil
from collections import defaultdict

from pyeventsystem.events import SimpleEventDispatcher
from pyeventsystem.interfaces import Middleware
from pyeventsystem.middleware import AutoDiscoveredMiddleware
from pyeventsystem.middleware import SimpleMiddlewareManager

from cloudbridge.cloud import providers
from cloudbridge.cloud.interfaces import CloudProvider
from cloudbridge.cloud.interfaces import TestMockHelperMixin


log = logging.getLogger(__name__)


# Todo: Move to pyeventsystem if we're keeping this logic
class ParentMiddlewareGenerator(SimpleMiddlewareManager):

    def __init__(self, event_manager=None):
        super(ParentMiddlewareGenerator, self).__init__(event_manager)
        self.middleware_constructors = []

    def add_middleware_class(self, middleware_class, *args, **kwargs):
        self.middleware_constructors.append((middleware_class, args, kwargs))

    def remove_middleware_class(self, middleware_class, *args, **kwargs):
        self.middleware_constructors.remove((middleware_class, args, kwargs))

    def get_directly_subscribed_handlers(self):
        all_handlers = []
        # Todo: Expose this better in pyeventsystem library
        event_dict = self.events._SimpleEventDispatcher__events
        for key in event_dict.keys():
            for h in event_dict[key]:
                all_handlers.append((h,
                                     h.event_pattern,
                                     h.priority,
                                     h.callback))
        middleware_handlers = []
        for m in self.middleware_list:
            obj = (m.obj_to_discover if isinstance(m, AutoDiscoveredMiddleware)
                   else m)
            handlers = m.discover_handlers(obj)
            for h in handlers:
                middleware_handlers.append((h.event_pattern, h.priority,
                                            h.callback))
        direct_subs = [h for h, e, p, c in all_handlers
                       if (e, p, c) not in middleware_handlers]
        return direct_subs

    def generate_child_manager(self, namespace=None):
        event_dispatcher = None
        if namespace:
            event_dispatcher = NamespacedEventDispatcher(namespace)
        manager = ChildMiddlewareManager(self, event_dispatcher)
        manager.inherit_handlers()
        return manager


# TODO: Move to pyeventsystem if we're keeping
class NamespacedEventDispatcher(SimpleEventDispatcher):

    def __init__(self, namespace):
        super(NamespacedEventDispatcher, self).__init__()
        self._namespace = namespace

    @property
    def namespace(self):
        return self._namespace

    def get_handlers_for_event(self, event):
        event = ".".join((self._namespace, event))
        return self.get_handlers_for_event_direct(event)

    def _create_handler_cache(self, event):
        event = ".".join((self._namespace, event))
        return self._create_handler_cache_direct(event)

    def _invalidate_cache(self, event_pattern):
        event_pattern = ".".join((self._namespace, event_pattern))
        return self._invalidate_cache_direct(event_pattern)

    def dispatch(self, sender, event, *args, **kwargs):
        event = ".".join((self._namespace, event))
        return self.dispatch_direct(sender, event, *args, **kwargs)

    def observe(self, event_pattern, priority, callback):
        event_pattern = ".".join((self._namespace, event_pattern))
        return self.observe_direct(event_pattern, priority, callback)

    def intercept(self, event_pattern, priority, callback):
        event_pattern = ".".join((self._namespace, event_pattern))
        return self.intercept_direct(event_pattern, priority, callback)

    def implement(self, event_pattern, priority, callback):
        event_pattern = ".".join((self._namespace, event_pattern))
        return self.implement_direct(event_pattern, priority, callback)

    def observe_direct(self, event_pattern, priority, callback):
        return super(NamespacedEventDispatcher, self).observe(event_pattern,
                                                              priority,
                                                              callback)

    def intercept_direct(self, event_pattern, priority, callback):
        return super(NamespacedEventDispatcher, self).intercept(event_pattern,
                                                                priority,
                                                                callback)

    def implement_direct(self, event_pattern, priority, callback):
        return super(NamespacedEventDispatcher, self).implement(event_pattern,
                                                                priority,
                                                                callback)

    def dispatch_direct(self, sender, event, *args, **kwargs):
        return super(NamespacedEventDispatcher, self).dispatch(sender, event,
                                                               *args, **kwargs)

    def get_handlers_for_event_direct(self, event):
        return super(NamespacedEventDispatcher, self).get_handlers_for_event(
            event)

    def _create_handler_cache_direct(self, event):
        return super(NamespacedEventDispatcher, self)._create_handler_cache(
            event)

    def _invalidate_cache_direct(self, event_pattern):
        return super(NamespacedEventDispatcher, self)._invalidate_cache(
            event_pattern)


# TODO: Move to pyeventsystem if we're keeping
class ChildMiddlewareManager(SimpleMiddlewareManager):

    def __init__(self, parent_manager, event_manager=None):
        super(ChildMiddlewareManager, self).__init__(event_manager)
        self._parent_manager = parent_manager
        self._inherited = {}

    def inherit_handlers(self):
        self.remove_inherited_handlers()
        middleware_list = []
        for middleware in self._parent_manager.middleware_list:
            added = self.add_direct(middleware)
            middleware_list.append(added)
        for constructor, args, kwargs in (self._parent_manager
                                              .middleware_constructors):
            m = constructor(*args, **kwargs)
            added = self.add_direct(m)
            middleware_list.append(added)
        self._inherited['middleware_list'] = middleware_list
        handler_list = []
        for handler in self._parent_manager.get_directly_subscribed_handlers():
            new_handler = handler.__class__(handler.event_pattern,
                                            handler.priority,
                                            handler.callback)
            handler_list.append(new_handler)
            self.events.subscribe(new_handler)
        self._inherited['handler_list'] = handler_list

    def remove_inherited_handlers(self):
        for m in self._inherited.get("middleware_list", []):
            self.remove(m)

        for h in self._inherited.get("handler_list", []):
            self.events.unsubscribe(h)

        self._inherited = {}

    @property
    def parent_manager(self):
        return self._parent_manager

    def add_direct(self, middleware):
        return super(ChildMiddlewareManager, self).add(middleware)

    def add(self, middleware):
        if isinstance(middleware, Middleware):
            m = middleware
            m.events = self.events
            discovered_handlers = m.discover_handlers(m)
        else:
            m = AutoDiscoveredMiddleware(middleware)
            m.events = self.events
            discovered_handlers = m.discover_handlers(m.obj_to_discover)

        # Rewrap handlers with namespaced event pattern if the event dispatcher
        # is namespaced
        if isinstance(self.events, NamespacedEventDispatcher):
            for handler in discovered_handlers:
                event_pattern = ".".join((self.events.namespace,
                                         handler.event_pattern))
                new_handler = handler.__class__(event_pattern,
                                                handler.priority,
                                                handler.callback)
                discovered_handlers.remove(handler)
                discovered_handlers.append(new_handler)
        m.add_handlers(discovered_handlers)
        self.middleware_list.append(m)
        return m


class ProviderList(object):
    AWS = 'aws'
    AZURE = 'azure'
    GCP = 'gcp'
    OPENSTACK = 'openstack'
    MOCK = 'mock'


class CloudProviderFactory(object):

    """
    Get info and handle on the available cloud provider implementations.
    """

    def __init__(self):
        self._middleware = ParentMiddlewareGenerator()
        self.provider_list = defaultdict(dict)
        log.debug("Providers List: %s", self.provider_list)

    @property
    def middleware(self):
        return self._middleware

    def register_provider_class(self, cls):
        """
        Registers a provider class with the factory. The class must
        inherit from cloudbridge.cloud.interfaces.CloudProvider
        and also have a class attribute named PROVIDER_ID.

        The PROVIDER_ID is a user friendly name for the cloud provider,
        such as 'aws'. The PROVIDER_ID must also be included in the
        cloudbridge.factory.ProviderList.

        :type  cls: class
        :param cls: A class implementing the CloudProvider interface.
                    Mock providers must also implement
                    :py:class:`cloudbridge.cloud.base.helpers.
                    TestMockHelperMixin`.
        """
        if isinstance(cls, type) and issubclass(cls, CloudProvider):
            if hasattr(cls, "PROVIDER_ID"):
                provider_id = getattr(cls, "PROVIDER_ID")
                if self.provider_list.get(provider_id, {}).get('class'):
                    log.warning("Provider with id: %s is already "
                                "registered. Overriding with class: %s",
                                provider_id, cls)
                self.provider_list[provider_id]['class'] = cls
            else:
                log.warning("Provider class: %s implements CloudProvider but"
                            " does not define PROVIDER_ID. Ignoring...", cls)
        else:
            log.debug("Class: %s does not implement the CloudProvider"
                      "  interface. Ignoring...", cls)

    def discover_providers(self):
        """
        Discover all available providers within the
        ``cloudbridge.cloud.providers`` package.
        Note that this methods does not guard against a failed import.
        """
        for _, modname, _ in pkgutil.iter_modules(providers.__path__):
            log.debug("Importing provider: %s", modname)
            try:
                self._import_provider(modname)
            except Exception as e:
                log.warn("Could not import provider: %s", e)

    def _import_provider(self, module_name):
        """
        Imports and registers providers from the given module name.
        Raises an ImportError if the import does not succeed.
        """
        log.debug("Importing providers from %s", module_name)
        module = importlib.import_module(
            "{0}.{1}".format(providers.__name__,
                             module_name))
        classes = inspect.getmembers(module, inspect.isclass)
        for _, cls in classes:
            log.debug("Registering the provider: %s", cls)
            self.register_provider_class(cls)

    def list_providers(self):
        """
        Get a list of available providers.

        It uses a simple automatic discovery system by iterating through all
        submodules in cloudbridge.cloud.providers.

        :rtype: dict
        :return: A dict of available providers and their implementations in the
                 following format::
                 {'aws': {'class': aws.provider.AWSCloudProvider},
                  'openstack': {'class': openstack.provider.OpenStackCloudProvi
                                         der}
                 }
        """
        if not self.provider_list:
            self.discover_providers()
        log.debug("List of available providers: %s", self.provider_list)
        return self.provider_list

    def create_provider(self, name, config):
        """
        Searches all available providers for a CloudProvider interface with the
        given name, and instantiates it based on the given config dictionary,
        where the config dictionary is a dictionary understood by that
        cloud provider.

        :type name: str
        :param name: Cloud provider name: one of ``aws``, ``openstack``,
        ``azure``.

        :type config: :class:`dict`
        :param config: A dictionary or an iterable of key/value pairs (as
                       tuples or other iterables of length two). See specific
                       provider implementation for the required fields.

        :return:  a concrete provider instance
        :rtype: ``object`` of :class:`.CloudProvider`
        """
        log.info("Creating '%s' provider", name)
        provider_class = self.get_provider_class(name)
        if provider_class is None:
            log.exception("A provider with the name %s could not "
                          "be found", name)
            raise NotImplementedError(
                'A provider with name {0} could not be'
                ' found'.format(name))
        log.debug("Created '%s' provider", name)
        namespaced_middleware = self.middleware.generate_child_manager(name)
        return provider_class(config,
                              namespaced_middleware)

    def get_provider_class(self, name):
        """
        Return a class for the requested provider.

        :rtype: provider class or ``None``
        :return: A class corresponding to the requested provider or ``None``
                 if the provider was not found.
        """
        log.debug("Returning a class for the %s provider", name)
        impl = self.list_providers().get(name)
        if impl:
            log.debug("Returning provider class for %s", name)
            return impl["class"]
        else:
            log.debug("Provider with the name: %s not found", name)
            return None

    def get_all_provider_classes(self, ignore_mocks=False):
        """
        Returns a list of classes for all available provider implementations

        :type ignore_mocks: ``bool``
        :param ignore_mocks: If True, does not return mock providers. Mock
        providers are providers which implement the TestMockHelperMixin.

        :rtype: type ``class`` or ``None``
        :return: A list of all available provider classes or an empty list
        if none found.
        """
        all_providers = []
        for impl in self.list_providers().values():
            if ignore_mocks:
                if not issubclass(impl["class"], TestMockHelperMixin):
                    all_providers.append(impl["class"])
            else:
                all_providers.append(impl["class"])
        log.info("List of provider classes: %s", all_providers)
        return all_providers
