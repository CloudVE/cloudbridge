"""
Base implementation of a provider interface
"""
import os

from cloudbridge.cloud.interfaces import CloudProvider
from cloudbridge.cloud.interfaces.resources import Configuration

DEFAULT_RESULT_LIMIT = 50
DEFAULT_WAIT_TIMEOUT = 600
DEFAULT_WAIT_INTERVAL = 5


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

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return str(self.__class__.__name__)

    def has_service(self, service_type):
        """
        Checks whether this provider supports a given service.

        :type service_type: str or :class:``.CloudServiceType``
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
        :param default_value: the default value to return if a value for the
                              ``key`` is not available

        :return: a configuration value for the supplied ``key``
        """
        if isinstance(self.config, dict):
            return self.config.get(key, default_value)
        else:
            return getattr(self.config, key) if hasattr(
                self.config, key) and getattr(self.config, key) else \
                default_value
