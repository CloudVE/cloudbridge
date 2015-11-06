"""
Implementation of common methods across cloud providers.
"""

import logging
import time

import six

from cloudbridge.cloud.interfaces import CloudProvider
from cloudbridge.cloud.interfaces.resources \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import Instance
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import InstanceType
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import LaunchConfig
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import ObjectLifeCycleMixin
from cloudbridge.cloud.interfaces.resources import Region
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.interfaces.resources import SecurityGroupRule
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import Volume
from cloudbridge.cloud.interfaces.resources import VolumeState
from cloudbridge.cloud.interfaces.resources import WaitStateException
from cloudbridge.cloud.interfaces.services import BlockStoreService
from cloudbridge.cloud.interfaces.services import ComputeService
from cloudbridge.cloud.interfaces.services import ImageService
from cloudbridge.cloud.interfaces.services import InstanceService
from cloudbridge.cloud.interfaces.services import InstanceTypesService
from cloudbridge.cloud.interfaces.services import KeyPairService
from cloudbridge.cloud.interfaces.services import ObjectStoreService
from cloudbridge.cloud.interfaces.services import ProviderService
from cloudbridge.cloud.interfaces.services import RegionService
from cloudbridge.cloud.interfaces.services import SecurityGroupService
from cloudbridge.cloud.interfaces.services import SecurityService
from cloudbridge.cloud.interfaces.services import SnapshotService
from cloudbridge.cloud.interfaces.services import VolumeService


log = logging.getLogger(__name__)


class BaseCloudProvider(CloudProvider):

    def __init__(self, config):
        self._config = config

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        self._config = config

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

    def wait_for(self, target_states, terminal_states=None, timeout=600,
                 interval=5):
        assert timeout > 0
        assert timeout > interval

        end_time = time.time() + timeout
        while True:
            if self.state in target_states:
                log.debug(
                    "Object: {0} successfully reached target state:"
                    " {1}".format(self, self.state))
                return True
            elif self.state in terminal_states:
                raise WaitStateException(
                    "Object: {0} is in state: {1} which is a terminal state"
                    " and cannot be waited on.".format(self, self.state))
            else:
                log.debug(
                    "Object {0} is in state: {1}. Waiting another {2}"
                    " seconds to reach target state(s): {3}...".format(
                        self,
                        self.state,
                        int(end_time - time.time()),
                        target_states))
                time.sleep(interval)
                if time.time() > end_time:
                    raise WaitStateException(
                        "Waited too long for object: {0} to become ready. It's"
                        " still in state: {1}".format(self, self.state))
            self.refresh()

    def wait_till_ready(self, timeout=600, interval=5):
        self.wait_for(
            self.ready_states,
            self.terminal_states,
            timeout,
            interval)


class BaseInstanceType(InstanceType):

    @property
    def size_total_disk(self):
        return self.size_root_disk + self.size_ephemeral_disks

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__, self.name)


class BaseInstance(BaseObjectLifeCycleMixin, Instance):

    @property
    def ready_states(self):
        return [InstanceState.RUNNING]

    @property
    def terminal_states(self):
        return [InstanceState.TERMINATED, InstanceState.ERROR]


