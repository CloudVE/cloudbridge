import importlib
import inspect
import logging
import pkgutil
from collections import defaultdict

from pyeventsystem.middleware import SimpleMiddlewareManager

from cloudbridge.cloud import providers
from cloudbridge.cloud.interfaces import CloudProvider
from cloudbridge.cloud.interfaces import TestMockHelperMixin


log = logging.getLogger(__name__)


# Todo: Move to pyeventsystem if we're keeping this logic
class ParentMiddlewareManager(SimpleMiddlewareManager):

    def __init__(self, event_manager=None):
        super(ParentMiddlewareManager, self).__init__(event_manager)
        self.middleware_constructors = []

    def add_constructor(self, middleware_class, *args):
        self.middleware_constructors.append((middleware_class, args))

    def remove_constructor(self, middleware_class, *args):
        self.middleware_constructors.remove((middleware_class, args))

    def generate_simple_manager(self):
        new_manager = SimpleMiddlewareManager()
        for middleware in self.middleware_list:
            new_manager.add(middleware)
        for constructor, args in self.middleware_constructors:
            m = constructor(*args)
            new_manager.add(m)
        return new_manager


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
        self._middleware = ParentMiddlewareManager()
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
        return provider_class(config, self.middleware)

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
