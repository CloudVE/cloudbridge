"""
Base implementation for data objects exposed through a provider or service
"""
import inspect
import io
import itertools
import logging
import os
import queue
import re
import shutil
import time
import uuid
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from typing import Any
from typing import IO
from typing import Iterator
from typing import Sequence
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import cast

from cloudbridge.interfaces.exceptions import \
    InvalidConfigurationException
from cloudbridge.interfaces.exceptions import InvalidLabelException
from cloudbridge.interfaces.exceptions import InvalidNameException
from cloudbridge.interfaces.exceptions import InvalidValueException
from cloudbridge.interfaces.exceptions import WaitStateException
from cloudbridge.interfaces.provider import CloudProvider
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
from cloudbridge.interfaces.resources import MultipartUpload
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
from cloudbridge.interfaces.resources import UploadConfig
from cloudbridge.interfaces.resources import UploadPart
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMFirewallRule
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume
from cloudbridge.interfaces.resources import VolumeState

from . import helpers as cb_helpers

if TYPE_CHECKING:
    from _typeshed import SupportsRead

    from cloudbridge.interfaces.services import BucketObjectService

log = logging.getLogger(__name__)

# Element type for the generic pageable collections defined in this module
# (mirrors ``cloudbridge.interfaces.resources.T``).
T = TypeVar("T")


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

    def __init__(self, provider: CloudProvider) -> None:
        self.__provider = provider

    @staticmethod
    def is_valid_resource_name(name: str) -> bool:
        if not name:
            return False
        else:
            return (True if BaseCloudResource.CB_NAME_PATTERN.match(name)
                    else False)

    @staticmethod
    def assert_valid_resource_label(name: str) -> None:
        if not BaseCloudResource.is_valid_resource_name(name):
            log.debug("InvalidLabelException raised on %s", name)
            raise InvalidLabelException(
                u"Invalid label: %s. Label must be at least 3 characters long"
                " and at most 63 characters. It must consist of lowercase"
                " letters, numbers, or dashes. The label must start with a "
                "letter and not end with a dash." % name)

    @staticmethod
    def assert_valid_resource_name(name: str) -> None:
        if not BaseCloudResource.is_valid_resource_name(name):
            log.debug("InvalidLabelException raised on %s", name)
            raise InvalidNameException(
                u"Invalid name: %s. Name must be at least 3 characters long"
                " and at most 63 characters. It must consist of lowercase"
                " letters, numbers, or dashes. The name must not start or"
                " end with a dash." % name)

    @staticmethod
    def _generate_name_from_label(label: str | None, default: str) -> str:
        if not label:
            label = default
        name = label[:55] + '-' + uuid.uuid4().hex[:6]
        BaseCloudResource.assert_valid_resource_name(name)
        return name

    @property
    def _provider(self) -> CloudProvider:
        return self.__provider

    def to_json(self) -> dict[str, Any]:
        # Get all attributes but filter methods and private/magic ones
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        return js

    def __repr__(self) -> str:
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

    def wait_for(self, target_states: list[str],
                 terminal_states: list[str] | None = None,
                 timeout: int | None = None,
                 interval: int | None = None) -> bool:
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


class BaseResultList(ResultList[T]):

    def __init__(
            self, is_truncated: bool, marker: str | None,
            supports_total: bool, total: int | None = None,
            data: Sequence[T] | None = None) -> None:
        # call list constructor
        super(BaseResultList, self).__init__(data or [])
        self._marker = marker
        self._is_truncated = is_truncated
        self._supports_total = True if supports_total else False
        self._total = total

    @property
    def marker(self) -> str | None:
        return self._marker

    @property
    def is_truncated(self) -> bool:
        return self._is_truncated

    @property
    def supports_total(self) -> bool:
        return self._supports_total

    @property
    def total_results(self) -> int:
        return cast(int, self._total)