class BaseLaunchConfig(LaunchConfig):

    def __init__(self, provider):
        self.provider = provider
        self.block_devices = []
        self.net_ids = []

    class BlockDeviceMapping(object):
        """
        Represents a block device mapping
        """

        def __init__(self, is_volume=False, source=None, is_root=None,
                     size=None, delete_on_terminate=None):
            self.is_volume = is_volume
            self.source = source
            self.is_root = is_root
            self.size = size
            self.delete_on_terminate = delete_on_terminate

        def __repr__(self):
            return "<CB-{0}: Dest: {1}, Src: {2}, IsRoot: {3}, Size: {4}>" \
                .format(self.__class__.__name__,
                        "volume" if self.is_volume else "ephemeral",
                        self.source, self.is_root, self.size)

    def add_ephemeral_device(self):
        block_device = BaseLaunchConfig.BlockDeviceMapping()
        self.block_devices.append(block_device)

    def add_volume_device(self, source=None, is_root=None, size=None,
                          delete_on_terminate=None):
        block_device = self._validate_volume_device(
            source=source, is_root=is_root, size=size,
            delete_on_terminate=delete_on_terminate)
        self.block_devices.append(block_device)

    def _validate_volume_device(self, source=None, is_root=None,
                                size=None, delete_on_terminate=None):
        """
        Validates a volume based device and throws an
        InvalidConfigurationException if the configuration is incorrect.
        """
        if source is None and not size:
            raise InvalidConfigurationException(
                "A size must be specified for a blank new volume")

        if source and \
                not isinstance(source, (Snapshot, Volume, MachineImage)):
            raise InvalidConfigurationException(
                "Source must be a Snapshot, Volume, MachineImage or None")
        if size:
            if not isinstance(size, six.integer_types) or not size > 0:
                raise InvalidConfigurationException(
                    "The size must be None or a number greater than 0")

        if is_root:
            for bd in self.block_devices:
                if bd.is_root:
                    raise InvalidConfigurationException(
                        "An existing block device: {0} has already been"
                        " marked as root. There can only be one root device.")

        return BaseLaunchConfig.BlockDeviceMapping(
            is_volume=True, source=source, is_root=is_root, size=size,
            delete_on_terminate=delete_on_terminate)

    def add_network_interface(self, net_id):
        self.net_ids.append(net_id)


class BaseMachineImage(BaseObjectLifeCycleMixin, MachineImage):

    @property
    def ready_states(self):
        return [MachineImageState.AVAILABLE]

    @property
    def terminal_states(self):
        return [MachineImageState.ERROR]

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.name)


class BaseVolume(BaseObjectLifeCycleMixin, Volume):

    @property
    def ready_states(self):
        return [VolumeState.AVAILABLE]

    @property
    def terminal_states(self):
        return [VolumeState.ERROR, VolumeState.DELETED]


class BaseSnapshot(BaseObjectLifeCycleMixin, Snapshot):

    @property
    def ready_states(self):
        return [SnapshotState.AVAILABLE]

    @property
    def terminal_states(self):
        return [SnapshotState.ERROR]


class BaseKeyPair(KeyPair):

    def __init__(self, provider, key_pair):
        self._provider = provider
        self._key_pair = key_pair

    def __eq__(self, other):
        return isinstance(other, KeyPair) and \
            self._provider == other._provider and \
            self.name == other.name

    @property
    def name(self):
        """
        Return the name of this key pair.
        """
        return self._key_pair.name

    def delete(self):
        """
        Delete this KeyPair.

        :rtype: bool
        :return: True if successful, otherwise False.
        """
        # This implementation assumes the `delete` method exists across
        #  multiple providers.
        self._key_pair.delete()

    def __repr__(self):
        return "<CBKeyPair: {0}>".format(self.name)


class BaseSecurityGroup(SecurityGroup):

    def __init__(self, provider, security_group):
        self._provider = provider
        self._security_group = security_group

    def __eq__(self, other):
        """
        Check if all the defined rules match across both security groups.
        """
        return (isinstance(other, SecurityGroup) and
                self._provider == other._provider and
                len(self.rules) == len(other.rules) and  # Shortcut
                set(self.rules) == set(other.rules))

    def __ne__(self, other):
        return not self.__eq__(other)

    def rule_exists(self, rules, rule):
        """
        Check if an authorization rule exists in a list of rules.

        :type rules: list of :class:``.SecurityGroupRule``
        :param rules: A list of rules to check against

        :type rule: :class:``.SecurityGroupRule``
        :param rule: A rule whose existence to check for

        :rtype: bool
        :return: ``True`` if an existing rule matches the supplied rule;
                 ``False`` otherwise.
        """
        for r in rules:
            if r == rule:
                return True
        return False

    @property
    def id(self):
        """
        Get the ID of this security group.

        :rtype: str
        :return: Security group ID
        """
        return self._security_group.id

    @property
    def name(self):
        """
        Return the name of this security group.
        """
        return self._security_group.name

    @property
    def description(self):
        """
        Return the description of this security group.
        """
        return self._security_group.description

    def delete(self):
        """
        Delete this security group.
        """
        return self._security_group.delete()

    def __repr__(self):
        return "<CBSecurityGroup: {0}>".format(self.name)


