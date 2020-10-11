"""
Base implementation for data objects exposed through a provider or service
"""
import inspect
import itertools
import logging
import os
import re
import shutil
import time
import uuid

import six

from cloudbridge.interfaces.exceptions import \
    InvalidConfigurationException
from cloudbridge.interfaces.exceptions import InvalidLabelException
from cloudbridge.interfaces.exceptions import InvalidNameException
from cloudbridge.interfaces.exceptions import WaitStateException
from cloudbridge.interfaces.resources import AttachmentInfo
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import BucketObject
from cloudbridge.interfaces.resources import CloudResource
from cloudbridge.interfaces.resources import DnsRecord
from cloudbridge.interfaces.resources import DnsZone
from cloudbridge.interfaces.resources import FloatingIP
from cloudbridge.interfaces.resources import FloatingIpState
from cloudbridge.interfaces.resources import GatewayState
from cloudbridge.interfaces.resources import Instance
from cloudbridge.interfaces.resources import InstanceState
from cloudbridge.interfaces.resources import InternetGateway
from cloudbridge.interfaces.resources import KeyPair
from cloudbridge.interfaces.resources import LaunchConfig
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import MachineImageState
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import NetworkState
from cloudbridge.interfaces.resources import ObjectLifeCycleMixin
from cloudbridge.interfaces.resources import PageableObjectMixin
from cloudbridge.interfaces.resources import PlacementZone
from cloudbridge.interfaces.resources import Region
from cloudbridge.interfaces.resources import ResultList
from cloudbridge.interfaces.resources import Router
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import SnapshotState
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import SubnetState
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMFirewallRule
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume
from cloudbridge.interfaces.resources import VolumeState

from . import helpers as cb_helpers

log = logging.getLogger(__name__)


class BaseCloudResource(CloudResource):
    """
    Base implementation of a CloudBridge Resource.
    """
    # Regular expression for valid cloudbridge resource names/labels.
    # Can be alphanumeric string that does not start or end with a dash
    # Must be at least 3 characters in length.
    # Ref: https://stackoverflow.com/questions/2525327/regex-for-a-za-z0-9
    # -with-dashes-allowed-in-between-but-not-at-the-start-or-e
    CB_NAME_PATTERN = re.compile(r"^[a-z][-a-z0-9]{1,61}[a-z0-9]$")

    def __init__(self, provider):
        self.__provider = provider

    @staticmethod
    def is_valid_resource_name(name):
        if not name:
            return False
        else:
            return (True if BaseCloudResource.CB_NAME_PATTERN.match(name)
                    else False)

    @staticmethod
    def assert_valid_resource_label(name):
        if not BaseCloudResource.is_valid_resource_name(name):
            log.debug("InvalidLabelException raised on %s", name)
            raise InvalidLabelException(
                u"Invalid label: %s. Label must be at least 3 characters long"
                " and at most 63 characters. It must consist of lowercase"
                " letters, numbers, or dashes. The label must start with a "
                "letter and not end with a dash." % name)

    @staticmethod
    def assert_valid_resource_name(name):
        if not BaseCloudResource.is_valid_resource_name(name):
            log.debug("InvalidLabelException raised on %s", name)
            raise InvalidNameException(
                u"Invalid name: %s. Name must be at least 3 characters long"
                " and at most 63 characters. It must consist of lowercase"
                " letters, numbers, or dashes. The name must not start or"
                " end with a dash." % name)

    @staticmethod
    def _generate_name_from_label(label, default):
        if not label:
            label = default
        name = label[:55] + '-' + uuid.uuid4().hex[:6]
        BaseCloudResource.assert_valid_resource_name(name)
        return name

    @property
    def _provider(self):
        return self.__provider

    def to_json(self):
        # Get all attributes but filter methods and private/magic ones
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        return js

    def __repr__(self):
        name_or_label = getattr(self, 'label', self.name)
        if name_or_label == self.id:
            return "<CB-{0}: {1}>".format(
                self.__class__.__name__, self.id)
        else:
            return "<CB-{0}: {1} ({2})>".format(
                self.__class__.__name__, name_or_label, self.id)


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
                        "Waited too long for object: {0} to reach a desired"
                        "state: {1}. It's still in state: {2}".format(
                            self, target_states, self.state))
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
        for result in self.iter():
            yield result

    def iter(self, **kwargs):
        result_list = self.list(**kwargs)
        if result_list.supports_server_paging:
            for result in result_list:
                yield result
            while result_list.is_truncated:
                result_list = self.list(marker=result_list.marker, **kwargs)
                for result in result_list:
                    yield result
        else:
            for result in result_list.data:
                yield result


