"""
Base implementation for data objects exposed through a provider or service
"""
import inspect
import itertools
import json
import logging
import os
import shutil
import time

from cloudbridge.cloud.interfaces.exceptions \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces.exceptions import WaitStateException
from cloudbridge.cloud.interfaces.resources import AttachmentInfo
from cloudbridge.cloud.interfaces.resources import Bucket
from cloudbridge.cloud.interfaces.resources import BucketObject
from cloudbridge.cloud.interfaces.resources import CloudResource
from cloudbridge.cloud.interfaces.resources import FloatingIP
from cloudbridge.cloud.interfaces.resources import Instance
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import InstanceType
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import LaunchConfig
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import ObjectLifeCycleMixin
from cloudbridge.cloud.interfaces.resources import PageableObjectMixin
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import Region
from cloudbridge.cloud.interfaces.resources import ResultList
from cloudbridge.cloud.interfaces.resources import Router
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.interfaces.resources import SecurityGroupRule
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import Subnet
from cloudbridge.cloud.interfaces.resources import Volume
from cloudbridge.cloud.interfaces.resources import VolumeState

import six

log = logging.getLogger(__name__)


class BaseCloudResource(CloudResource):

    def __init__(self, provider):
        self.__provider = provider

    @property
    def _provider(self):
        return self.__provider

    def to_json(self):
        # Get all attributes but filter methods and private/magic ones
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        return json.dumps(js, sort_keys=True)


class BaseObjectLifeCycleMixin(ObjectLifeCycleMixin):
    """
    A base implementation of an ObjectLifeCycleMixin.
    This base implementation has an implementation of wait_for
    which refreshes the object's state till the desired ready states
    are reached. Subclasses must still implement the wait_till_ready
    method, since the desired ready states are object specific.
    """

    def wait_for(self, target_states, terminal_states=None, timeout=None,
                 interval=None):
        if timeout is None:
            timeout = self._provider.config.default_wait_timeout
        if interval is None:
            interval = self._provider.config.default_wait_interval

        assert timeout >= 0
        assert interval >= 0
        assert timeout >= interval

        end_time = time.time() + timeout

        while self.state not in target_states:
            if self.state in (terminal_states or []):
                raise WaitStateException(
                    "Object: {0} is in state: {1} which is a terminal state"
                    " and cannot be waited on.".format(self, self.state))
            else:
                log.debug(
                    "Object %s is in state: %s. Waiting another %s"
                    " seconds to reach target state(s): %s...",
                    self,
                    self.state,
                    int(end_time - time.time()),
                    target_states)
                time.sleep(interval)
                if time.time() > end_time:
                    raise WaitStateException(
                        "Waited too long for object: {0} to become ready. It's"
                        " still in state: {1}".format(self, self.state))
            self.refresh()
        log.debug("Object: %s successfully reached target state: %s",
                  self, self.state)
        return True


class BaseResultList(ResultList):

    def __init__(
            self, is_truncated, marker, supports_total, total=None, data=None):
        # call list constructor
        super(BaseResultList, self).__init__(data or [])
        self._marker = marker
        self._is_truncated = is_truncated
        self._supports_total = True if supports_total else False
        self._total = total

    @property
    def marker(self):
        return self._marker

    @property
    def is_truncated(self):
        return self._is_truncated

    @property
    def supports_total(self):
        return self._supports_total

    @property
    def total_results(self):
        return self._total


class ServerPagedResultList(BaseResultList):
    """
    This is a convenience class that extends the :class:`BaseResultList` class
    and provides a server side implementation of paging. It is meant for use by
    provider developers and is not meant for direct use by end-users.
    This class can be used to wrap a partial result list when an operation
    supports server side paging.
    """

    @property
    def supports_server_paging(self):
        return True

    @property
    def data(self):
        raise NotImplementedError(
            "ServerPagedResultLists do not support the data property")