class BaseSecurityGroupRule(SecurityGroupRule):

    def __init__(self, provider, rule, parent):
        self._provider = provider
        self._rule = rule
        self.parent = parent

    def __repr__(self):
        return "<CBSecurityGroupRule: IP: {0}; from: {1}; to: {2}>".format(
            self.ip_protocol, self.from_port, self.to_port)

    def __eq__(self, other):
        return self.ip_protocol == other.ip_protocol and \
            self.from_port == other.from_port and \
            self.to_port == other.to_port and \
            self.cidr_ip == other.cidr_ip

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        """
        Return a hash-based interpretation of all of the object's field values.

        This is requried for operations on hashed collections including
        ``set``, ``frozenset``, and ``dict``.
        """
        return hash("{0}{1}{2}{3}{4}".format(self.ip_protocol, self.from_port,
                                             self.to_port, self.cidr_ip,
                                             self.group))


class BaseRegion(Region):

    def __init__(self, provider, region):
        self._provider = provider
        self._region = region

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.name)

    def __eq__(self, other):
        if isinstance(other, Region):
            return self._provider == other._provider and \
                self.id == other.id


class BaseProviderService(ProviderService):

    def __init__(self, provider):
        self._provider = provider

    @property
    def provider(self):
        return self._provider


class BaseComputeService(ComputeService, BaseProviderService):

    def __init__(self, provider):
        super(BaseComputeService, self).__init__(provider)


class BaseVolumeService(VolumeService, BaseProviderService):

    def __init__(self, provider):
        super(BaseVolumeService, self).__init__(provider)


class BaseSnapshotService(SnapshotService, BaseProviderService):

    def __init__(self, provider):
        super(BaseSnapshotService, self).__init__(provider)


class BaseBlockStoreService(BlockStoreService, BaseProviderService):

    def __init__(self, provider):
        super(BaseBlockStoreService, self).__init__(provider)


class BaseImageService(ImageService, BaseProviderService):

    def __init__(self, provider):
        super(BaseImageService, self).__init__(provider)


class BaseObjectStoreService(ObjectStoreService, BaseProviderService):

    def __init__(self, provider):
        super(BaseObjectStoreService, self).__init__(provider)


class BaseSecurityService(SecurityService, BaseProviderService):

    def __init__(self, provider):
        super(BaseSecurityService, self).__init__(provider)


class BaseKeyPairService(KeyPairService, BaseProviderService):

    def __init__(self, provider):
        super(BaseKeyPairService, self).__init__(provider)


class BaseSecurityGroupService(SecurityGroupService, BaseProviderService):

    def __init__(self, provider):
        super(BaseSecurityGroupService, self).__init__(provider)


class BaseInstanceTypesService(InstanceTypesService, BaseProviderService):

    def __init__(self, provider):
        super(BaseInstanceTypesService, self).__init__(provider)

    def find(self, **kwargs):
        name = kwargs.get('name')
        if name:
            return (itype for itype in self.list() if itype.name == name)
        else:
            return None


class BaseInstanceService(InstanceService, BaseProviderService):

    def __init__(self, provider):
        super(BaseInstanceService, self).__init__(provider)


class BaseRegionService(RegionService, BaseProviderService):

    def __init__(self, provider):
        super(BaseRegionService, self).__init__(provider)
