import importlib


class ProviderList(object):
    AWS = 'aws'
    OPENSTACK = 'openstack'
    AZURE = 'azure'


class CloudProviderFactory(object):

    """
    Get info and handle on the available cloud provider implementations.
    """

    def list_providers(self):
        """
        Get a list of available providers.

        (This function could eventually be implemented as a registry file
        containing all available implementations, or alternatively, using
        automatic discovery.)

        :rtype: list
        :return: A list of available providers and their interface versions.
        """
        return [
            {"name": ProviderList.OPENSTACK,
             "implementations":
                [{"class":
                  "cloudbridge.providers.openstack.OpenStackCloudProviderV1",
                  "version": 1}]},
            {"name": ProviderList.AWS,
             "implementations":
                [{"class": "cloudbridge.providers.aws.AWSCloudProviderV1",
                  "mock_class":
                  "cloudbridge.providers.aws.MockAWSCloudProvider",
                  "version": 1}]}]

    def find_provider_impl(self, name, version=None, get_mock=False):
        """
        Finds a provider implementation class given its name.

        :type name: str
        :param name: A name of the provider whose implementation to look for.

        :type version: inst
        :param version: A specific version of the provider to look for. If the
                        version is not specified, return the latest available
                        version.

        :type get_mock: ``bool``
        :param get_mock: If True, returns a mock version of the provider
        if available, or the real version if not.

        :rtype: ``None`` or str
        :return: If found, return a module (including class name) of the
                 provider or ``None`` if the provider was not found.
        """
        for provider in self.list_providers():
            if provider['name'] == name:
                if version:
                    match = [item for item in provider["implementations"]
                             if item["version"] == version]
                    if match:
                        if get_mock and match[0].get("mock_class"):
                            return match[0]["mock_class"]
                        else:
                            return match[0]["class"]
                    else:
                        return None
                else:
                    # Return latest available version
                    latest_version = sorted(
                        (item for item in provider["implementations"]),
                        key=lambda x: x["version"])[-1]
                    if get_mock and latest_version.get("mock_class"):
                        return latest_version["mock_class"]
                    else:
                        return latest_version["class"]
        return None

    def create_provider(self, name, config, version=None):
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
        impl = self.find_provider_impl(name, version=version)
        if impl is None:
            raise NotImplementedError(
                'A provider by name {0} implementing interface v1 could not be'
                ' found'.format(name))
        provider_class = self._get_provider_class(impl)
        return provider_class(config)

    def _get_provider_class(self, impl):
        module_name, class_name = impl.rsplit(".", 1)
        provider_class = getattr(importlib.import_module(module_name),
                                 class_name)
        return provider_class

    def get_provider_class(self, name, version=None, get_mock=False):
        """
        Return a class for the requested provider.

        :type get_mock: ``bool``
        :param get_mock: If True, returns a mock version of the provider
        if available, or the real version if not.

        :rtype: provider class or ``None``
        :return: A class corresponding to the requested provider or ``None``
                 if the provider was not found.
        """
        provider_class = self.find_provider_impl(
            name,
            version,
            get_mock=get_mock)
        if provider_class:
            return self._get_provider_class(provider_class)
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
        for provider in self.list_providers():
            for impl in provider["implementations"]:
                if get_mock and impl.get("mock_class"):
                    all_providers.append(
                        self._get_provider_class(
                            impl["mock_class"]))
                else:
                    all_providers.append(
                        self._get_provider_class(
                            impl["class"]))
        return all_providers
