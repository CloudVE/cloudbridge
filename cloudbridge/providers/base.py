from cloudbridge.providers.interfaces import CloudProvider
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import SecurityGroup


class BaseCloudProvider(CloudProvider):

    def __init__(self, config):
        self.config = config

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
        if isinstance(self.config, dict):
            return self.config.get(key, default_value)
        else:
            return getattr(self.config, key) if hasattr(self.config, key) and getattr(self.config, key) else default_value


class BaseKeyPair(KeyPair):

    def __init__(self, name, material=None):
        self.name = name
        self.material = material

    def __repr__(self):
        return "<CBKeyPair: {0}>".format(self.name)

    # def name(self):
    #     """
    #     Return the name of this key pair.

    #     :rtype: str
    #     :return: A name of this ssh key pair
    #     """
    #     raise NotImplementedError(
    #         'name not implemented by this provider')


class BaseSecurityGroup(SecurityGroup):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<CBSecurityGroup: {0}>".format(self.name)