class ServerPagedResultList(BaseResultList[T]):
    """
    This is a convenience class that extends the :class:`BaseResultList` class
    and provides a server side implementation of paging. It is meant for use by
    provider developers and is not meant for direct use by end-users.
    This class can be used to wrap a partial result list when an operation
    supports server side paging.
    """

    @property
    def supports_server_paging(self) -> bool:
        return True

    @property
    def data(self) -> list[T]:
        raise NotImplementedError(
            "ServerPagedResultLists do not support the data property")


class ClientPagedResultList(BaseResultList[T]):
    """
    This is a convenience class that extends the :class:`BaseResultList` class
    and provides a client side implementation of paging. It is meant for use by
    provider developers and is not meant for direct use by end-users.
    This class can be used to wrap a full result list when an operation does
    not support server side paging. This class will then provide a paged view
    of the full result set entirely on the client side.
    """

    def __init__(self, provider: CloudProvider, objects: Sequence[T],
                 limit: int | None = None, marker: str | None = None) -> None:
        self._objects = list(objects)
        limit = limit or provider.config.default_result_limit
        total_size = len(objects)
        if marker:
            from_marker = itertools.dropwhile(
                lambda obj: not cast(CloudResource, obj).id == marker, objects)
            # skip one past the marker
            next(from_marker, None)
            objects = list(from_marker)
        is_truncated = len(objects) > limit
        results = list(itertools.islice(objects, limit))
        super(ClientPagedResultList, self).__init__(
            is_truncated,
            cast(CloudResource, results[-1]).id if is_truncated else None,
            True, total=total_size,
            data=results)

    @property
    def supports_server_paging(self) -> bool:
        return False

    @property
    def data(self) -> list[T]:
        return self._objects


class BasePageableObjectMixin(PageableObjectMixin[T]):
    """
    A mixin to provide iteration capability for a class
    that support a list(limit, marker) method.
    """

    def __iter__(self) -> Iterator[T]:
        for result in self.iter():
            yield result

    def iter(self, **kwargs: Any) -> Iterator[T]:
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

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseVMType, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, VMType) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @property
    def size_total_disk(self) -> int:
        return self.size_root_disk + self.size_ephemeral_disks


class BaseInstance(BaseCloudResource, BaseObjectLifeCycleMixin, Instance):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseInstance, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
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

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [InstanceState.RUNNING],
            terminal_states=[InstanceState.DELETED, InstanceState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self) -> None:
        # InstanceService.delete is implemented by every provider but is not
        # declared on the public typed interface, hence the ignore.
        self._provider.compute.instances.delete(self)  # type: ignore[attr-defined]


class BaseLaunchConfig(LaunchConfig):

    def __init__(self, provider: CloudProvider) -> None:
        self.provider = provider
        self.block_devices: list[BaseLaunchConfig.BlockDeviceMapping] = []

    class BlockDeviceMapping(object):
        """
        Represents a block device mapping
        """

        def __init__(self, is_volume: bool = False,
                     source: Volume | Snapshot | MachineImage | None = None,
                     is_root: bool | None = None, size: int | None = None,
                     delete_on_terminate: bool | None = None) -> None:
            self.is_volume = is_volume
            self.source = source
            self.is_root = is_root
            self.size = size
            self.delete_on_terminate = delete_on_terminate

    def add_ephemeral_device(self) -> None:
        block_device = BaseLaunchConfig.BlockDeviceMapping()
        self.block_devices.append(block_device)

    def add_volume_device(
            self, source: Volume | Snapshot | MachineImage | None = None,
            is_root: bool | None = None, size: int | None = None,
            delete_on_terminate: bool | None = None) -> None:
        block_device = self._validate_volume_device(
            source=source, is_root=is_root, size=size,
            delete_on_terminate=delete_on_terminate)
        log.debug("Appending %s to the block_devices list",
                  block_device)
        self.block_devices.append(block_device)

    def _validate_volume_device(
            self, source: Volume | Snapshot | MachineImage | None = None,
            is_root: bool | None = None, size: int | None = None,
            delete_on_terminate: bool | None = None
    ) -> "BaseLaunchConfig.BlockDeviceMapping":
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
            if not isinstance(size, int) or not size > 0:
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

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseMachineImage, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, MachineImage) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.label == other.label and
                self.description == other.description)

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [MachineImageState.AVAILABLE],
            terminal_states=[MachineImageState.ERROR],
            timeout=timeout,
            interval=interval)