class ClientPagedResultList(BaseResultList):
    """
    This is a convenience class that extends the :class:`BaseResultList` class
    and provides a client side implementation of paging. It is meant for use by
    provider developers and is not meant for direct use by end-users.
    This class can be used to wrap a full result list when an operation does
    not support server side paging. This class will then provide a paged view
    of the full result set entirely on the client side.
    """

    def __init__(self, provider, objects, limit=None, marker=None):
        self._objects = objects
        limit = limit or provider.config.default_result_limit
        total_size = len(objects)
        if marker:
            from_marker = itertools.dropwhile(
                lambda obj: not obj.id == marker, objects)
            # skip one past the marker
            next(from_marker, None)
            objects = list(from_marker)
        is_truncated = len(objects) > limit
        results = list(itertools.islice(objects, limit))
        super(ClientPagedResultList, self).__init__(
            is_truncated,
            results[-1].id if is_truncated else None,
            True, total=total_size,
            data=results)

    @property
    def supports_server_paging(self):
        return False

    @property
    def data(self):
        return self._objects


class BasePageableObjectMixin(PageableObjectMixin):
    """
    A mixin to provide iteration capability for a class
    that support a list(limit, marker) method.
    """

    def __iter__(self):
        marker = None

        result_list = self.list(marker=marker)
        if result_list.supports_server_paging:
            for result in result_list:
                yield result
            while result_list.is_truncated:
                result_list = self.list(marker=marker)
                for result in result_list:
                    yield result
                marker = result_list.marker
        else:
            for result in result_list.data:
                yield result


class BaseInstanceType(InstanceType, BaseCloudResource):

    def __init__(self, provider):
        super(BaseInstanceType, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, InstanceType) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @property
    def size_total_disk(self):
        return self.size_root_disk + self.size_ephemeral_disks

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseInstance(BaseCloudResource, BaseObjectLifeCycleMixin, Instance):

    def __init__(self, provider):
        super(BaseInstance, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Instance) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name and
                self.security_groups == other.security_groups and
                self.public_ips == other.public_ips and
                self.private_ips == other.private_ips and
                self.image_id == other.image_id)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [InstanceState.RUNNING],
            terminal_states=[InstanceState.TERMINATED, InstanceState.ERROR],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseLaunchConfig(LaunchConfig):

    def __init__(self, provider):
        self.provider = provider
        self.block_devices = []

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


class BaseMachineImage(
        BaseCloudResource, BaseObjectLifeCycleMixin, MachineImage):

    def __init__(self, provider):
        super(BaseMachineImage, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, MachineImage) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name and
                self.description == other.description)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [MachineImageState.AVAILABLE],
            terminal_states=[MachineImageState.ERROR],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseAttachmentInfo(AttachmentInfo):

    def __init__(self, volume, instance_id, device):
        self._volume = volume
        self._instance_id = instance_id
        self._device = device

    @property
    def volume(self):
        return self._volume

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def device(self):
        return self._device


class BaseVolume(BaseCloudResource, BaseObjectLifeCycleMixin, Volume):

    def __init__(self, provider):
        super(BaseVolume, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Volume) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [VolumeState.AVAILABLE],
            terminal_states=[VolumeState.ERROR, VolumeState.DELETED],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseSnapshot(BaseCloudResource, BaseObjectLifeCycleMixin, Snapshot):

    def __init__(self, provider):
        super(BaseSnapshot, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Snapshot) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.name == other.name)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [SnapshotState.AVAILABLE],
            terminal_states=[SnapshotState.ERROR],
            timeout=timeout,
            interval=interval)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.name, self.id)


class BaseKeyPair(KeyPair, BaseCloudResource):

    def __init__(self, provider, key_pair):
        super(BaseKeyPair, self).__init__(provider)
        self._key_pair = key_pair

    def __eq__(self, other):
        return (isinstance(other, KeyPair) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.name == other.name)

    @property
    def id(self):
        """
        Return the id of this key pair.
        """
        return self._key_pair.name

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