class BaseVMType(BaseCloudResource, VMType):

    def __init__(self, provider):
        super(BaseVMType, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, VMType) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @property
    def size_total_disk(self):
        return self.size_root_disk + self.size_ephemeral_disks


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
                self.label == other.label and
                self.vm_firewalls == other.vm_firewalls and
                self.public_ips == other.public_ips and
                self.private_ips == other.private_ips and
                self.image_id == other.image_id)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [InstanceState.RUNNING],
            terminal_states=[InstanceState.DELETED, InstanceState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self):
        self._provider.compute.instances.delete(self)


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
        log.debug("Appending %s to the block_devices list",
                  block_device)
        self.block_devices.append(block_device)

    def _validate_volume_device(self, source=None, is_root=None,
                                size=None, delete_on_terminate=None):
        """
        Validates a volume based device and throws an
        InvalidConfigurationException if the configuration is incorrect.
        """
        if source is None and not size:
            log.exception("InvalidConfigurationException raised: "
                          "no size argument specified.")
            raise InvalidConfigurationException(
                "A size must be specified for a blank new volume.")

        if source and \
                not isinstance(source, (Snapshot, Volume, MachineImage)):
            log.exception("InvalidConfigurationException raised: "
                          "source argument not specified correctly.")
            raise InvalidConfigurationException(
                "Source must be a Snapshot, Volume, MachineImage, or None.")
        if size:
            if not isinstance(size, six.integer_types) or not size > 0:
                log.exception("InvalidConfigurationException raised: "
                              "size argument must be an integer greater than "
                              "0. Got type %s and value %s.", type(size), size)
                raise InvalidConfigurationException(
                    "The size must be None or an integer greater than 0.")

        if is_root:
            for bd in self.block_devices:
                if bd.is_root:
                    log.exception("InvalidConfigurationException raised: "
                                  "%s has already been marked as the root "
                                  "block device.", bd)
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
                self.label == other.label and
                self.description == other.description)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [MachineImageState.AVAILABLE],
            terminal_states=[MachineImageState.ERROR],
            timeout=timeout,
            interval=interval)


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
                self.label == other.label)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [VolumeState.AVAILABLE],
            terminal_states=[VolumeState.ERROR, VolumeState.DELETED],
            timeout=timeout,
            interval=interval)

    def delete(self):
        """
        Delete this volume.
        """
        return self._provider.storage.volumes.delete(self)


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
                self.label == other.label)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [SnapshotState.AVAILABLE],
            terminal_states=[SnapshotState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self):
        """
        Delete this snapshot.
        """
        return self._provider.storage.snapshots.delete(self)


class BaseKeyPair(BaseCloudResource, KeyPair):

    def __init__(self, provider, key_pair):
        super(BaseKeyPair, self).__init__(provider)
        self._key_pair = key_pair
        self._private_material = None

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
        return self.id

    @property
    def material(self):
        return self._private_material

    @material.setter
    # pylint:disable=arguments-differ
    def material(self, value):
        self._private_material = value

    def delete(self):
        self._provider.security.key_pairs.delete(self)


class BaseVMFirewall(BaseCloudResource, VMFirewall):

    def __init__(self, provider, vm_firewall):
        super(BaseVMFirewall, self).__init__(provider)
        self._vm_firewall = vm_firewall

    def __eq__(self, other):
        """
        Check if all the defined rules match across both VM firewalls.
        """
        return (isinstance(other, VMFirewall) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                set(self.rules) == set(other.rules))

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def id(self):
        """
        Get the ID of this VM firewall.

        :rtype: str
        :return: VM firewall ID
        """
        return self._vm_firewall.id

    @property
    def name(self):
        """
        Return the name of this VM firewall.
        """
        return self.id

    @property
    def description(self):
        """
        Return the description of this VM firewall.
        """
        return self._vm_firewall.description

    def delete(self):
        """
        Delete this VM firewall.
        """
        return self._provider.security.vm_firewalls.delete(self)


