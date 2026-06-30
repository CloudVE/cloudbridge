"""
DataTypes used by this provider
"""
from __future__ import annotations

import collections
import io
import logging
from datetime import datetime
from typing import Any
from typing import IO
from typing import Iterable
from typing import Iterator
from typing import TYPE_CHECKING
from typing import cast

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.compute.models import DataDisk
from azure.mgmt.compute.models import ManagedDiskParameters
from azure.mgmt.compute.models import SubResource as ComputeSubResource
from azure.mgmt.devtestlabs.models import GalleryImageReference
from azure.mgmt.network.models import NetworkSecurityGroup

import paramiko

from cloudbridge.base.resources import BaseAttachmentInfo
from cloudbridge.base.resources import BaseBucket
from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.base.resources import BaseDnsRecord
from cloudbridge.base.resources import BaseDnsZone
from cloudbridge.base.resources import BaseFloatingIP
from cloudbridge.base.resources import BaseInstance
from cloudbridge.base.resources import BaseInternetGateway
from cloudbridge.base.resources import BaseKeyPair
from cloudbridge.base.resources import BaseLaunchConfig
from cloudbridge.base.resources import BaseMachineImage
from cloudbridge.base.resources import BaseNetwork
from cloudbridge.base.resources import BasePlacementZone
from cloudbridge.base.resources import BaseRegion
from cloudbridge.base.resources import BaseRouter
from cloudbridge.base.resources import BaseSnapshot
from cloudbridge.base.resources import BaseSubnet
from cloudbridge.base.resources import BaseVMFirewall
from cloudbridge.base.resources import BaseVMFirewallRule
from cloudbridge.base.resources import BaseVMType
from cloudbridge.base.resources import BaseVolume
from cloudbridge.interfaces import InstanceState
from cloudbridge.interfaces import VolumeState
from cloudbridge.interfaces.exceptions import ProviderInternalException
from cloudbridge.interfaces.resources import AttachmentInfo
from cloudbridge.interfaces.resources import BucketObject
from cloudbridge.interfaces.resources import FloatingIP
from cloudbridge.interfaces.resources import Gateway
from cloudbridge.interfaces.resources import Instance
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import MachineImageState
from cloudbridge.interfaces.resources import NetworkState
from cloudbridge.interfaces.resources import PlacementZone
from cloudbridge.interfaces.resources import RouterState
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import SnapshotState
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import SubnetState
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import UploadConfig
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume

from . import helpers as azure_helpers
from .subservices import AzureBucketObjectSubService
from .subservices import AzureDnsRecordSubService
from .subservices import AzureFloatingIPSubService
from .subservices import AzureGatewaySubService
from .subservices import AzureSubnetSubService
from .subservices import AzureVMFirewallRuleSubService

if TYPE_CHECKING:
    from cloudbridge.providers.azure.provider import AzureCloudProvider

log = logging.getLogger(__name__)