class BaseAttachmentInfo(AttachmentInfo):

    def __init__(self, volume: Volume, instance_id: str,
                 device: str | None) -> None:
        self._volume = volume
        self._instance_id = instance_id
        self._device = device

    @property
    def volume(self) -> Volume:
        return self._volume

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def device(self) -> str | None:
        return self._device


class BaseVolume(BaseCloudResource, BaseObjectLifeCycleMixin, Volume):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseVolume, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Volume) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.label == other.label)

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [VolumeState.AVAILABLE],
            terminal_states=[VolumeState.ERROR, VolumeState.DELETED],
            timeout=timeout,
            interval=interval)

    def delete(self) -> None:
        """
        Delete this volume.
        """
        return self._provider.storage.volumes.delete(self)


class BaseSnapshot(BaseCloudResource, BaseObjectLifeCycleMixin, Snapshot):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseSnapshot, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Snapshot) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.state == other.state and
                self.label == other.label)

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [SnapshotState.AVAILABLE],
            terminal_states=[SnapshotState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self) -> None:
        """
        Delete this snapshot.
        """
        return self._provider.storage.snapshots.delete(self)


class BaseKeyPair(BaseCloudResource, KeyPair):

    def __init__(self, provider: CloudProvider, key_pair: Any) -> None:
        super(BaseKeyPair, self).__init__(provider)
        self._key_pair = key_pair
        self._private_material: str | None = None

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, KeyPair) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.name == other.name)

    @property
    def id(self) -> str:
        """
        Return the id of this key pair.
        """
        return cast(str, self._key_pair.name)

    @property
    def name(self) -> str:
        """
        Return the name of this key pair.
        """
        return self.id

    @property
    def material(self) -> str | None:
        return self._private_material

    @material.setter
    # pylint:disable=arguments-differ
    def material(self, value: str | None) -> None:
        self._private_material = value

    def delete(self) -> None:
        self._provider.security.key_pairs.delete(self)


class BaseVMFirewall(BaseCloudResource, VMFirewall):

    def __init__(self, provider: CloudProvider, vm_firewall: Any) -> None:
        super(BaseVMFirewall, self).__init__(provider)
        self._vm_firewall = vm_firewall

    def __eq__(self, other: object) -> bool:
        """
        Check if all the defined rules match across both VM firewalls.
        """
        return (isinstance(other, VMFirewall) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                set(self.rules) == set(other.rules))

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    @property
    def id(self) -> str:
        """
        Get the ID of this VM firewall.

        :rtype: str
        :return: VM firewall ID
        """
        return cast(str, self._vm_firewall.id)

    @property
    def name(self) -> str:
        """
        Return the name of this VM firewall.
        """
        return self.id

    @property
    def description(self) -> str | None:
        """
        Return the description of this VM firewall.
        """
        return cast("str | None", self._vm_firewall.description)

    def delete(self) -> None:
        """
        Delete this VM firewall.
        """
        return self._provider.security.vm_firewalls.delete(self)


class BaseVMFirewallRule(BaseCloudResource, VMFirewallRule):

    def __init__(self, parent_fw: VMFirewall, rule: Any) -> None:
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
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return ("<{0}: id: {1}; direction: {2}; protocol: {3};  from: {4};"
                " to: {5}; cidr: {6}, src_dest_fw: {7}>"
                .format(self.__class__.__name__, self.id, self.direction,
                        self.protocol, self.from_port, self.to_port, self.cidr,
                        self.src_dest_fw_id))

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, VMFirewallRule) and
                self.direction == other.direction and
                self.protocol == other.protocol and
                self.from_port == other.from_port and
                self.to_port == other.to_port and
                self.cidr == other.cidr and
                self.src_dest_fw_id == other.src_dest_fw_id)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """
        Return a hash-based interpretation of all of the object's field values.

        This is requeried for operations on hashed collections including
        ``set``, ``frozenset``, and ``dict``.
        """
        return hash("{0}{1}{2}{3}{4}{5}".format(
            self.direction, self.protocol, self.from_port, self.to_port,
            self.cidr, self.src_dest_fw_id))

    def to_json(self) -> dict[str, Any]:
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        js['src_dest_fw'] = self.src_dest_fw_id
        js['firewall'] = self.firewall.id
        return js

    def delete(self) -> None:
        # The interface types the second arg as a rule_id (str), but every
        # provider's _vm_firewall_rules.delete accepts the rule object itself.
        self._provider.security._vm_firewall_rules.delete(
            self.firewall, self)  # type: ignore[arg-type]