class BaseSecurityGroup(SecurityGroup, BaseCloudResource):

    def __init__(self, provider, security_group):
        super(BaseSecurityGroup, self).__init__(provider)
        self._security_group = security_group

    def __eq__(self, other):
        """
        Check if all the defined rules match across both security groups.
        """
        return (isinstance(other, SecurityGroup) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                len(self.rules) == len(other.rules) and  # Shortcut
                set(self.rules) == set(other.rules))

    def __ne__(self, other):
        return not self.__eq__(other)

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
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.name)


class BaseSecurityGroupRule(SecurityGroupRule, BaseCloudResource):

    def __init__(self, provider, rule, parent):
        super(BaseSecurityGroupRule, self).__init__(provider)
        self._rule = rule
        self.parent = parent

    def __repr__(self):
        return ("<CBSecurityGroupRule: IP: {0}; from: {1}; to: {2}; grp: {3}>"
                .format(self.ip_protocol, self.from_port, self.to_port,
                        self.group))

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


class BasePlacementZone(PlacementZone, BaseCloudResource):

    def __init__(self, provider):
        super(BasePlacementZone, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.id)

    def __eq__(self, other):
        return (isinstance(other, PlacementZone) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseRegion(Region, BaseCloudResource):

    def __init__(self, provider):
        super(BaseRegion, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.id)

    def __eq__(self, other):
        return (isinstance(other, Region) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        js['zones'] = [z.name for z in self.zones]
        return json.dumps(js, sort_keys=True)


class BaseBucketObject(BucketObject, BaseCloudResource):

    def __init__(self, provider):
        super(BaseBucketObject, self).__init__(provider)

    def save_content(self, target_stream):
        """
        Download this object and write its
        contents to the target_stream.
        """
        shutil.copyfileobj(self.iter_content(), target_stream)

    def __eq__(self, other):
        return (isinstance(other, BucketObject) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.name)


class BaseBucket(BasePageableObjectMixin, Bucket, BaseCloudResource):

    def __init__(self, provider):
        super(BaseBucket, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Bucket) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)

    def __repr__(self):
        return "<CB-{0}: {1}>".format(self.__class__.__name__,
                                      self.name)


class BaseNetwork(BaseCloudResource, Network, BaseObjectLifeCycleMixin):

    CB_DEFAULT_NETWORK_NAME = os.environ.get('CB_DEFAULT_NETWORK_NAME',
                                             'CloudBridgeNet')

    def __init__(self, provider):
        super(BaseNetwork, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.name)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [NetworkState.AVAILABLE],
            terminal_states=[NetworkState.ERROR],
            timeout=timeout,
            interval=interval)

    def __eq__(self, other):
        return (isinstance(other, Network) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseSubnet(Subnet, BaseCloudResource):

    CB_DEFAULT_SUBNET_NAME = os.environ.get('CB_DEFAULT_SUBNET_NAME',
                                            'CloudBridgeSubnet')

    def __init__(self, provider):
        super(BaseSubnet, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.name)

    def __eq__(self, other):
        return (isinstance(other, Subnet) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseFloatingIP(FloatingIP, BaseCloudResource):

    def __init__(self, provider):
        super(BaseFloatingIP, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__,
                                            self.id, self.public_ip)

    def __eq__(self, other):
        return (isinstance(other, FloatingIP) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseRouter(Router, BaseCloudResource):

    CB_DEFAULT_ROUTER_NAME = os.environ.get('CB_DEFAULT_ROUTER_NAME',
                                            'CloudBridgeRouter')

    def __init__(self, provider):
        super(BaseRouter, self).__init__(provider)

    def __repr__(self):
        return "<CB-{0}: {1} ({2})>".format(self.__class__.__name__, self.id,
                                            self.name)

    def __eq__(self, other):
        return (isinstance(other, Router) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)
