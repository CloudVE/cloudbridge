import importlib
import inspect
import logging
import pkgutil
from collections import defaultdict

from cloudbridge.cloud import providers
from cloudbridge.cloud.interfaces import CloudProvider
from cloudbridge.cloud.interfaces import TestMockHelperMixin


log = logging.getLogger(__name__)


class ProviderList(object):
    AWS = 'aws'
    OPENSTACK = 'openstack'
    AZURE = 'azure'


class CloudProviderFactory(object):

    """
    Get info and handle on the available cloud provider implementations.
    """

    def __init__(self):
        self.provider_list = defaultdict(dict)
        log.debug("Providers List: %s", self.provider_list)

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
                if issubclass(cls, TestMockHelperMixin):
                    if self.provider_list.get(provider_id, {}).get(
                            'mock_class'):
                        log.warning("Mock provider with id: %s is already "
                                    "registered. Overriding with class: %s",
                                    provider_id, cls)
                    self.provider_list[provider_id]['mock_class'] = cls
                else:
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
            self._import_provider(modname)

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
                 {'aws': {'class': aws.provider.AWSCloudProvider,
                          'mock_class': aws.provider.MockAWSCloudProvider},
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
        :param name: Cloud provider name: one of ``aws``, ``openstack``.

        :type config: an object with required fields
        :param config: This can be a Bunch or any other object whose fields can
                       be accessed using dot notation. See specific provider
                       implementation for the required fields.

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
        return provider_class(config)

    def get_provider_class(self, name, get_mock=False):
        """
        Return a class for the requested provider.

        :type get_mock: ``bool``
        :param get_mock: If True, returns a mock version of the provider
        if available, or the real version if not.

        :rtype: provider class or ``None``
        :return: A class corresponding to the requested provider or ``None``
                 if the provider was not found.
        """
        log.debug("Returning a class for the %s provider", name)
        impl = self.list_providers().get(name)
        if impl:
            if get_mock and impl.get("mock_class"):
                log.debug("param get_mock set to True, returning "
                          "a mock version of the provider %s", name)
                return impl["mock_class"]
            else:
                log.debug("Returning the real version of %s", name)
                return impl["class"]
        else:
            log.debug("Provider with the name: %s not found", name)
            return None

    def get_all_provider_classes(self, get_mock=False):
        """
        Returns a list of classes for all available provider implementations

        :type get_mock: ``bool``
        :param get_mock: If True, returns a mock version of the provider
        if available, or the real version if not.

        :rtype: type ``class`` or ``None``
        :return: A list of all available provider classes or an empty list
        if none found.
        """
        all_providers = []
        for impl in self.list_providers().values():
            if get_mock and impl.get("mock_class"):
                log.debug("param get_mock set to True, appending "
                          "a mock version of the provider %s", impl)
                all_providers.append(impl["mock_class"])
            else:
                all_providers.append(impl["class"])
        log.info("List of provider classes: %s", all_providers)
        return all_providers