class BasePlacementZone(BaseCloudResource, PlacementZone):

    def __init__(self, provider: CloudProvider) -> None:
        super(BasePlacementZone, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, PlacementZone) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseRegion(BaseCloudResource, Region):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseRegion, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Region) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def to_json(self) -> dict[str, Any]:
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        js['zones'] = [z.id for z in self.zones]
        return js

    @property
    def default_zone(self) -> PlacementZone:
        return next(iter(self.zones))


class BaseUploadPart(UploadPart):
    """
    A simple, serializable handle for a single uploaded part. Concrete
    providers return these from ``upload_part`` and consume them in
    ``complete_multipart_upload``.
    """

    def __init__(self, part_number: int, etag: object) -> None:
        self._part_number = part_number
        self._etag = etag

    @property
    def part_number(self) -> int:
        return self._part_number

    @property
    def etag(self) -> object:
        return self._etag

    def __repr__(self) -> str:
        return "<CB-{0}: {1} ({2})>".format(
            self.__class__.__name__, self._part_number, self._etag)


class BaseMultipartUpload(BaseCloudResource, MultipartUpload):
    """
    Base implementation of an in-progress multipart upload. It is a thin
    handle that delegates the actual work to the provider's bucket-object
    service, mirroring how other base resources delegate to their service
    (e.g. ``BaseBucket.delete``).
    """

    def __init__(self, provider: CloudProvider, bucket: Bucket,
                 object_name: str, upload_id: str) -> None:
        super(BaseMultipartUpload, self).__init__(provider)
        self._bucket = bucket
        self._object_name = object_name
        self._upload_id = upload_id

    @property
    def id(self) -> str:
        return self._upload_id

    @property
    def name(self) -> str:
        return self._object_name

    @property
    def bucket(self) -> Bucket:
        return self._bucket

    @property
    def object_name(self) -> str:
        return self._object_name

    def upload_part(self, part_number: int,
                    data: bytes | IO[bytes]) -> UploadPart:
        # pylint:disable=protected-access
        # _bucket_objects is a provider-internal service not exposed on the
        # public StorageService interface, hence the typed cast + ignore.
        return self._bucket_objects.upload_part(
            self._bucket, self, part_number, data)

    def complete(self, parts: list[UploadPart]) -> BucketObject:
        # pylint:disable=protected-access
        return self._bucket_objects.complete_multipart_upload(
            self._bucket, self, parts)

    def abort(self) -> None:
        # pylint:disable=protected-access
        return self._bucket_objects.abort_multipart_upload(
            self._bucket, self)

    @property
    def _bucket_objects(self) -> "BucketObjectService":
        # _bucket_objects is a provider-internal service not exposed on the
        # public StorageService interface, hence the typed cast + ignore.
        return cast(
            "BucketObjectService",
            self._provider.storage._bucket_objects)  # type: ignore[attr-defined]