class BaseVMFirewallRule(BaseCloudResource, VMFirewallRule):

    def __init__(self, parent_fw, rule):
        # pylint:disable=protected-access
        super(BaseVMFirewallRule, self).__init__(
            parent_fw._provider)
        self.firewall = parent_fw
        self._rule = rule

        # Cache name
        self._name = "{0}-{1}-{2}-{3}-{4}-{5}".format(
            self.direction, self.protocol, self.from_port, self.to_port,
            self.cidr, self.src_dest_fw_id).lower()

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return ("<{0}: id: {1}; direction: {2}; protocol: {3};  from: {4};"
                " to: {5}; cidr: {6}, src_dest_fw: {7}>"
                .format(self.__class__.__name__, self.id, self.direction,
                        self.protocol, self.from_port, self.to_port, self.cidr,
                        self.src_dest_fw_id))

    def __eq__(self, other):
        return (isinstance(other, VMFirewallRule) and
                self.direction == other.direction and
                self.protocol == other.protocol and
                self.from_port == other.from_port and
                self.to_port == other.to_port and
                self.cidr == other.cidr and
                self.src_dest_fw_id == other.src_dest_fw_id)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        """
        Return a hash-based interpretation of all of the object's field values.

        This is requeried for operations on hashed collections including
        ``set``, ``frozenset``, and ``dict``.
        """
        return hash("{0}{1}{2}{3}{4}{5}".format(
            self.direction, self.protocol, self.from_port, self.to_port,
            self.cidr, self.src_dest_fw_id))

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        js['src_dest_fw'] = self.src_dest_fw_id
        js['firewall'] = self.firewall.id
        return js

    def delete(self):
        self._provider.security._vm_firewall_rules.delete(self.firewall, self)


class BasePlacementZone(BaseCloudResource, PlacementZone):

    def __init__(self, provider):
        super(BasePlacementZone, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, PlacementZone) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseRegion(BaseCloudResource, Region):

    def __init__(self, provider):
        super(BaseRegion, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Region) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        js['zones'] = [z.id for z in self.zones]
        return js

    @property
    def default_zone(self):
        return next(iter(self.zones))


class BaseBucketObject(BaseCloudResource, BucketObject):

    # Regular expression for valid bucket keys.
    # They, must match the following criteria: http://docs.aws.amazon.com/"
    # AmazonS3/latest/dev/UsingMetadata.html#object-key-guidelines
    #
    # Note: The following regex is based on: https://stackoverflow.com/question
    # s/537772/what-is-the-most-correct-regular-expression-for-a-unix-file-path
    CB_NAME_PATTERN = re.compile(r"[^\0]+")

    def __init__(self, provider):
        super(BaseBucketObject, self).__init__(provider)

    @staticmethod
    def is_valid_resource_name(name):
        return (True if BaseBucketObject.CB_NAME_PATTERN.match(name)
                else False)

    @staticmethod
    def assert_valid_resource_name(name):
        if not BaseBucketObject.is_valid_resource_name(name):
            log.debug("InvalidLabelException raised on %s", name,
                      exc_info=True)
            raise InvalidLabelException(
                u"Invalid object name: %s. Name must match criteria defined "
                "in: http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMeta"
                "data.html#object-key-guidelines" % name)

    def save_content(self, target_stream):
        shutil.copyfileobj(self.iter_content(), target_stream)

    def __eq__(self, other):
        return (isinstance(other, BucketObject) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)


class BaseBucket(BaseCloudResource, Bucket):

    def __init__(self, provider):
        super(BaseBucket, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Bucket) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)

    def delete(self):
        """
        Delete this bucket.
        """
        self._provider.storage.buckets.delete(self.id)

    # TODO: Discuss creating `create_object` method, or change docs


