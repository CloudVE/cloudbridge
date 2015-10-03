"""
Implementation of common methods across cloud providers.
"""

import logging
import time

from cloudbridge.providers.interfaces import CloudProvider
from cloudbridge.providers.interfaces import Instance
from cloudbridge.providers.interfaces import InstanceState
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import MachineImageState
from cloudbridge.providers.interfaces import ObjectLifeCycleMixin
from cloudbridge.providers.interfaces import SecurityGroup
from cloudbridge.providers.interfaces import WaitStateException


log = logging.getLogger(__name__)


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
                self.config, key) and getattr(self.config, key) else \
                default_value


class BaseObjectLifeCycleMixin(ObjectLifeCycleMixin):
    """
    A base implementation of an ObjectLifeCycleMixin.
    This base implementation has an implementation of wait_till_ready
    which refreshes the object's state till the desired ready states
    are reached. Subclasses must implement two new properties - ready_states
    and terminal_states, which return a list of states to wait for.
    """
    @property
    def ready_states(self):
        raise NotImplementedError(
            "ready_states not implemented by this object. Subclasses must"
            " implement this method and return a valid set of ready states")

    @property
    def terminal_states(self):
        raise NotImplementedError(
            "terminal_states not implemented by this object. Subclasses must"
            " implement this method and return a valid set of terminal states")

    def wait_till_ready(self, timeout=600, interval=5):
        assert timeout > 0
        assert timeout > interval
        assert interval > 0

        for time_left in range(timeout, 0, -interval):
            if self.state in self.ready_states:
                return True
            elif self.state in self.terminal_states:
                raise WaitStateException(
                    "Object: {0} is in state: {1} which is a terminal state"
                    " and cannot be waited on.".format(self, self.state))
            else:
                log.debug(
                    "Object {0} is in state: {1}. Waiting another {2} seconds"
                    " to reach state a ready state...".format(
                        self,
                        self.state,
                        time_left))
                time.sleep(interval)
            self.refresh()

        raise WaitStateException("Waited too long for object: {0} to become"
                                 " ready. It's still  in state: {1}".format(
                                     self, self.state))


class BaseInstance(BaseObjectLifeCycleMixin, Instance):

    @property
    def ready_states(self):
        return [InstanceState.RUNNING]

    @property
    def terminal_states(self):
        return [InstanceState.TERMINATED, InstanceState.ERROR]


class BaseMachineImage(BaseObjectLifeCycleMixin, MachineImage):

    @property
    def ready_states(self):
        return [MachineImageState.AVAILABLE]

    @property
    def terminal_states(self):
        return [MachineImageState.ERROR]


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