class BaseBucketObject(BaseCloudResource, BucketObject):

    # Regular expression for valid bucket keys.
    # They, must match the following criteria: http://docs.aws.amazon.com/"
    # AmazonS3/latest/dev/UsingMetadata.html#object-key-guidelines
    #
    # Note: The following regex is based on: https://stackoverflow.com/question
    # s/537772/what-is-the-most-correct-regular-expression-for-a-unix-file-path
    CB_NAME_PATTERN = re.compile(r"[^\0]+")

    # Uploads larger than this many bytes are split into parts.
    CB_MULTIPART_THRESHOLD = int(os.environ.get(
        'CB_MULTIPART_THRESHOLD', 100 * 1024 * 1024))   # 100 MiB
    # The size of each part for multipart uploads.
    CB_MULTIPART_PART_SIZE = int(os.environ.get(
        'CB_MULTIPART_PART_SIZE', 50 * 1024 * 1024))    # 50 MiB
    # Portable floor: S3 and Swift reject non-final parts smaller than 5 MiB,
    # so part sizes below this are rejected up-front.
    CB_MULTIPART_MIN_PART_SIZE = 5 * 1024 * 1024
    # Number of parts uploaded in parallel by the transparent multipart path.
    CB_MULTIPART_MAX_CONCURRENCY = int(os.environ.get(
        'CB_MULTIPART_MAX_CONCURRENCY', 5))

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseBucketObject, self).__init__(provider)

    @property
    def bucket(self) -> Bucket:
        # Provider-implemented; every concrete BucketObject knows its bucket.
        raise NotImplementedError(
            "BucketObject subclasses must implement the bucket property")

    def _upload_single_shot(
            self, data: str | bytes | IO[bytes]) -> BucketObject:
        # Provider-implemented single-shot (non-multipart) upload.
        raise NotImplementedError(
            "BucketObject subclasses must implement _upload_single_shot")

    @property
    def _bucket_objects(self) -> "BucketObjectService":
        # _bucket_objects is a provider-internal service not exposed on the
        # public StorageService interface, hence the typed cast + ignore.
        return cast(
            "BucketObjectService",
            self._provider.storage._bucket_objects)  # type: ignore[attr-defined]

    @staticmethod
    def is_valid_resource_name(name: str) -> bool:
        return (True if BaseBucketObject.CB_NAME_PATTERN.match(name)
                else False)

    @staticmethod
    def assert_valid_resource_name(name: str) -> None:
        if not BaseBucketObject.is_valid_resource_name(name):
            log.debug("InvalidLabelException raised on %s", name,
                      exc_info=True)
            raise InvalidLabelException(
                u"Invalid object name: %s. Name must match criteria defined "
                "in: http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMeta"
                "data.html#object-key-guidelines" % name)

    def save_content(self, target_stream: IO[bytes]) -> None:
        # iter_content() is declared Iterable[bytes] on the interface, but the
        # concrete objects returned by providers also support .read(); cast so
        # copyfileobj accepts it without changing behavior.
        shutil.copyfileobj(
            cast("SupportsRead[bytes]", self.iter_content()), target_stream)

    # The three resolvers below pick, in order of precedence: an explicit
    # per-call UploadConfig field, the provider/global config, then the class
    # default constant.
    def _multipart_threshold(self, config: UploadConfig | None = None) -> int:
        if config is not None and config.threshold is not None:
            return int(config.threshold)
        # pylint:disable=protected-access
        # _get_config_value is a provider-internal helper not on the public
        # CloudProvider interface, hence the ignore.
        return int(self._provider._get_config_value(  # type: ignore[attr-defined]
            'multipart_threshold', self.CB_MULTIPART_THRESHOLD))

    def _multipart_part_size(self, config: UploadConfig | None = None) -> int:
        if config is not None and config.part_size is not None:
            return int(config.part_size)
        # pylint:disable=protected-access
        return int(self._provider._get_config_value(  # type: ignore[attr-defined]
            'multipart_part_size', self.CB_MULTIPART_PART_SIZE))

    def _multipart_max_concurrency(
            self, config: UploadConfig | None = None) -> int:
        if config is not None and config.max_concurrency is not None:
            return int(config.max_concurrency)
        # pylint:disable=protected-access
        return int(self._provider._get_config_value(  # type: ignore[attr-defined]
            'multipart_max_concurrency', self.CB_MULTIPART_MAX_CONCURRENCY))

    @staticmethod
    def _data_size(data: str | bytes | IO[bytes]) -> int | None:
        """
        Best-effort size of an upload payload, or ``None`` if it cannot be
        determined without consuming the data (e.g. a non-seekable stream).
        """
        if isinstance(data, str):
            return len(data.encode('utf-8'))
        if isinstance(data, (bytes, bytearray)):
            return len(data)
        if hasattr(data, 'seek') and hasattr(data, 'tell'):
            try:
                pos = data.tell()
                data.seek(0, os.SEEK_END)
                size = data.tell()
                data.seek(pos)
                return size
            except (OSError, ValueError):
                return None
        return None

    @staticmethod
    def _as_stream(data: str | bytes | IO[bytes]) -> IO[bytes]:
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(data, (bytes, bytearray)):
            return io.BytesIO(data)
        return data

    def upload(self, data: str | bytes | IO[bytes],
               config: UploadConfig | None = None) -> BucketObject:
        size = self._data_size(data)
        if size is not None and size > self._multipart_threshold(config):
            return self._upload_multipart(self._as_stream(data), config)
        return self._upload_single_shot(data)

    def upload_from_file(
            self, path: str,
            config: UploadConfig | None = None) -> BucketObject:
        if os.path.getsize(path) > self._multipart_threshold(config):
            with open(path, 'rb') as f:
                return self._upload_multipart(f, config)
        return self._upload_from_file_single_shot(path)

    def _upload_multipart(self, stream: IO[bytes],
                          config: UploadConfig | None = None) -> BucketObject:
        """
        Drive the explicit multipart lifecycle over a stream, reading it one
        part at a time so the whole payload is never held in memory.

        Parts are uploaded across a bounded thread pool. To stay safe even on
        providers whose SDK client/connection is not thread-safe, each worker
        uploads through its own cloned provider (see :meth:`.CloudProvider.
        clone`), so no provider state is shared between threads. Any failure
        aborts the upload to avoid leaking staged parts.

        Providers with an efficient, thread-safe native uploader (e.g. AWS via
        boto3's ``upload_fileobj``) override this method to use it directly.
        """
        part_size = self._multipart_part_size(config)
        if part_size < self.CB_MULTIPART_MIN_PART_SIZE:
            raise InvalidValueException('multipart_part_size', part_size)

        concurrency = max(1, self._multipart_max_concurrency(config))
        upload = self.create_multipart_upload()
        try:
            if concurrency == 1:
                parts = self._upload_parts_serially(upload, stream, part_size)
            else:
                parts = self._upload_parts_concurrently(
                    upload, stream, part_size, concurrency)
            return upload.complete(parts)
        except Exception:
            upload.abort()
            raise

    def _upload_parts_serially(self, upload: MultipartUpload,
                               stream: IO[bytes],
                               part_size: int) -> list[UploadPart]:
        parts = []
        part_number = 1
        while True:
            chunk = self._read_part(stream, part_size)
            if not chunk:
                break
            parts.append(upload.upload_part(part_number, chunk))
            part_number += 1
        return parts

    def _upload_parts_concurrently(self, upload: MultipartUpload,
                                   stream: IO[bytes], part_size: int,
                                   concurrency: int) -> list[UploadPart]:
        # A pool of cloned bucket-object services, one per worker, so each
        # thread touches an isolated provider/connection.
        clones: "queue.Queue[BucketObjectService]" = queue.Queue()
        for _ in range(concurrency):
            # pylint:disable=protected-access
            # _bucket_objects is a provider-internal service not exposed on the
            # public StorageService interface, hence the typed cast + ignore.
            clones.put(cast(
                "BucketObjectService",
                self._provider.clone().storage._bucket_objects))  # type: ignore[attr-defined]

        def upload_one(part_number: int, chunk: bytes) -> UploadPart:
            service = clones.get()
            try:
                return service.upload_part(
                    upload.bucket, upload, part_number, chunk)
            finally:
                clones.put(service)

        parts: list[UploadPart] = []
        in_flight: set[Future[UploadPart]] = set()
        part_number = 1
        depleted = False
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            while not depleted or in_flight:
                # Keep the pool fed but never read more than ``concurrency``
                # parts ahead, bounding memory to ~concurrency * part_size.
                while not depleted and len(in_flight) < concurrency:
                    chunk = self._read_part(stream, part_size)
                    if not chunk:
                        depleted = True
                        break
                    in_flight.add(
                        executor.submit(upload_one, part_number, chunk))
                    part_number += 1
                if not in_flight:
                    break
                done, in_flight = wait(
                    in_flight, return_when=FIRST_COMPLETED)
                for future in done:
                    parts.append(future.result())
        return parts

    @staticmethod
    def _read_part(stream: IO[bytes], part_size: int) -> bytes:
        """
        Read exactly ``part_size`` bytes from ``stream`` (fewer only at EOF),
        coalescing short reads so non-final parts always meet the provider
        minimum part size.
        """
        buffer = bytearray()
        while len(buffer) < part_size:
            chunk = stream.read(part_size - len(buffer))
            if not chunk:
                break
            buffer.extend(chunk)
        return bytes(buffer)

    def _upload_from_file_single_shot(
            self, path: str) -> BucketObject:
        """
        Default small-file upload: read the file and hand it to the provider's
        single-shot upload. Providers with a more efficient native file upload
        (e.g. AWS ``upload_file``) override :meth:`upload_from_file` directly.
        """
        with open(path, 'rb') as f:
            return self._upload_single_shot(f)

    def create_multipart_upload(self) -> MultipartUpload:
        # pylint:disable=protected-access
        return self._bucket_objects.create_multipart_upload(
            self.bucket, self.name)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, BucketObject) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)