class BaseNetwork(BaseCloudResource, BaseObjectLifeCycleMixin, Network):

    CB_DEFAULT_NETWORK_LABEL = os.environ.get('CB_DEFAULT_NETWORK_LABEL',
                                              'cloudbridge-net')
    CB_DEFAULT_IPV4RANGE = os.environ.get('CB_DEFAULT_IPV4RANGE',
                                          u'10.0.0.0/16')

    def __init__(self, provider):
        super(BaseNetwork, self).__init__(provider)

    @staticmethod
    def cidr_blocks_overlap(block1, block2):
        common_length = min(int(block1.split('/')[1]),
                            int(block2.split('/')[1]))

        p1 = [format(int(b), '08b') for b in block1.split('/')[0].split('.')]
        prefix1 = ''.join(p1)[:common_length]

        p2 = [format(int(b), '08b') for b in block2.split('/')[0].split('.')]
        prefix2 = ''.join(p2)[:common_length]

        return prefix1 == prefix2

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [NetworkState.AVAILABLE],
            terminal_states=[NetworkState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self):
        self._provider.networking.networks.delete(self)

    def __eq__(self, other):
        return (isinstance(other, Network) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseSubnet(BaseCloudResource, BaseObjectLifeCycleMixin, Subnet):

    CB_DEFAULT_SUBNET_LABEL = os.environ.get('CB_DEFAULT_SUBNET_LABEL',
                                             'cloudbridge-subnet')
    CB_DEFAULT_SUBNET_IPV4RANGE = os.environ.get('CB_DEFAULT_SUBNET_IPV4RANGE',
                                                 '10.0.0.0/24')

    def __init__(self, provider):
        super(BaseSubnet, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Subnet) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @property
    def network(self):
        return self._provider.networking.networks.get(self.network_id)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [SubnetState.AVAILABLE],
            terminal_states=[SubnetState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self):
        self._provider.networking.subnets.delete(self)


class BaseFloatingIP(BaseCloudResource, BaseObjectLifeCycleMixin, FloatingIP):

    def __init__(self, provider):
        super(BaseFloatingIP, self).__init__(provider)

    @property
    def name(self):
        return self.public_ip

    @property
    def state(self):
        return (FloatingIpState.IN_USE if self.in_use
                else FloatingIpState.AVAILABLE)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [FloatingIpState.AVAILABLE, FloatingIpState.IN_USE],
            terminal_states=[FloatingIpState.ERROR],
            timeout=timeout,
            interval=interval)

    def __eq__(self, other):
        return (isinstance(other, FloatingIP) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def delete(self):
        # For OS where the gateway is necessary, we pass the gateway when
        # deleting, for all others we pass None and it will be ignored
        gw = getattr(self, '_gateway_id', None)
        self._provider.networking._floating_ips.delete(gw, self.id)


class BaseRouter(BaseCloudResource, Router):

    CB_DEFAULT_ROUTER_LABEL = os.environ.get('CB_DEFAULT_ROUTER_LABEL',
                                             'cloudbridge-router')

    def __init__(self, provider):
        super(BaseRouter, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, Router) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def delete(self):
        self._provider.networking.routers.delete(self)


class BaseInternetGateway(BaseCloudResource, BaseObjectLifeCycleMixin,
                          InternetGateway):

    CB_DEFAULT_INET_GATEWAY_NAME = cb_helpers.get_env(
        'CB_DEFAULT_INET_GATEWAY_NAME', 'cloudbridge-inetgateway')

    def __init__(self, provider):
        super(BaseInternetGateway, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, InternetGateway) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def wait_till_ready(self, timeout=None, interval=None):
        self.wait_for(
            [GatewayState.AVAILABLE],
            terminal_states=[GatewayState.ERROR, GatewayState.UNKNOWN],
            timeout=timeout,
            interval=interval)

    def delete(self):
        return self._provider.networking._gateways.delete(self.network_id,
                                                          self)


class BaseDnsZone(BaseCloudResource, DnsZone):

    CB_NAME_PATTERN = re.compile(
        r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9]"
        r"[a-z0-9-]{0,61}[a-z0-9]\.?$")

    def __init__(self, provider):
        super(BaseDnsZone, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, BaseDnsZone) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @staticmethod
    def is_valid_resource_name(name):
        if not name:
            return False
        else:
            return (True if BaseDnsZone.CB_NAME_PATTERN.match(name)
                    else False)

    @staticmethod
    def assert_valid_resource_name(name):
        if not BaseDnsZone.is_valid_resource_name(name):
            log.debug("InvalidNameException raised on %s", name,
                      exc_info=True)
            raise InvalidNameException(
                u"Invalid object name: %s. Name must be fully qualified "
                u"(ending with a .) and match criteria defined "
                u"in: https://stackoverflow.com/q/10306690/10971151" % name)

    def delete(self):
        return self._provider.dns.host_zones.delete(self.id)


class BaseDnsRecord(BaseCloudResource, DnsRecord):

    CB_NAME_PATTERN = re.compile(
        r"^(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9]"
        r"[a-z0-9-]{0,61}[a-z0-9]\.?$")

    def __init__(self, provider):
        super(BaseDnsRecord, self).__init__(provider)

    def __eq__(self, other):
        return (isinstance(other, BaseDnsRecord) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @staticmethod
    def is_valid_resource_name(name):
        if not name:
            return False
        else:
            return (True if BaseDnsRecord.CB_NAME_PATTERN.match(name)
                    else False)

    @staticmethod
    def assert_valid_resource_name(name):
        if not BaseDnsRecord.is_valid_resource_name(name):
            log.debug("InvalidNameException raised on %s", name,
                      exc_info=True)
            raise InvalidNameException(
                u"Invalid object name: %s. Name must be fully qualified "
                u"(ending with a .) and match criteria defined "
                u"in: https://stackoverflow.com/q/10306690/10971151" % name)