class AzureVMFirewall(BaseVMFirewall):
    def __init__(self, provider: AzureCloudProvider, vm_firewall: Any) -> None:
        super(AzureVMFirewall, self).__init__(provider, vm_firewall)
        self._vm_firewall = vm_firewall
        self._vm_firewall.tags = self._vm_firewall.tags or {}
        self._rule_container = AzureVMFirewallRuleSubService(provider, self)

    @property
    def network_id(self) -> str | None:
        return self._vm_firewall.tags.get('network_id', None)

    @property
    def resource_id(self) -> str:
        return self._vm_firewall.id

    @property
    def id(self) -> str:
        return self._vm_firewall.id

    @property
    def name(self) -> str:
        return self._vm_firewall.name

    @property
    def label(self) -> str | None:
        return self._vm_firewall.tags.get('Label', None)

    @label.setter
    def label(self, value: str) -> None:
        self.assert_valid_resource_label(value)
        self._vm_firewall.tags.update(Label=value or "")
        cast("AzureCloudProvider", self._provider).azure_client \
            .update_vm_firewall_tags(self.id, self._vm_firewall.tags)

    @property
    def description(self) -> str | None:
        return self._vm_firewall.tags.get('Description')

    @description.setter
    def description(self, value: str) -> None:
        self._vm_firewall.tags.update(Description=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_vm_firewall_tags(self.id,
                                    self._vm_firewall.tags)

    @property
    def rules(self) -> AzureVMFirewallRuleSubService:
        return self._rule_container

    def refresh(self) -> None:
        """
        Refreshes the security group with tags if required.
        """
        try:
            self._vm_firewall = cast(
                "AzureCloudProvider", self._provider).azure_client. \
                get_vm_firewall(self.id)
            if not self._vm_firewall.tags:
                self._vm_firewall.tags = {}
        except (ResourceNotFoundError, ValueError) as cloud_error:
            log.exception(cloud_error)
            # The security group no longer exists and cannot be refreshed.

    def to_json(self) -> dict[str, Any]:
        js = super(AzureVMFirewall, self).to_json()
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = json_rules
        if js.get('network_id'):
            js.pop('network_id')  # Omit for consistency across cloud providers
        return js


# Tuple for port range
PortRange = collections.namedtuple('PortRange', ['from_port', 'to_port'])


class AzureVMFirewallRule(BaseVMFirewallRule):
    def __init__(self, parent_fw: VMFirewall, rule: Any) -> None:
        super(AzureVMFirewallRule, self).__init__(parent_fw, rule)

    @property
    def id(self) -> str:
        return self._rule.id

    @property
    def name(self) -> str:
        return self._rule.name

    @property
    def direction(self) -> TrafficDirection:
        if self._rule.direction == "Inbound":
            return TrafficDirection.INBOUND
        elif self._rule.direction == "Outbound":
            return TrafficDirection.OUTBOUND
        raise ProviderInternalException(
            "Unknown traffic direction: {0}".format(self._rule.direction))

    @property
    def protocol(self) -> str | None:
        return self._rule.protocol

    @property
    def from_port(self) -> int:
        return self._port_range_tuple.from_port

    @property
    def to_port(self) -> int:
        return self._port_range_tuple.to_port

    @property
    def _port_range_tuple(self) -> PortRange:
        if self._rule.destination_port_range == '*':
            return PortRange(1, 65535)
        destination_port_range = self._rule.destination_port_range
        port_range_split = destination_port_range.split('-', 1)
        return PortRange(int(port_range_split[0]), int(port_range_split[1]))

    @property
    def cidr(self) -> str | None:
        return self._rule.source_address_prefix

    @property
    def src_dest_fw_id(self) -> str | None:
        return self.firewall.id

    @property
    def src_dest_fw(self) -> VMFirewall | None:
        return self.firewall


class AzureBucketObject(BaseBucketObject):
    def __init__(self, provider: AzureCloudProvider, container: AzureBucket,
                 blob_properties: Any) -> None:
        super(AzureBucketObject, self).__init__(provider)
        self._container = container
        self._blob_properties = blob_properties

    @property
    def _blob_client(self) -> Any:
        return self._container._bucket.get_blob_client(self.name)

    @property
    def id(self) -> str:
        return self._blob_properties.name

    @property
    def name(self) -> str:
        return self._blob_properties.name

    @property
    def size(self) -> int:
        """
        Get this object's size.
        """
        return self._blob_properties.size

    @property
    def last_modified(self) -> str:

        """
        Get the date and time this object was last modified.
        """
        return self._blob_properties.last_modified.strftime("%Y-%m-%dT%H:%M:%S.%f")

    def iter_content(self) -> Iterable[bytes]:
        """
        Returns this object's content as an
        iterable stream.
        """

        def iterable_to_stream(iterable: Iterator[bytes]) -> io.RawIOBase:
            class IterStream(io.RawIOBase):
                def __init__(self) -> None:
                    self.leftover: bytes | None = None

                def readable(self) -> bool:
                    return True

                def readinto(self, b: Any) -> int:
                    try:
                        buffer_length = len(b)  # We're supposed to return at most this much
                        chunk = self.leftover or next(iterable)
                        output, self.leftover = chunk[:buffer_length], chunk[buffer_length:]
                        b[:len(output)] = output
                        return len(output)
                    except StopIteration:
                        return 0  # indicate EOF

            return IterStream()

        def blob_iterator() -> Iterator[bytes]:
            for chunk in self._blob_client.download_blob().chunks():
                yield chunk

        return iterable_to_stream(blob_iterator())

    @property
    def bucket(self) -> AzureBucket:
        return self._container

    def _upload_single_shot(self, data: str | bytes | IO[bytes]) -> BucketObject:
        """
        Upload the object in a single request. ``data`` may be text, bytes or
        a file-like object; the Azure SDK streams file-like data rather than
        buffering it all in memory. Larger uploads are handled transparently
        by the base class via the multipart path.
        """
        cast("AzureCloudProvider", self._provider).azure_client.upload_blob(
            self._container.id, self.id, data)
        return self

    def _upload_multipart(self, stream: IO[bytes],
                          config: UploadConfig | None = None) -> BucketObject:
        # The Azure SDK's upload_blob stages blocks concurrently (max_concurrency
        # workers) over a thread-safe client, so the transparent multipart path
        # delegates to it rather than CloudBridge's generic clone-pool driver.
        cast("AzureCloudProvider", self._provider).azure_client.upload_blob(
            self._container.id, self.id, stream,
            max_concurrency=self._multipart_max_concurrency(config))
        return self

    def delete(self) -> None:
        """
        Delete this object.

        :rtype: bool
        :return: True if successful
        """
        self._blob_client.delete_blob()

    def generate_url(self, expires_in: int, writable: bool = False) -> str:
        """
        Generate a URL to this object.
        """
        return cast(
            "AzureCloudProvider", self._provider).azure_client.get_blob_url(
            self._container, self.name, expires_in, writable)

    def refresh(self) -> None:
        pass


class AzureBucket(BaseBucket):
    def __init__(self, provider: AzureCloudProvider, bucket: Any) -> None:
        super(AzureBucket, self).__init__(provider)
        self._bucket = bucket
        self._object_container = AzureBucketObjectSubService(provider, self)

    @property
    def id(self) -> str:
        try:
            name = self._bucket.name
        except AttributeError:
            name = self._bucket.container_name
        return name

    @property
    def name(self) -> str:
        """
        Get this bucket's name.

        Due to changes in the Azure API, we can either received a
        Container or a ContainerClient, Container has a name, but
        the ContainerClient has a container_name
        """
        try:
            name = self._bucket.name
        except AttributeError:
            name = self._bucket.container_name
        return name

    def exists(self, name: str) -> bool:
        """
        Determine if an object with given name exists in this bucket.
        """
        return True if self.objects.get(name) else False

    @property
    def objects(self) -> AzureBucketObjectSubService:
        return self._object_container


class AzureVolume(BaseVolume):
    VOLUME_STATE_MAP: dict[str, str] = {
        'InProgress': VolumeState.CREATING,
        'Creating': VolumeState.CREATING,
        'Unattached': VolumeState.AVAILABLE,
        'Attached': VolumeState.IN_USE,
        'Deleting': VolumeState.CONFIGURING,
        'Updating': VolumeState.CONFIGURING,
        'Deleted': VolumeState.DELETED,
        'Failed': VolumeState.ERROR,
        'Canceled': VolumeState.ERROR
    }

    def __init__(self, provider: AzureCloudProvider, volume: Any) -> None:
        super(AzureVolume, self).__init__(provider)
        self._volume = volume
        self._description: str | None = None
        self._state = 'unknown'
        self._update_state()
        if not self._volume.tags:
            self._volume.tags = {}

    def _update_state(self) -> None:
        if not self._volume.provisioning_state == 'Succeeded':
            self._state = self._volume.provisioning_state
        elif self._volume.managed_by:
            self._state = 'Attached'
        else:
            self._state = 'Unattached'

    @property
    def id(self) -> str:
        return self._volume.id

    @property
    def resource_id(self) -> str:
        return self._volume.id

    @property
    def name(self) -> str:
        return self._volume.name

    @property
    def tags(self) -> dict[str, str]:
        return self._volume.tags

    @property
    def label(self) -> str | None:
        """
        Get the volume label.

        .. note:: an instance must have a (case sensitive) tag ``Label``
        """
        return self._volume.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the volume label.
        """
        self.assert_valid_resource_label(value)
        self._volume.tags.update(Label=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_disk_tags(self.id,
                             self._volume.tags)

    @property
    def description(self) -> str:
        return self._volume.tags.get('Description', None)

    @description.setter
    def description(self, value: str) -> None:
        self._volume.tags.update(Description=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_disk_tags(self.id,
                             self._volume.tags)

    @property
    def size(self) -> int:
        return self._volume.disk_size_gb

    @property
    def create_time(self) -> str:
        return self._volume.time_created.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @property
    def zone_id(self) -> str:
        return self._volume.location

    @property
    def source(self) -> Snapshot | MachineImage | None:
        return self._volume.creation_data.source_uri

    @property
    def attachments(self) -> AttachmentInfo | None:
        """
        Azure does not have option to specify the device name
        while attaching disk to VM. It is automatically populated
        and is not returned. As a result this method ignores
        the device name parameter and passes None
        to the BaseAttachmentInfo
        :return:
        """
        if self._volume.managed_by:
            return BaseAttachmentInfo(self, self._volume.managed_by, None)
        else:
            return None

    def attach(self, instance: str | Instance, device: str) -> None:
        """
        Attach this volume to an instance.
        """
        instance_id = instance.id if isinstance(
            instance,
            Instance) else instance
        vm = cast("AzureCloudProvider", self._provider).azure_client.get_vm(
            instance_id)

        vm.storage_profile.data_disks.append(DataDisk(
            lun=len(vm.storage_profile.data_disks),
            name=self._volume.name,
            create_option='attach',
            managed_disk=ManagedDiskParameters(id=self.resource_id)
        ))
        cast("AzureCloudProvider", self._provider).azure_client.update_vm(
            instance_id, vm)

    def detach(self, force: bool = False) -> None:
        """
        Detach this volume from an instance.
        """
        azure_client = cast("AzureCloudProvider", self._provider).azure_client
        for vm in azure_client.list_vm():
            for item in vm.storage_profile.data_disks:
                if item.managed_disk and \
                        item.managed_disk.id == self.resource_id:
                    vm.storage_profile.data_disks.remove(item)
                    azure_client.update_vm(vm.id, vm)

    def create_snapshot(self, label: str,
                        description: str | None = None) -> Snapshot:
        """
        Create a snapshot of this Volume.
        """
        return self._provider.storage.snapshots.create(label, self,
                                                       description)

    @property
    def state(self) -> str:
        return AzureVolume.VOLUME_STATE_MAP.get(
            self._state, VolumeState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._volume = cast(
                "AzureCloudProvider", self._provider).azure_client. \
                get_disk(self.id)
            self._update_state()
        except (ResourceNotFoundError, ValueError) as cloud_error:
            log.exception(cloud_error)
            # The volume no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'


class AzureSnapshot(BaseSnapshot):
    SNAPSHOT_STATE_MAP: dict[str, str] = {
        'InProgress': SnapshotState.PENDING,
        'Succeeded': SnapshotState.AVAILABLE,
        'Failed': SnapshotState.ERROR,
        'Canceled': SnapshotState.ERROR,
        'Updating': SnapshotState.CONFIGURING,
        'Deleting': SnapshotState.CONFIGURING,
        'Deleted': SnapshotState.UNKNOWN
    }

    def __init__(self, provider: AzureCloudProvider, snapshot: Any) -> None:
        super(AzureSnapshot, self).__init__(provider)
        self._snapshot = snapshot
        self._description: str | None = None
        self._state = self._snapshot.provisioning_state
        if not self._snapshot.tags:
            self._snapshot.tags = {}

    @property
    def id(self) -> str:
        return self._snapshot.id

    @property
    def name(self) -> str:
        return self._snapshot.name

    @property
    def resource_id(self) -> str:
        return self._snapshot.id

    @property
    def label(self) -> str | None:
        """
        Get the snapshot label.

        .. note:: an instance must have a (case sensitive) tag ``Label``
        """
        return self._snapshot.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the snapshot label.
        """
        self.assert_valid_resource_label(value)
        self._snapshot.tags.update(Label=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_snapshot_tags(self.id,
                                 self._snapshot.tags)

    @property
    def description(self) -> str:
        return self._snapshot.tags.get('Description', None)

    @description.setter
    def description(self, value: str) -> None:
        self._snapshot.tags.update(Description=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_snapshot_tags(self.id,
                                 self._snapshot.tags)

    @property
    def size(self) -> int:
        return self._snapshot.disk_size_gb

    @property
    def volume_id(self) -> str | None:
        return self._snapshot.creation_data.source_resource_id

    @property
    def create_time(self) -> str:
        return self._snapshot.time_created.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @property
    def state(self) -> str:
        return AzureSnapshot.SNAPSHOT_STATE_MAP.get(
            self._state, SnapshotState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._snapshot = cast(
                "AzureCloudProvider", self._provider).azure_client. \
                get_snapshot(self.id)
            self._state = self._snapshot.provisioning_state
        except (ResourceNotFoundError, ValueError) as cloud_error:
            log.exception(cloud_error)
            # The snapshot no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'

    def create_volume(self, size: int | None = None,
                      volume_type: str | None = None,
                      iops: int | None = None) -> Volume:
        """
        Create a new Volume from this Snapshot.
        """
        return self._provider.storage.volumes. \
            create(self.name, self.size, snapshot=self)


class AzureMachineImage(BaseMachineImage):
    IMAGE_STATE_MAP: dict[str, str] = {
        'InProgress': MachineImageState.PENDING,
        'Succeeded': MachineImageState.AVAILABLE,
        'Failed': MachineImageState.ERROR
    }

    def __init__(self, provider: AzureCloudProvider, image: Any) -> None:
        super(AzureMachineImage, self).__init__(provider)
        # Image can be either a dict for public image reference
        # or the Azure iamge object
        self._image = image
        if isinstance(self._image, GalleryImageReference):
            self._state = 'Succeeded'
        else:
            self._state = self._image.provisioning_state
            if not self._image.tags:
                self._image.tags = {}

    @property
    def id(self) -> str:
        """
        Get the image identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            image_id = azure_helpers.normalize_rg_case(self._image.id)
            if not image_id:
                raise ProviderInternalException("Image is missing an id")
            return image_id

    @property
    def name(self) -> str:
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            return self._image.name

    @property
    def resource_id(self) -> str:
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            return self._image.id

    @property
    def label(self) -> str | None:
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            return self._image.tags.get('Label', None)

    @label.setter
    def label(self, value: str) -> None:
        """
        Set the image label when it is a private image.
        """
        if not self.is_gallery_image:
            self.assert_valid_resource_label(value)
            self._image.tags.update(Label=value or "")
            cast("AzureCloudProvider", self._provider).azure_client. \
                update_image_tags(self.id, self._image.tags)

    @property
    def description(self) -> str | None:
        """
        Get the image description.

        :rtype: ``str``
        :return: Description for this image as returned by the cloud middleware
        """
        if self.is_gallery_image:
            return 'Public gallery image from the Azure Marketplace: '\
                    + self.name
        else:
            return self._image.tags.get('Description', None)

    @description.setter
    def description(self, value: str) -> None:
        """
        Set the image description.
        """
        if not self.is_gallery_image:
            self._image.tags.update(Description=value or "")
            cast("AzureCloudProvider", self._provider).azure_client. \
                update_image_tags(self.id, self._image.tags)

    @property
    def min_disk(self) -> int | None:
        """
        Returns the minimum size of the disk that's required to
        boot this image (in GB).
        This value is not retuned in azure api
        as this is a limitation with Azure Compute API

        :rtype: ``int``
        :return: The minimum disk size needed by this image
        """
        if self.is_gallery_image:
            return 0
        else:
            return self._image.storage_profile.os_disk.disk_size_gb or 0

    def delete(self) -> None:
        """
        Delete this image
        """
        if not self.is_gallery_image:
            cast("AzureCloudProvider", self._provider).azure_client. \
                delete_image(self.id)

    @property
    def state(self) -> str:
        if self.is_gallery_image:
            return MachineImageState.AVAILABLE
        else:
            return AzureMachineImage.IMAGE_STATE_MAP.get(
                self._state, MachineImageState.UNKNOWN)

    @property
    def is_gallery_image(self) -> bool:
        """
        Returns true if the image is a public reference and false if it
        is a private image in the resource group.
        """
        return isinstance(self._image, GalleryImageReference)

    def refresh(self) -> None:
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        if not self.is_gallery_image:
            try:
                self._image = cast(
                    "AzureCloudProvider", self._provider).azure_client. \
                    get_image(self.id)
                self._state = self._image.provisioning_state
            except ResourceNotFoundError as cloud_error:
                log.exception(cloud_error)
                # image no longer exists
                self._state = "unknown"


class AzureNetwork(BaseNetwork):
    NETWORK_STATE_MAP: dict[str, str] = {
        'InProgress': NetworkState.PENDING,
        'Succeeded': NetworkState.AVAILABLE,
    }

    def __init__(self, provider: AzureCloudProvider, network: Any) -> None:
        super(AzureNetwork, self).__init__(provider)
        self._network = network
        self._state = self._network.provisioning_state
        if not self._network.tags:
            self._network.tags = {}
        self._gateway_service = AzureGatewaySubService(provider, self)
        self._subnet_svc = AzureSubnetSubService(provider, self)

    @property
    def id(self) -> str:
        return self._network.id

    @property
    def name(self) -> str:
        return self._network.name

    @property
    def resource_id(self) -> str:
        return self._network.id

    @property
    def label(self) -> str | None:
        """
        Get the network label.

        .. note:: the network must have a (case sensitive) tag ``Label``
        """
        return self._network.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the network label.
        """
        self.assert_valid_resource_label(value)
        self._network.tags.update(Label=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_network_tags(self.id, self._network.tags)

    @property
    def external(self) -> bool:
        """
        For Azure, all VPC networks can be connected to the Internet so always
        return ``True``.
        """
        return True

    @property
    def state(self) -> str:
        return AzureNetwork.NETWORK_STATE_MAP.get(
            self._state, NetworkState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this network by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._network = cast(
                "AzureCloudProvider", self._provider).azure_client.\
                get_network(self.id)
            self._state = self._network.provisioning_state
        except (ResourceNotFoundError, ValueError) as cloud_error:
            log.exception(cloud_error)
            # The network no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'

    @property
    def cidr_block(self) -> str:
        """
        Address space associated with this network
        :return:
        """
        return self._network.address_space.address_prefixes[0]

    def delete(self) -> None:
        """
        Delete an existing network.
        """
        cast("AzureCloudProvider", self._provider).azure_client. \
            delete_network(self.id)

    @property
    def subnets(self) -> AzureSubnetSubService:
        return self._subnet_svc

    @property
    def gateways(self) -> AzureGatewaySubService:
        return self._gateway_service


class AzureFloatingIP(BaseFloatingIP):

    def __init__(self, provider: AzureCloudProvider,
                 floating_ip: Any) -> None:
        super(AzureFloatingIP, self).__init__(provider)
        self._ip = floating_ip

    @property
    def id(self) -> str:
        return self._ip.id

    @property
    def name(self) -> str:
        return self._ip.ip_address

    @property
    def resource_id(self) -> str:
        return self._ip.id

    @property
    def public_ip(self) -> str:
        return self._ip.ip_address

    @property
    def private_ip(self) -> str | None:
        return self._ip.ip_configuration.private_ip_address \
            if self._ip.ip_configuration else None

    @property
    def in_use(self) -> bool:
        return True if self._ip.ip_configuration else False

    def refresh(self) -> None:
        # Gateway is not needed as it doesn't exist in Azure, so just
        # getting the Floating IP again from the client
        # pylint:disable=protected-access
        fip = cast(AzureFloatingIP, self._provider.networking._floating_ips.get(
            cast(Any, None), self.id))
        # pylint:disable=protected-access
        self._ip = fip._ip


class AzureRegion(BaseRegion):
    def __init__(self, provider: AzureCloudProvider,
                 azure_region: Any) -> None:
        super(AzureRegion, self).__init__(provider)
        self._azure_region = azure_region

    @property
    def id(self) -> str:
        return self._azure_region.name

    @property
    def name(self) -> str:
        return self._azure_region.name

    @property
    def zones(self) -> list[AzurePlacementZone]:
        """
            Access information about placement zones within this region.
            As Azure does not have this feature, mapping the region
            name as zone id and name.
        """
        return [AzurePlacementZone(
            cast("AzureCloudProvider", self._provider),
            self._azure_region.name,
            self._azure_region.name)]


class AzurePlacementZone(BasePlacementZone):
    """
    As Azure does not provide zones (limited support), we are mapping the
    region information in the zones.
    """
    def __init__(self, provider: AzureCloudProvider, zone: str,
                 region: str) -> None:
        super(AzurePlacementZone, self).__init__(provider)
        self._azure_zone = zone
        self._azure_region = region

    @property
    def id(self) -> str:
        """
            Get the zone id
            :rtype: ``str``
            :return: ID for this zone as returned by the cloud middleware.
        """
        return self._azure_zone

    @property
    def name(self) -> str:
        """
            Get the zone name.
            :rtype: ``str``
            :return: Name for this zone as returned by the cloud middleware.
        """
        return self._azure_region

    @property
    def region_name(self) -> str:
        """
            Get the region that this zone belongs to.
            :rtype: ``str``
            :return: Name of this zone's region as returned by the
            cloud middleware
        """
        return self._azure_region


class AzureSubnet(BaseSubnet):
    _SUBNET_STATE_MAP: dict[str, str] = {
        'InProgress': SubnetState.PENDING,
        'Succeeded': SubnetState.AVAILABLE,
    }

    def __init__(self, provider: AzureCloudProvider, subnet: Any) -> None:
        super(AzureSubnet, self).__init__(provider)
        self._subnet = subnet
        self._state = self._subnet.provisioning_state
        self._tag_name: str | None = None

    @property
    def id(self) -> str:
        return self._subnet.id

    @property
    def name(self) -> str:
        net_name = self.network_id.split('/')[-1]
        sn_name = self._subnet.name
        return '{0}/{1}'.format(net_name, sn_name)

    @property
    def label(self) -> str | None:
        # Although Subnet doesn't support labels, we use the parent Network's
        # tags to track the subnet's labels
        network = self.network
        # pylint:disable=protected-access
        az_network = cast(AzureNetwork, network)._network
        return az_network.tags.get(self.tag_name, None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        self.assert_valid_resource_label(value)
        network = self.network
        # pylint:disable=protected-access
        az_network = cast(AzureNetwork, network)._network
        kwargs = {self.tag_name: value or ""}
        az_network.tags.update(**kwargs)
        cast("AzureCloudProvider", self._provider).azure_client \
            .update_network_tags(az_network.id, az_network.tags)

    @property
    def tag_name(self) -> str:
        if not self._tag_name:
            self._tag_name = 'SubnetLabel_{0}'.format(self._subnet.name)
        return self._tag_name

    @property
    def resource_id(self) -> str:
        return self._subnet.id

    @property
    def zone(self) -> PlacementZone | None:
        # pylint:disable=protected-access
        region = self._provider.compute.regions.get(
            cast(AzureNetwork, self.network)._network.location)
        if not region:
            return None
        return list(region.zones)[0]

    @property
    def cidr_block(self) -> str:
        return self._subnet.address_prefix

    @property
    def network_id(self) -> str:
        return cast("AzureCloudProvider", self._provider).azure_client \
            .get_network_id_for_subnet(self.id)

    @property
    def state(self) -> str:
        return self._SUBNET_STATE_MAP.get(self._state, NetworkState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this network by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._subnet = cast(
                "AzureCloudProvider", self._provider).azure_client. \
                get_subnet(self.id)
            self._state = self._subnet.provisioning_state
        except (ResourceNotFoundError, ValueError) as cloud_error:
            log.exception(cloud_error)
            # The subnet no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'


class AzureInstance(BaseInstance):

    INSTANCE_STATE_MAP: dict[str, str] = {
        'InProgress': InstanceState.PENDING,
        'Creating': InstanceState.PENDING,
        'VM running': InstanceState.RUNNING,
        'Updating': InstanceState.CONFIGURING,
        'Deleted': InstanceState.DELETED,
        'Stopping': InstanceState.CONFIGURING,
        'Deleting': InstanceState.CONFIGURING,
        'Stopped': InstanceState.STOPPED,
        'Canceled': InstanceState.ERROR,
        'Failed': InstanceState.ERROR,
        'VM stopped': InstanceState.STOPPED,
        'VM deallocated': InstanceState.STOPPED,
        'VM deallocating': InstanceState.CONFIGURING,
        'VM stopping': InstanceState.CONFIGURING,
        'VM starting': InstanceState.CONFIGURING
    }

    def __init__(self, provider: AzureCloudProvider,
                 vm_instance: Any) -> None:
        super(AzureInstance, self).__init__(provider)
        self._vm = vm_instance
        self._update_state()
        if not self._vm.tags:
            self._vm.tags = {}

    @property
    def _nic_ids(self) -> Iterator[str]:
        return (nic.id for nic in self._vm.network_profile.network_interfaces)

    @property
    def _nics(self) -> Iterator[Any]:
        azure_client = cast("AzureCloudProvider", self._provider).azure_client
        return (azure_client.get_nic(nic_id)
                for nic_id in self._nic_ids)

    @property
    def _public_ip_ids(self) -> Iterator[str]:
        return (ip_config.public_ip_address.id
                for nic in self._nics
                for ip_config in nic.ip_configurations
                if nic.ip_configurations and ip_config.public_ip_address)

    @property
    def id(self) -> str:
        """
        Get the instance identifier.
        """
        return self._vm.id

    @property
    def name(self) -> str:
        """
        Get the instance name.
        """
        return self._vm.name

    @property
    def resource_id(self) -> str:
        return self._vm.id

    @property
    def label(self) -> str | None:
        """
        Get the instance label.

        .. note:: an instance must have a (case sensitive) tag ``Label``
        """
        return self._vm.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the instance label.
        """
        self.assert_valid_resource_label(value)
        self._vm.tags.update(Label=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_vm_tags(self.id, self._vm.tags)

    @property
    def public_ips(self) -> list[str]:
        """
        Get all the public IP addresses for this instance.
        """
        azure_client = cast("AzureCloudProvider", self._provider).azure_client
        return [azure_client.get_floating_ip(pip).ip_address
                for pip in self._public_ip_ids]

    @property
    def private_ips(self) -> list[str]:
        """
        Get all the private IP addresses for this instance.
        """
        return [ip_config.private_ip_address
                for nic in self._nics
                for ip_config in nic.ip_configurations
                if nic.ip_configurations and ip_config.private_ip_address]

    @property
    def vm_type_id(self) -> str:
        """
        Get the instance type name.
        """
        return self._vm.hardware_profile.vm_size

    @property
    def vm_type(self) -> VMType:
        """
        Get the instance type.
        """
        return self._provider.compute.vm_types.find(
            name=self.vm_type_id)[0]

    @property
    def create_time(self) -> str | datetime:
        """
        Get the instance creation time
        """
        return self._vm.time_created

    def reboot(self) -> None:
        """
        Reboot this instance (using the cloud middleware API).
        """
        cast("AzureCloudProvider", self._provider).azure_client. \
            restart_vm(self.id)

    def start(self) -> None:
        """
        Start this instance (using the cloud middleware API).
        """
        cast("AzureCloudProvider", self._provider).azure_client. \
            start_vm(self.id)

    def stop(self) -> None:
        """
        Stop this instance (using the cloud middleware API).
        """
        cast("AzureCloudProvider", self._provider).azure_client. \
            stop_vm(self.id)

    @property
    def image_id(self) -> str:
        """
        Get the image ID for this instance.
        """
        # Not tested for resource group images
        reference_dict = self._vm.storage_profile.image_reference.as_dict()
        if reference_dict.get('publisher'):
            return ':'.join([reference_dict['publisher'],
                             reference_dict['offer'],
                             reference_dict['sku'],
                             reference_dict['version']])
        else:
            return reference_dict['id']

    @property
    def zone_id(self) -> str:
        """
        Get the placement zone id where this instance is running.
        """
        return self._vm.location

    @property
    def subnet_id(self) -> str:
        """
        Return the first subnet id associated with the first network iface.

        An Azure instance can have multiple network interfaces attached with
        each interface having at most one subnet. This method will return only
        the subnet of the first attached network interface.
        """
        azure_client = cast("AzureCloudProvider", self._provider).azure_client
        for nic_id in self._nic_ids:
            nic = azure_client.get_nic(nic_id)
            for ipc in nic.ip_configurations:
                return ipc.subnet.id
        raise ProviderInternalException(
            "Instance {0} has no subnet".format(self.id))

    @property
    def vm_firewalls(self) -> list[VMFirewall]:
        return cast("list[VMFirewall]", [
            self._provider.security.vm_firewalls.get(group_id)
            for group_id in self.vm_firewall_ids])

    @property
    def vm_firewall_ids(self) -> list[str]:
        return [nic.network_security_group.id
                for nic in self._nics
                if nic.network_security_group]

    @property
    def key_pair_id(self) -> str | None:
        """
        Get the name of the key pair associated with this instance.
        """
        return self._vm.tags.get('Key_Pair')

    def create_image(self, label: str,
                     private_key_path: str | None = None) -> MachineImage:
        """
        Create a new image based on this instance. Documentation for create
        image available at https://docs.microsoft.com/en-us/azure/virtual-ma
        chines/linux/capture-image. In azure, we need to deprovision the VM
        before capturing.
        To deprovision, login to the VM and execute the `waagent deprovision`
        command. To do this programmatically, use paramiko to ssh into the VM
        and executing deprovision command. To SSH into the VM programmatically
        however, we need to pass private key file path, so we have modified the
        CloudBridge interface to pass the private key file path
        """

        self.assert_valid_resource_label(label)
        name = self._generate_name_from_label(label, 'cb-img')
        azure_client = cast("AzureCloudProvider", self._provider).azure_client

        if not self._state == 'VM generalized':
            if not self._state == 'VM running':
                azure_client.start_vm(self.id)

            # if private_key_path:
            self._deprovision(private_key_path)
            azure_client.deallocate_vm(self.id)
            azure_client.generalize_vm(self.id)

        create_params = {
            'location': self._provider.region_name,
            'source_virtual_machine': ComputeSubResource(id=self.resource_id),
            'tags': {'Label': label}
        }

        image = azure_client.create_image(name, create_params)
        return AzureMachineImage(
            cast("AzureCloudProvider", self._provider), image)

    def _deprovision(self, private_key_path: str | None) -> None:
        if not private_key_path:
            return
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.public_ips[0],
                username=cast(
                    "AzureCloudProvider",
                    self._provider).vm_default_user_name,
                key_filename=private_key_path)
            client.exec_command('sudo waagent -deprovision -force')
        finally:
            client.close()

    def add_floating_ip(self, floating_ip: FloatingIP | str) -> None:
        """
        Attaches public ip to the instance.
        """
        floating_ip_id = floating_ip.id if isinstance(
            floating_ip, AzureFloatingIP) else floating_ip
        nic = next(self._nics)
        nic.ip_configurations[0].public_ip_address = {
            'id': floating_ip_id
        }
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_nic(nic.id, nic)

    def remove_floating_ip(self, floating_ip: FloatingIP | str) -> None:
        """
        Remove a public IP address from this instance.
        """
        floating_ip_id = floating_ip.id if isinstance(
            floating_ip, AzureFloatingIP) else floating_ip
        nic = next(self._nics)
        for ip_config in nic.ip_configurations:
            if ip_config.public_ip_address.id == floating_ip_id:
                nic.ip_configurations[0].public_ip_address = None
                cast("AzureCloudProvider", self._provider).azure_client. \
                    update_nic(nic.id, nic)

    def add_vm_firewall(self, firewall: VMFirewall) -> None:
        '''
        :param fw:
        :return: None

        This method adds the security group to VM instance.
        In Azure, security group added to Network interface.
        Azure supports to add only one security group to
        network interface, we are adding the provided security group
        if not associated any security group to NIC
        else replacing the existing security group.
        '''
        fw: Any = (self._provider.security.vm_firewalls.get(firewall)
                   if isinstance(firewall, str) else firewall)
        nic = next(self._nics)
        if not nic.network_security_group:
            nic.network_security_group = NetworkSecurityGroup()
            nic.network_security_group.id = fw.resource_id
        else:
            existing_fw: Any = self._provider.security.\
                vm_firewalls.get(nic.network_security_group.id)
            new_fw: Any = self._provider.security.vm_firewalls.\
                create('{0}-{1}'.format(fw.name, existing_fw.name),
                       'Merged security groups {0} and {1}'.
                       format(fw.name, existing_fw.name))
            new_fw.add_rule(src_dest_fw=fw)
            new_fw.add_rule(src_dest_fw=existing_fw)
            nic.network_security_group.id = new_fw.resource_id

        cast("AzureCloudProvider", self._provider).azure_client. \
            update_nic(nic.id, nic)

    def remove_vm_firewall(self, firewall: VMFirewall) -> None:

        '''
        :param fw:
        :return: None

        This method removes the security group to VM instance.
        In Azure, security group added to Network interface.
        Azure supports to add only one security group to
        network interface, we are removing the provided security group
        if it associated to NIC
        else we are ignoring.
        '''

        nic = next(self._nics)
        fw: Any = (self._provider.security.vm_firewalls.get(firewall)
                   if isinstance(firewall, str) else firewall)
        if nic.network_security_group and \
                nic.network_security_group.id == fw.resource_id:
            nic.network_security_group = None
            cast("AzureCloudProvider", self._provider).azure_client. \
                update_nic(nic.id, nic)

    def _update_state(self) -> None:
        """
        Azure python sdk list operation does not return the current
        staus of the instance. We have to explicity call the get method
        for each instance to get the instance status(instance_view).
        This is the limitation with azure rest api
        :return:
        """
        if not self._vm.instance_view:
            self.refresh()
        if self._vm.instance_view and len(
                self._vm.instance_view.statuses) > 1:
            self._state = \
                self._vm.instance_view.statuses[1].display_status
        else:
            self._state = \
                self._vm.provisioning_state

    @property
    def state(self) -> str:
        return AzureInstance.INSTANCE_STATE_MAP.get(
            self._state, InstanceState.UNKNOWN)

    def refresh(self) -> None:
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._vm = cast(
                "AzureCloudProvider", self._provider).azure_client.get_vm(
                self.id)
            if not self._vm.tags:
                self._vm.tags = {}
            self._update_state()
        except (ResourceNotFoundError, ValueError) as cloud_error:
            log.exception(cloud_error)
            # The volume no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'


class AzureLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider: AzureCloudProvider) -> None:
        super(AzureLaunchConfig, self).__init__(provider)


class AzureVMType(BaseVMType):

    def __init__(self, provider: AzureCloudProvider, vm_type: Any) -> None:
        super(AzureVMType, self).__init__(provider)
        self._vm_type = vm_type

    @property
    def id(self) -> str:
        return self._vm_type.name

    @property
    def name(self) -> str:
        return self._vm_type.name

    @property
    def family(self) -> str | None:
        """
        Python sdk does not return family details.
        So, as of now populating it with 'Unknown'
        """
        return "Unknown"

    @property
    def vcpus(self) -> int:
        return self._vm_type.number_of_cores

    @property
    def ram(self) -> float:
        return int(self._vm_type.memory_in_mb) / 1024

    @property
    def size_root_disk(self) -> int:
        return self._vm_type.os_disk_size_in_mb / 1024

    @property
    def size_ephemeral_disks(self) -> int:
        return self._vm_type.resource_disk_size_in_mb / 1024

    @property
    def num_ephemeral_disks(self) -> int:
        """
        Azure by default adds one ephemeral disk. We can not add
        more ephemeral disks to VM explicitly
        So, returning it as Zero.
        """
        return 0

    @property
    def extra_data(self) -> dict[str, Any]:
        return {
                    'max_data_disk_count':
                    self._vm_type.max_data_disk_count
               }


class AzureKeyPair(BaseKeyPair):

    def __init__(self, provider: AzureCloudProvider, key_pair: Any) -> None:
        super(AzureKeyPair, self).__init__(provider, key_pair)

    @property
    def id(self) -> str:
        return self._key_pair['Name']

    @property
    def name(self) -> str:
        return self._key_pair['Name']


class AzureRouter(BaseRouter):
    def __init__(self, provider: AzureCloudProvider,
                 route_table: Any) -> None:
        super(AzureRouter, self).__init__(provider)
        self._route_table = route_table
        if not self._route_table.tags:
            self._route_table.tags = {}

    @property
    def id(self) -> str:
        route_table_id = self._route_table.id
        if not route_table_id:
            raise ProviderInternalException(
                "Route table is missing an id")
        return route_table_id

    @property
    def name(self) -> str:
        return self._route_table.name

    @property
    def resource_id(self) -> str:
        return self._route_table.id

    @property
    def label(self) -> str | None:
        """
        Get the router label.

        .. note:: the router must have a (case sensitive) tag ``Label``
        """
        return self._route_table.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value: str) -> None:
        """
        Set the router label.
        """
        self.assert_valid_resource_label(value)
        self._route_table.tags.update(Label=value or "")
        cast("AzureCloudProvider", self._provider).azure_client. \
            update_route_table_tags(self._route_table.name,
                                    self._route_table.tags)

    def refresh(self) -> None:
        self._route_table = cast(
            "AzureCloudProvider", self._provider).azure_client. \
            get_route_table(self._route_table.name)

    @property
    def state(self) -> str:
        self.refresh()  # Explicitly refresh the local object
        if self._route_table.subnets:
            return RouterState.ATTACHED
        return RouterState.DETACHED

    @property
    def network_id(self) -> str | None:
        return None

    def attach_subnet(self, subnet: Subnet | str) -> None:
        subnet_id = subnet.id if isinstance(subnet, AzureSubnet) else subnet
        cast("AzureCloudProvider", self._provider).azure_client. \
            attach_subnet_to_route_table(subnet_id,
                                         self.resource_id)
        self.refresh()

    @property
    def subnets(self) -> Iterable[Subnet]:
        if self._route_table.subnets:
            return [AzureSubnet(
                cast("AzureCloudProvider", self._provider), sn)
                for sn in self._route_table.subnets]
        return []

    def detach_subnet(self, subnet: Subnet | str) -> None:
        subnet_id = subnet.id if isinstance(subnet, AzureSubnet) else subnet
        cast("AzureCloudProvider", self._provider).azure_client. \
            detach_subnet_to_route_table(subnet_id,
                                         self.resource_id)
        self.refresh()

    def attach_gateway(self, gateway: Gateway) -> None:
        pass

    def detach_gateway(self, gateway: Gateway) -> None:
        pass


class AzureInternetGateway(BaseInternetGateway):
    def __init__(self, provider: AzureCloudProvider, gateway: Any,
                 gateway_net: AzureNetwork | str) -> None:
        super(AzureInternetGateway, self).__init__(provider)
        self._gateway = gateway
        self._network_id = gateway_net.id if isinstance(
            gateway_net, AzureNetwork) else gateway_net
        self._state = ''
        self._fips_container = AzureFloatingIPSubService(provider, self)

    @property
    def id(self) -> str:
        return "cb-gateway-wrapper"

    @property
    def name(self) -> str:
        return "cb-gateway-wrapper"

    def refresh(self) -> None:
        pass

    @property
    def state(self) -> str:
        return self._state

    @property
    def network_id(self) -> str | None:
        return self._network_id

    def delete(self) -> None:
        pass

    @property
    def floating_ips(self) -> AzureFloatingIPSubService:
        return self._fips_container


# Map Azure record-set type suffix (e.g. 'Microsoft.Network/dnszones/A')
# to cloudbridge DnsRecordType. Used to expose record data in a normalized form.
_AZURE_RECORD_TYPE_ATTR: dict[str, str] = {
    'A': 'a_records',
    'AAAA': 'aaaa_records',
    'CNAME': 'cname_record',
    'MX': 'mx_records',
    'NS': 'ns_records',
    'PTR': 'ptr_records',
    'SRV': 'srv_records',
    'TXT': 'txt_records',
}


def _azure_record_type(raw_record: Any) -> str:
    """Return the bare type (e.g. 'A') from an Azure RecordSet."""
    rec_type = raw_record.type or ''
    # Azure formats: 'Microsoft.Network/dnszones/A' or bare 'A'
    return rec_type.split('/')[-1] if '/' in rec_type else rec_type


def _azure_record_data(raw_record: Any) -> list[str]:
    """Extract the data values from an Azure RecordSet as a list of strings."""
    rt = _azure_record_type(raw_record)
    attr = _AZURE_RECORD_TYPE_ATTR.get(rt)
    if not attr:
        return []
    value = getattr(raw_record, attr, None)
    if value is None:
        return []
    if rt == 'A':
        return [r.ipv4_address for r in value]
    if rt == 'AAAA':
        return [r.ipv6_address for r in value]
    if rt == 'CNAME':
        return [value.cname]
    if rt == 'MX':
        return ['{0} {1}'.format(r.preference, r.exchange) for r in value]
    if rt == 'NS':
        return [r.nsdname for r in value]
    if rt == 'PTR':
        return [r.ptrdname for r in value]
    if rt == 'SRV':
        return ['{0} {1} {2} {3}'.format(r.priority, r.weight, r.port,
                                         r.target) for r in value]
    if rt == 'TXT':
        # Each TXT record carries a list of strings; join with spaces by convention
        return [' '.join(r.value) if isinstance(r.value, list) else r.value
                for r in value]
    return []


class AzureDnsZone(BaseDnsZone):

    def __init__(self, provider: AzureCloudProvider, dns_zone: Any) -> None:
        super(AzureDnsZone, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_record_container = AzureDnsRecordSubService(provider, self)

    @property
    def id(self) -> str:
        zone_id = self._dns_zone.name
        if not zone_id:
            raise ProviderInternalException(
                "DNS zone is missing a name")
        return zone_id

    @property
    def name(self) -> str:
        return self._dns_zone.name

    @property
    def admin_email(self) -> str | None:
        tags = self._dns_zone.tags or {}
        return tags.get('admin_email')

    @property
    def records(self) -> AzureDnsRecordSubService:
        return self._dns_record_container


class AzureDnsRecord(BaseDnsRecord):

    def __init__(self, provider: AzureCloudProvider, dns_zone: AzureDnsZone,
                 dns_record: Any) -> None:
        super(AzureDnsRecord, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_rec = dns_record

    @property
    def id(self) -> str:
        return self.name + ":" + self.type

    @property
    def name(self) -> str:
        return self._dns_rec.name

    @property
    def zone_id(self) -> str:
        zone_id = self._dns_zone.id
        if not zone_id:
            raise ProviderInternalException(
                "DNS record is missing a zone id")
        return zone_id

    @property
    def type(self) -> str:
        return _azure_record_type(self._dns_rec)

    @property
    def data(self) -> list[str]:
        return _azure_record_data(self._dns_rec)

    @property
    def ttl(self) -> int:
        return self._dns_rec.ttl

    def delete(self) -> None:
        # pylint:disable=protected-access
        records: Any = self._provider.dns._records
        records.delete(self._dns_zone, self)
