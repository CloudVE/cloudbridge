"""Base implementation of a provider interface."""
import ast
import functools
import logging
import os
from configparser import ConfigParser
from os.path import expanduser
from typing import Any
from typing import cast

from pyeventsystem.middleware import MiddlewareManager
from pyeventsystem.middleware import SimpleMiddlewareManager

from ..base.middleware import ExceptionWrappingMiddleware
from ..interfaces import CloudProvider
from ..interfaces.exceptions import ProviderConnectionException
from ..interfaces.resources import Configuration
from ..interfaces.resources import PlacementZone
from ..interfaces.resources import Region

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

    def __init__(self, user_config: dict[str, Any]) -> None:
        self.update(user_config)

    @property
    def default_result_limit(self) -> int:
        """
        Get the maximum number of results to return for a
        list method

        :rtype: ``int``
        :return: The maximum number of results to return
        """
        log.debug("Maximum number of results for list methods %s",
                  DEFAULT_RESULT_LIMIT)
        return cast(int, self.get('default_result_limit', DEFAULT_RESULT_LIMIT))

    @property
    def default_wait_timeout(self) -> int:
        """
        Gets the default wait timeout for LifeCycleObjects.
        """
        log.debug("Default wait timeout for LifeCycleObjects %s",
                  DEFAULT_WAIT_TIMEOUT)
        return cast(int, self.get('default_wait_timeout',
                                  DEFAULT_WAIT_TIMEOUT))

    @property
    def default_wait_interval(self) -> int:
        """
        Gets the default wait interval for LifeCycleObjects.
        """
        log.debug("Default wait interfal for LifeCycleObjects %s",
                  DEFAULT_WAIT_INTERVAL)
        return cast(int, self.get('default_wait_interval',
                                  DEFAULT_WAIT_INTERVAL))

    @property
    def debug_mode(self) -> bool:
        """
        A flag indicating whether CloudBridge is in debug mode. Setting
        this to True will cause the underlying provider's debug
        output to be turned on.

        The flag can be toggled by sending in the cb_debug value via
        the config dictionary, or setting the CB_DEBUG environment variable.

        :rtype: ``bool``
        :return: Whether debug mode is on.
        """
        return cast(bool, self.get('cb_debug',
                                   os.environ.get('CB_DEBUG', False)))


class BaseCloudProvider(CloudProvider):

    PROVIDER_ID: str

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = BaseConfiguration(config)
        self._config_parser = ConfigParser()
        self._config_parser.read(CloudBridgeConfigLocations)
        self._middleware = SimpleMiddlewareManager()
        self.add_required_middleware()
        self._region_name: str | None = None
        self._zone_name: str | None = None

    @property
    def region_name(self) -> str:
        return cast(str, self._region_name)

    @property
    def zone_name(self) -> str | None:
        if not self._zone_name:
            region = self.compute.regions.current
            # ``default_zone`` is provided by the concrete Region
            # implementation rather than the public Region interface.
            zone = cast("PlacementZone | None",
                        getattr(cast(Region, region), 'default_zone'))
            self._zone_name = zone.name if zone else None
            return self._zone_name
        else:
            try:
                zone_dict = ast.literal_eval(self._zone_name)
                if isinstance(zone_dict, dict):
                    return cast("str | None", zone_dict)
            except (ValueError, SyntaxError):
                pass
            return self._zone_name

    @property
    def config(self) -> Configuration:
        return self._config

    @property
    def name(self) -> str:
        return str(self.__class__.__name__)

    @property
    def middleware(self) -> MiddlewareManager:
        return self._middleware

    def add_required_middleware(self) -> None:
        """
        Adds common middleware that is essential for cloudbridge to function.
        Any other extra middleware can be added through the provider factory.
        """
        self.middleware.add(ExceptionWrappingMiddleware())

    def authenticate(self) -> bool:
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

    def clone(self, zone: PlacementZone | None = None) -> CloudProvider:
        cloned_config = self.config.copy()
        cloned_provider = self.__class__(cloned_config)
        if zone:
            # pylint:disable=protected-access
            cloned_provider._zone_name = zone.name
        return cloned_provider

    def _deepgetattr(self, obj: object, attr: str) -> Any:
        """Recurses through an attribute chain to get the ultimate value."""
        return functools.reduce(getattr, attr.split('.'), obj)

    def has_service(self, service_type: str) -> bool:
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

    def _get_config_value(self, key: str,
                          default_value: Any = None) -> Any:
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
        return value