class BaseBucket(BaseCloudResource, Bucket):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseBucket, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Bucket) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id and
                # check from most to least likely mutables
                self.name == other.name)

    def delete(self, delete_contents: bool = False) -> None:
        """
        Delete this bucket.
        """
        if delete_contents:
            for obj in self.objects:
                obj.delete()
        # BucketService.delete is implemented by every provider but is not
        # declared on the public typed interface, hence the ignore.
        self._provider.storage.buckets.delete(self.id)  # type: ignore[attr-defined]

    # TODO: Discuss creating `create_object` method, or change docs


class BaseNetwork(BaseCloudResource, BaseObjectLifeCycleMixin, Network):

    CB_DEFAULT_NETWORK_LABEL = os.environ.get('CB_DEFAULT_NETWORK_LABEL',
                                              'cloudbridge-net')
    CB_DEFAULT_IPV4RANGE = os.environ.get('CB_DEFAULT_IPV4RANGE',
                                          u'10.0.0.0/16')

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseNetwork, self).__init__(provider)

    @staticmethod
    def cidr_blocks_overlap(block1: str, block2: str) -> bool:
        common_length = min(int(block1.split('/')[1]),
                            int(block2.split('/')[1]))

        p1 = [format(int(b), '08b') for b in block1.split('/')[0].split('.')]
        prefix1 = ''.join(p1)[:common_length]

        p2 = [format(int(b), '08b') for b in block2.split('/')[0].split('.')]
        prefix2 = ''.join(p2)[:common_length]

        return prefix1 == prefix2

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [NetworkState.AVAILABLE],
            terminal_states=[NetworkState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self) -> None:
        self._provider.networking.networks.delete(self)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Network) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)


