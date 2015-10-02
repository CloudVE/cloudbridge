"""
Implementation of common methods across cloud providers.
"""

import logging
import time

from cloudbridge.providers.interfaces import CloudProvider
from cloudbridge.providers.interfaces import Instance
from cloudbridge.providers.interfaces import InstanceState
from cloudbridge.providers.interfaces import InstanceWaitException
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import MachineImageState
from cloudbridge.providers.interfaces import MachineImageWaitException
from cloudbridge.providers.interfaces import SecurityGroup


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
                self.config, key) and getattr(self.config, key) else default_value


class BaseInstance(Instance):

    @property
    def ready_states(self):
        return [InstanceState.RUNNING]

    @property
    def terminal_states(self):
        return [InstanceState.TERMINATED, InstanceState.ERROR]

    def wait_till_ready(self, timeout=600, interval=5):
        assert timeout > 0
        assert timeout > interval
        assert interval > 0

        for time_left in range(timeout, 0, -interval):
            state = self.instance_state
            if state in self.ready_states:
                return True
            elif state in self.terminal_states:
                raise InstanceWaitException(
                    "Instance is in state: {0} which is a terminal state and cannot be waited on.".format(state))
            else:
                log.debug(
                    "Instance is in state '{0}'. Waiting another {1} seconds to reach state a ready state...".format(
                        state,
                        time_left))
                time.sleep(interval)
            self.refresh()

        raise InstanceWaitException(
            "Waited too long for instance to become ready. Instance Id: %s is in state: %s".format(
                self.instance_id,
                self.name,
                self.instance_state))


class BaseMachineImage(MachineImage):

    @property
    def ready_states(self):
        return [MachineImageState.AVAILABLE]

    @property
    def terminal_states(self):
        return [MachineImageState.ERROR]

    def wait_till_ready(self, timeout=600, interval=5):
        assert timeout > 0
        assert timeout > interval
        assert interval > 0

        for time_left in range(timeout, 0, -interval):
            state = self.image_state
            if state in self.ready_states:
                return True
            elif state in self.terminal_states:
                raise MachineImageWaitException(
                    "Image is in state: {0} which is a terminal state and cannot be waited on.".format(state))
            else:
                log.debug(
                    "Image is in state '{0}'. Waiting another {1} seconds to reach state a ready state...".format(
                        state,
                        time_left))
                time.sleep(interval)
            self.refresh()

        raise MachineImageWaitException(
            "Waited too long for image to become ready. Image Id: %s is still in state: %s".format(
                self.image_id,
                self.name,
                self.image_state))


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
