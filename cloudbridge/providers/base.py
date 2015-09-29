"""
Implementation of common methods across cloud providers.
"""

from cloudbridge.providers.interfaces import CloudProvider
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import SecurityGroup


class BaseCloudProvider(CloudProvider):

    def __init__(self, config):
        self.config = config

    @property
    def name(self):
        return str(self.__class__.__name__)

    def has_service(self, service_type):
        """
        Checks whether this provider supports a given service.

        :type service_type: str or :class:``.CloudProviderServiceType``
        :param service_type: Type of service to check support for.

        :rtype: bool
        :return: ``True`` if the service type is supported.
        """
        try:
            if getattr(self, service_type):
                return True
        except AttributeError:
            pass  # Undefined service type
        return False

    def _get_config_value(self, key, default_value):
        """
        A convenience method to extract a configuration value.

        :type key: str
        :param key: a field to look for in the ``self.config`` field

        :type default_value: anything
        : param default_value: the default value to return if a value for the
                               ``key`` is not available

        :return: a configuration value for the supplied ``key``
        """
        if isinstance(self.config, dict):
            return self.config.get(key, default_value)
        else:
            return getattr(self.config, key) if hasattr(
                self.config, key) and getattr(self.config, key) else default_value


class BaseKeyPair(KeyPair):

    def __init__(self, name, material=None):
        self.name = name
        self.material = material

    def __repr__(self):
        return "<CBKeyPair: {0}>".format(self.name)


class BaseSecurityGroup(SecurityGroup):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<CBSecurityGroup: {0}>".format(self.name)