class BaseSubnet(BaseCloudResource, BaseObjectLifeCycleMixin, Subnet):

    CB_DEFAULT_SUBNET_LABEL = os.environ.get('CB_DEFAULT_SUBNET_LABEL',
                                             'cloudbridge-subnet')
    CB_DEFAULT_SUBNET_IPV4RANGE = os.environ.get('CB_DEFAULT_SUBNET_IPV4RANGE',
                                                 '10.0.0.0/24')

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseSubnet, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Subnet) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @property
    def network(self) -> Network:
        # The parent network of an existing subnet always resolves; the
        # service get() is typed Network | None, so narrow to Network.
        return cast(
            Network, self._provider.networking.networks.get(self.network_id))

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [SubnetState.AVAILABLE],
            terminal_states=[SubnetState.ERROR],
            timeout=timeout,
            interval=interval)

    def delete(self) -> None:
        self._provider.networking.subnets.delete(self)


class BaseFloatingIP(BaseCloudResource, BaseObjectLifeCycleMixin, FloatingIP):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseFloatingIP, self).__init__(provider)

    @property
    def name(self) -> str:
        return self.public_ip

    @property
    def state(self) -> str:
        return (FloatingIpState.IN_USE if self.in_use
                else FloatingIpState.AVAILABLE)

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [FloatingIpState.AVAILABLE, FloatingIpState.IN_USE],
            terminal_states=[FloatingIpState.ERROR],
            timeout=timeout,
            interval=interval)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, FloatingIP) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def delete(self) -> None:
        # For OS where the gateway is necessary, we pass the gateway when
        # deleting, for all others we pass None and it will be ignored
        gw: Any = getattr(self, '_gateway_id', None)
        self._provider.networking._floating_ips.delete(gw, self.id)


