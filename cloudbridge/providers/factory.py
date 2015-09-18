import importlib

class ProviderList():
    EC2 = 'ec2'
    OPENSTACK = 'openstack'
    AZURE = 'azure'

class CloudProviderFactory():
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
        return [{"name": "openstack",
                 "implementation":
                 [{"class": "cloudbridge.providers.openstack.OpenstackCloudProviderV1",
                   "version": 1}]},
                {"name": "ec2",
                 "implementation":
                 [{"class": "cloudbridge.providers.ec2.EC2CloudProviderV1",
                   "version": 1}]}]

    def find_provider_impl(self, name, version=None):
        """
        Finds a provider implementation class given its name.

        :type name: str
        :param name: A name of the provider whose implementation to look for.

        :type version: inst
        :param version: A specific version of the provider to look for. If the
                        version is not specified, return the latest available
                        version.

        :rtype: ``None`` or str
        :return: If found, return a module (including class name) of the
                 provider or ``None`` if the provider was not found.
        """
        for provider in self.list_providers():
            if provider['name'] == name:
                if version:
                    match = [item for item in provider["implementation"]
                             if item["version"] == version]
                    if match:
                        return match[0]["class"]
                    else:
                        return None
                else:
                    # Return latest available version
                    return sorted((item for item in provider["implementation"]),
                                  key=lambda x: x["version"])[-1]["class"]
        return None

    def create_provider(self, name, config, version=None):
        """
        Searches all available providers for a CloudProvider interface with the
        given name, and instantiates it based on the given config dictionary,
        where the config dictionary is a dictionary understood by that
        cloud provider.

        :type name: str
        :param name: Cloud provider name: one of ``ec2``, ``openstack``.

        :type config: an object with required fields
        :param config: This can be a Bunch or any other object whose fields can
                       be accessed using dot notation. See specific provider
                       implementation for the required fields.

        :return:  a concrete provider instance
        :rtype: ``object`` of :class:`.CloudProviderV1`
        """
        provider = self.find_provider_impl(name, version=version)
        if provider is None:
            raise NotImplementedError(
                'A provider by name {0} implementing interface v1 could not be '
                'found'.format(name))
        else:
            module_name, class_name = provider.rsplit(".", 1)
            provider_class = getattr(importlib.import_module(module_name),
                                     class_name)
            return provider_class(config)