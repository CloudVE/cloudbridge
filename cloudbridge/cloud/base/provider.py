"""Base implementation of a provider interface."""
import functools
import os
from os.path import expanduser
try:
    from configparser import SafeConfigParser
except ImportError:  # Python 2
    from ConfigParser import SafeConfigParser

from cloudbridge.cloud.interfaces import CloudProvider
from cloudbridge.cloud.interfaces.exceptions import ProviderConnectionException
from cloudbridge.cloud.interfaces.resources import Configuration


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
        return self.get('default_result_limit', DEFAULT_RESULT_LIMIT)

    @property
    def default_wait_timeout(self):
        """
        Gets the default wait timeout for LifeCycleObjects.
        """
        return self.get('default_wait_timeout', DEFAULT_WAIT_TIMEOUT)

    @property
    def default_wait_interval(self):
        """
        Gets the default wait interval for LifeCycleObjects.
        """
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


class BaseCloudProvider(CloudProvider):

    def __init__(self, config):
        self._config = BaseConfiguration(config)
        self._config_parser = SafeConfigParser()
        self._config_parser.read(CloudBridgeConfigLocations)

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return str(self.__class__.__name__)

    def authenticate(self):
        """
        A basic implementation which simply runs a low impact command to
        check whether cloud credentials work. Providers should override with
        more efficient implementations.
        """
        try:
            self.security.key_pairs.list()
            return True
        except Exception as e:
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
        try:
            if self._deepgetattr(self, service_type):
                return True
        except AttributeError:
            pass  # Undefined service type
        except NotImplementedError:
            pass  # service not implemented
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
        if isinstance(self.config, dict) and self.config.get(key):
            return self.config.get(key, default_value)
        elif hasattr(self.config, key) and getattr(self.config, key):
            return getattr(self.config, key)
        elif (self._config_parser.has_option(self.PROVIDER_ID, key) and
              self._config_parser.get(self.PROVIDER_ID, key)):
            return self._config_parser.get(self.PROVIDER_ID, key)
        return default_value