class BaseRouter(BaseCloudResource, Router):

    CB_DEFAULT_ROUTER_LABEL = os.environ.get('CB_DEFAULT_ROUTER_LABEL',
                                             'cloudbridge-router')

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseRouter, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Router) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def delete(self) -> None:
        self._provider.networking.routers.delete(self)


class BaseInternetGateway(BaseCloudResource, BaseObjectLifeCycleMixin,
                          InternetGateway):

    CB_DEFAULT_INET_GATEWAY_NAME = cb_helpers.get_env(
        'CB_DEFAULT_INET_GATEWAY_NAME', 'cloudbridge-inetgateway')

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseInternetGateway, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, InternetGateway) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    def wait_till_ready(
            self, timeout: int | None = None,
            interval: int | None = None) -> None:
        self.wait_for(
            [GatewayState.AVAILABLE],
            terminal_states=[GatewayState.ERROR, GatewayState.UNKNOWN],
            timeout=timeout,
            interval=interval)

    def delete(self) -> None:
        # A gateway is always attached to a network when it can be deleted;
        # network_id is typed str | None, so narrow to str for the service.
        return self._provider.networking._gateways.delete(
            cast(str, self.network_id), self)


class BaseDnsZone(BaseCloudResource, DnsZone):

    CB_NAME_PATTERN = re.compile(
        r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9]"
        r"[a-z0-9-]{0,61}[a-z0-9]\.?$")

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseDnsZone, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, BaseDnsZone) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @staticmethod
    def is_valid_resource_name(name: str) -> bool:
        if not name:
            return False
        else:
            return (True if BaseDnsZone.CB_NAME_PATTERN.match(name)
                    else False)

    @staticmethod
    def assert_valid_resource_name(name: str) -> None:
        if not BaseDnsZone.is_valid_resource_name(name):
            log.debug("InvalidNameException raised on %s", name,
                      exc_info=True)
            raise InvalidNameException(
                u"Invalid object name: %s. Name must be fully qualified "
                u"(ending with a .) and match criteria defined "
                u"in: https://stackoverflow.com/q/10306690/10971151" % name)

    def delete(self) -> None:
        return self._provider.dns.host_zones.delete(self.id)


class BaseDnsRecord(BaseCloudResource, DnsRecord):

    CB_NAME_PATTERN = re.compile(
        r"^(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9]"
        r"[a-z0-9-]{0,61}[a-z0-9]\.?$")

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseDnsRecord, self).__init__(provider)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, BaseDnsRecord) and
                # pylint:disable=protected-access
                self._provider == other._provider and
                self.id == other.id)

    @staticmethod
    def is_valid_resource_name(name: str) -> bool:
        if not name:
            return False
        else:
            return (True if BaseDnsRecord.CB_NAME_PATTERN.match(name)
                    else False)

    @staticmethod
    def assert_valid_resource_name(name: str) -> None:
        if not BaseDnsRecord.is_valid_resource_name(name):
            log.debug("InvalidNameException raised on %s", name,
                      exc_info=True)
            raise InvalidNameException(
                u"Invalid object name: %s. Name must be fully qualified "
                u"(ending with a .) and match criteria defined "
                u"in: https://stackoverflow.com/q/10306690/10971151" % name)
