"""
DataTypes used by this provider
"""
import collections
import logging
from uuid import uuid4

from azure.common import AzureException
from azure.mgmt.devtestlabs.models import GalleryImageReference
from azure.mgmt.network.models import NetworkSecurityGroup

from msrestazure.azure_exceptions import CloudError

import pysftp

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.resources import BaseAttachmentInfo, \
    BaseBucket, BaseBucketContainer, BaseBucketObject, BaseFloatingIP, \
    BaseFloatingIPContainer, BaseGatewayContainer, BaseInstance, \
    BaseInternetGateway, BaseKeyPair, BaseLaunchConfig, \
    BaseMachineImage, BaseNetwork, BasePlacementZone, BaseRegion, BaseRouter, \
    BaseSnapshot, BaseSubnet, BaseVMFirewall, BaseVMFirewallRule, \
    BaseVMFirewallRuleContainer, BaseVMType, BaseVolume, ClientPagedResultList
from cloudbridge.cloud.interfaces import InstanceState, VolumeState
from cloudbridge.cloud.interfaces.resources import Instance, \
    MachineImageState, NetworkState, RouterState, \
    SnapshotState, SubnetState, TrafficDirection

from . import helpers as azure_helpers

log = logging.getLogger(__name__)


class AzureVMFirewall(BaseVMFirewall):
    def __init__(self, provider, vm_firewall):
        super(AzureVMFirewall, self).__init__(provider, vm_firewall)
        self._vm_firewall = vm_firewall
        self._vm_firewall.tags = self._vm_firewall.tags or {}
        self._rule_container = AzureVMFirewallRuleContainer(provider, self)

    @property
    def network_id(self):
        return None

    @property
    def resource_id(self):
        return self._vm_firewall.id

    @property
    def id(self):
        return self._vm_firewall.id

    @property
    def name(self):
        return self._vm_firewall.name

    @property
    def label(self):
        return self._vm_firewall.tags.get('Label', None)

    @label.setter
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._vm_firewall.tags.update(Label=value or "")
        self._provider.azure_client.update_vm_firewall_tags(
            self.id, self._vm_firewall.tags)

    @property
    def description(self):
        return self._vm_firewall.tags.get('Description')

    @description.setter
    def description(self, value):
        self._vm_firewall.tags.update(Description=value or "")
        self._provider.azure_client.\
            update_vm_firewall_tags(self.id,
                                    self._vm_firewall.tags)

    @property
    def rules(self):
        return self._rule_container

    def delete(self):
        self._provider.azure_client.delete_vm_firewall(self.id)

    def refresh(self):
        """
        Refreshes the security group with tags if required.
        """
        try:
            self._vm_firewall = self._provider.azure_client. \
                get_vm_firewall(self.id)
            if not self._vm_firewall.tags:
                self._vm_firewall.tags = {}
        except (CloudError, ValueError) as cloud_error:
            log.exception(cloud_error.message)
            # The security group no longer exists and cannot be refreshed.

    def to_json(self):
        js = super(AzureVMFirewall, self).to_json()
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = json_rules
        if js.get('network_id'):
            js.pop('network_id')  # Omit for consistency across cloud providers
        return js


class AzureVMFirewallRuleContainer(BaseVMFirewallRuleContainer):

    def __init__(self, provider, firewall):
        super(AzureVMFirewallRuleContainer, self).__init__(provider, firewall)

    def list(self, limit=None, marker=None):
        # Filter out firewall rules with priority < 3500 because values
        # between 3500 and 4096 are assumed to be owned by cloudbridge
        # default rules.
        # pylint:disable=protected-access
        rules = [AzureVMFirewallRule(self.firewall, rule) for rule
                 in self.firewall._vm_firewall.security_rules
                 if rule.priority < 3500]
        return ClientPagedResultList(self._provider, rules,
                                     limit=limit, marker=marker)

    def create(self, direction, protocol=None, from_port=None, to_port=None,
               cidr=None, src_dest_fw=None):
        if protocol and from_port and to_port:
            return self._create_rule(direction, protocol, from_port,
                                     to_port, cidr)
        elif src_dest_fw:
            result = None
            fw = (self._provider.security.vm_firewalls.get(src_dest_fw)
                  if isinstance(src_dest_fw, str) else src_dest_fw)
            for rule in fw.rules:
                result = self._create_rule(
                    rule.direction, rule.protocol, rule.from_port,
                    rule.to_port, rule.cidr)
            return result
        else:
            return None

    def _create_rule(self, direction, protocol, from_port, to_port, cidr):

        # If cidr is None, default values is set as 0.0.0.0/0
        if not cidr:
            cidr = '0.0.0.0/0'

        count = len(self.firewall._vm_firewall.security_rules) + 1
        rule_name = "cb-rule-" + str(count)
        priority = 1000 + count
        destination_port_range = str(from_port) + "-" + str(to_port)
        source_port_range = '*'
        destination_address_prefix = "*"
        access = "Allow"
        direction = ("Inbound" if direction == TrafficDirection.INBOUND
                     else "Outbound")
        parameters = {"priority": priority,
                      "protocol": protocol,
                      "source_port_range": source_port_range,
                      "source_address_prefix": cidr,
                      "destination_port_range": destination_port_range,
                      "destination_address_prefix": destination_address_prefix,
                      "access": access,
                      "direction": direction}
        result = self._provider.azure_client. \
            create_vm_firewall_rule(self.firewall.id,
                                    rule_name, parameters)
        # pylint:disable=protected-access
        self.firewall._vm_firewall.security_rules.append(result)
        return AzureVMFirewallRule(self.firewall, result)


# Tuple for port range
PortRange = collections.namedtuple('PortRange', ['from_port', 'to_port'])


class AzureVMFirewallRule(BaseVMFirewallRule):
    def __init__(self, parent_fw, rule):
        super(AzureVMFirewallRule, self).__init__(parent_fw, rule)

    @property
    def id(self):
        return self._rule.id

    @property
    def name(self):
        return self._rule.name

    @property
    def direction(self):
        return (TrafficDirection.INBOUND if self._rule.direction == "Inbound"
                else TrafficDirection.OUTBOUND)

    @property
    def protocol(self):
        return self._rule.protocol

    @property
    def from_port(self):
        return self._port_range_tuple.from_port

    @property
    def to_port(self):
        return self._port_range_tuple.to_port

    @property
    def _port_range_tuple(self):
        if self._rule.destination_port_range == '*':
            return PortRange(1, 65535)
        destination_port_range = self._rule.destination_port_range
        port_range_split = destination_port_range.split('-', 1)
        return PortRange(int(port_range_split[0]), int(port_range_split[1]))

    @property
    def cidr(self):
        return self._rule.source_address_prefix

    @property
    def src_dest_fw_id(self):
        return self.firewall.id

    @property
    def src_dest_fw(self):
        return self.firewall

    def delete(self):
        vm_firewall = self.firewall.name
        self._provider.azure_client. \
            delete_vm_firewall_rule(self.id, vm_firewall)
        for i, o in enumerate(self.firewall._vm_firewall.security_rules):
            if o.id == self.id:
                del self.firewall._vm_firewall.security_rules[i]
                break


class AzureBucketObject(BaseBucketObject):
    def __init__(self, provider, container, key):
        super(AzureBucketObject, self).__init__(provider)
        self._container = container
        self._key = key

    @property
    def id(self):
        return self._key.name

    @property
    def name(self):
        return self._key.name

    @property
    def size(self):
        """
        Get this object's size.
        """
        return self._key.properties.content_length

    @property
    def last_modified(self):

        """
        Get the date and time this object was last modified.
        """
        return self._key.properties.last_modified. \
            strftime("%Y-%m-%dT%H:%M:%S.%f")

    def iter_content(self):
        """
        Returns this object's content as an
        iterable.
        """
        content_stream = self._provider.azure_client. \
            get_blob_content(self._container.id, self._key.name)
        if content_stream:
            content_stream.seek(0)
        return content_stream

    def upload(self, data):
        """
        Set the contents of this object to the data read from the source
        string.
        """
        try:
            self._provider.azure_client.create_blob_from_text(
                self._container.id, self.id, data)
            return True
        except AzureException as azureEx:
            log.exception(azureEx)
            return False

    def upload_from_file(self, path):
        """
        Store the contents of the file pointed by the "path" variable.
        """
        try:
            self._provider.azure_client.create_blob_from_file(
                self._container.id, self.id, path)
            return True
        except AzureException as azureEx:
            log.exception(azureEx)
            return False

    def delete(self):
        """
        Delete this object.

        :rtype: bool
        :return: True if successful
        """
        self._provider.azure_client.delete_blob(self._container.id,
                                                self.id)

    def generate_url(self, expires_in):
        """
        Generate a URL to this object.
        """
        return self._provider.azure_client.get_blob_url(
            self._container.id, self.id, expires_in)

    def refresh(self):
        self._key = self._provider.azure_client.get_blob(
            self._container.id, self._key.id)


class AzureBucket(BaseBucket):
    def __init__(self, provider, bucket):
        super(AzureBucket, self).__init__(provider)
        self._bucket = bucket
        self._object_container = AzureBucketContainer(provider, self)

    @property
    def id(self):
        return self._bucket.name

    @property
    def name(self):
        """
        Get this bucket's name.
        """
        return self._bucket.name

    def delete(self, delete_contents=True):
        """
        Delete this bucket.
        """
        self._provider.azure_client.delete_container(self.name)

    def exists(self, name):
        """
        Determine if an object with given name exists in this bucket.
        """
        return True if self.get(name) else False

    @property
    def objects(self):
        return self._object_container


class AzureBucketContainer(BaseBucketContainer):

    def __init__(self, provider, bucket):
        super(AzureBucketContainer, self).__init__(provider, bucket)

    def get(self, key):
        """
        Retrieve a given object from this bucket.
        """
        try:
            obj = self._provider.azure_client.get_blob(self.bucket.name,
                                                       key)
            return AzureBucketObject(self._provider, self.bucket, obj)
        except AzureException as azureEx:
            log.exception(azureEx)
            return None

    def list(self, limit=None, marker=None, prefix=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        objects = [AzureBucketObject(self._provider, self.bucket, obj)
                   for obj in
                   self._provider.azure_client.list_blobs(
                       self.bucket.name, prefix=prefix)]
        return ClientPagedResultList(self._provider, objects,
                                     limit=limit, marker=marker)

    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def create(self, name):
        self._provider.azure_client.create_blob_from_text(
            self.bucket.name, name, '')
        return self.get(name)


class AzureVolume(BaseVolume):
    VOLUME_STATE_MAP = {
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

    def __init__(self, provider, volume):
        super(AzureVolume, self).__init__(provider)
        self._volume = volume
        self._description = None
        self._state = 'unknown'
        self._update_state()
        if not self._volume.tags:
            self._volume.tags = {}

    def _update_state(self):
        if not self._volume.provisioning_state == 'Succeeded':
            self._state = self._volume.provisioning_state
        elif self._volume.managed_by:
            self._state = 'Attached'
        else:
            self._state = 'Unattached'

    @property
    def id(self):
        return self._volume.id

    @property
    def resource_id(self):
        return self._volume.id

    @property
    def name(self):
        return self._volume.name

    @property
    def tags(self):
        return self._volume.tags

    @property
    def label(self):
        """
        Get the volume label.

        .. note:: an instance must have a (case sensitive) tag ``Label``
        """
        return self._volume.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the volume label.
        """
        self.assert_valid_resource_label(value)
        self._volume.tags.update(Label=value or "")
        self._provider.azure_client. \
            update_disk_tags(self.id,
                             self._volume.tags)

    @property
    def description(self):
        return self._volume.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._volume.tags.update(Description=value or "")
        self._provider.azure_client. \
            update_disk_tags(self.id,
                             self._volume.tags)

    @property
    def size(self):
        return self._volume.disk_size_gb

    @property
    def create_time(self):
        return self._volume.time_created.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @property
    def zone_id(self):
        return self._volume.location

    @property
    def source(self):
        return self._volume.creation_data.source_uri

    @property
    def attachments(self):
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

    def attach(self, instance, device=None):
        """
        Attach this volume to an instance.
        """
        instance_id = instance.id if isinstance(
            instance,
            Instance) else instance
        vm = self._provider.azure_client.get_vm(instance_id)

        vm.storage_profile.data_disks.append({
            'lun': len(vm.storage_profile.data_disks),
            'name': self._volume.name,
            'create_option': 'attach',
            'managed_disk': {
                'id': self.resource_id
            }
        })
        self._provider.azure_client.update_vm(instance_id, vm)

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        for vm in self._provider.azure_client.list_vm():
            for item in vm.storage_profile.data_disks:
                if item.managed_disk and \
                        item.managed_disk.id == self.resource_id:
                    vm.storage_profile.data_disks.remove(item)
                    self._provider.azure_client.update_vm(vm.id, vm)

    def create_snapshot(self, label, description=None):
        """
        Create a snapshot of this Volume.
        """
        return self._provider.storage.snapshots.create(label, self,
                                                       description)

    def delete(self):
        """
        Delete this volume.
        """
        self._provider.azure_client.delete_disk(self.id)

    @property
    def state(self):
        return AzureVolume.VOLUME_STATE_MAP.get(
            self._state, VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._volume = self._provider.azure_client. \
                get_disk(self.id)
            self._update_state()
        except (CloudError, ValueError) as cloud_error:
            log.exception(cloud_error.message)
            # The volume no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'


class AzureSnapshot(BaseSnapshot):
    SNAPSHOT_STATE_MAP = {
        'InProgress': SnapshotState.PENDING,
        'Succeeded': SnapshotState.AVAILABLE,
        'Failed': SnapshotState.ERROR,
        'Canceled': SnapshotState.ERROR,
        'Updating': SnapshotState.CONFIGURING,
        'Deleting': SnapshotState.CONFIGURING,
        'Deleted': SnapshotState.UNKNOWN
    }

    def __init__(self, provider, snapshot):
        super(AzureSnapshot, self).__init__(provider)
        self._snapshot = snapshot
        self._description = None
        self._state = self._snapshot.provisioning_state
        if not self._snapshot.tags:
            self._snapshot.tags = {}

    @property
    def id(self):
        return self._snapshot.id

    @property
    def name(self):
        return self._snapshot.name

    @property
    def resource_id(self):
        return self._snapshot.id

    @property
    def label(self):
        """
        Get the snapshot label.

        .. note:: an instance must have a (case sensitive) tag ``Label``
        """
        return self._snapshot.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the snapshot label.
        """
        self.assert_valid_resource_label(value)
        self._snapshot.tags.update(Label=value or "")
        self._provider.azure_client. \
            update_snapshot_tags(self.id,
                                 self._snapshot.tags)

    @property
    def description(self):
        return self._snapshot.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._snapshot.tags.update(Description=value or "")
        self._provider.azure_client. \
            update_snapshot_tags(self.id,
                                 self._snapshot.tags)

    @property
    def size(self):
        return self._snapshot.disk_size_gb

    @property
    def volume_id(self):
        return self._snapshot.creation_data.source_resource_id

    @property
    def create_time(self):
        return self._snapshot.time_created.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @property
    def state(self):
        return AzureSnapshot.SNAPSHOT_STATE_MAP.get(
            self._state, SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._snapshot = self._provider.azure_client. \
                get_snapshot(self.id)
            self._state = self._snapshot.provisioning_state
        except (CloudError, ValueError) as cloud_error:
            log.exception(cloud_error.message)
            # The snapshot no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'

    def delete(self):
        """
        Delete this snapshot.
        """
        self._provider.azure_client.delete_snapshot(self.id)

    def create_volume(self, placement=None,
                      size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.
        """
        return self._provider.storage.volumes. \
            create(self.name, self.size, zone=placement, snapshot=self)


class AzureMachineImage(BaseMachineImage):
    IMAGE_STATE_MAP = {
        'InProgress': MachineImageState.PENDING,
        'Succeeded': MachineImageState.AVAILABLE,
        'Failed': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
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
    def id(self):
        """
        Get the image identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            return self._image.id

    @property
    def name(self):
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            return self._image.name

    @property
    def resource_id(self):
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            return self._image.id

    @property
    def label(self):
        if self.is_gallery_image:
            return azure_helpers.generate_urn(self._image)
        else:
            return self._image.tags.get('Label', None)

    @label.setter
    def label(self, value):
        """
        Set the image label when it is a private image.
        """
        if not self.is_gallery_image:
            self.assert_valid_resource_label(value)
            self._image.tags.update(Label=value or "")
            self._provider.azure_client. \
                update_image_tags(self.id, self._image.tags)

    @property
    def description(self):
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
    def description(self, value):
        """
        Set the image description.
        """
        if not self.is_gallery_image:
            self._image.tags.update(Description=value or "")
            self._provider.azure_client. \
                update_image_tags(self.id, self._image.tags)

    @property
    def min_disk(self):
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

    def delete(self):
        """
        Delete this image
        """
        if not self.is_gallery_image:
            self._provider.azure_client.delete_image(self.id)

    @property
    def state(self):
        if self.is_gallery_image:
            return MachineImageState.AVAILABLE
        else:
            return AzureMachineImage.IMAGE_STATE_MAP.get(
                self._state, MachineImageState.UNKNOWN)

    @property
    def is_gallery_image(self):
        """
        Returns true if the image is a public reference and false if it
        is a private image in the resource group.
        """
        return isinstance(self._image, GalleryImageReference)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        if not self.is_gallery_image:
            try:
                self._image = self._provider.azure_client.get_image(self.id)
                self._state = self._image.provisioning_state
            except CloudError as cloud_error:
                log.exception(cloud_error.message)
                # image no longer exists
                self._state = "unknown"


class AzureGatewayContainer(BaseGatewayContainer):
    def __init__(self, provider, network):
        super(AzureGatewayContainer, self).__init__(provider, network)
        # Azure doesn't have a notion of a route table or an internet
        # gateway as OS and AWS so create placeholder objects of the
        # AzureInternetGateway here.
        # http://bit.ly/2BqGdVh
        # Singleton returned by the list method
        self.gateway_singleton = AzureInternetGateway(self._provider, None,
                                                      network)

    def get_or_create_inet_gateway(self):
        gateway = AzureInternetGateway(self._provider, None, self._network)
        return gateway

    def list(self, limit=None, marker=None):
        return [self.gateway_singleton]

    def delete(self, gateway):
        pass


class AzureNetwork(BaseNetwork):
    NETWORK_STATE_MAP = {
        'InProgress': NetworkState.PENDING,
        'Succeeded': NetworkState.AVAILABLE,
    }

    def __init__(self, provider, network):
        super(AzureNetwork, self).__init__(provider)
        self._network = network
        self._state = self._network.provisioning_state
        if not self._network.tags:
            self._network.tags = {}
        self._gateway_service = AzureGatewayContainer(provider, self)

    @property
    def id(self):
        return self._network.id

    @property
    def name(self):
        return self._network.name

    @property
    def resource_id(self):
        return self._network.id

    @property
    def label(self):
        """
        Get the network label.

        .. note:: the network must have a (case sensitive) tag ``Label``
        """
        return self._network.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the network label.
        """
        self.assert_valid_resource_label(value)
        self._network.tags.update(Label=value or "")
        self._provider.azure_client. \
            update_network_tags(self.id, self._network)

    @property
    def external(self):
        """
        For Azure, all VPC networks can be connected to the Internet so always
        return ``True``.
        """
        return True

    @property
    def state(self):
        return AzureNetwork.NETWORK_STATE_MAP.get(
            self._state, NetworkState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this network by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._network = self._provider.azure_client.\
                get_network(self.id)
            self._state = self._network.provisioning_state
        except (CloudError, ValueError) as cloud_error:
            log.exception(cloud_error.message)
            # The network no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'

    @property
    def cidr_block(self):
        """
        Address space associated with this network
        :return:
        """
        return self._network.address_space.address_prefixes[0]

    def delete(self):
        """
        Delete an existing network.
        """
        self._provider.azure_client.delete_network(self.id)

    @property
    def subnets(self):
        """
        List all the subnets in this network
        :return:
        """
        return self._provider.networking.subnets.list(network=self.id)

    def create_subnet(self, label, cidr_block, zone=None):
        """
        Create the subnet with cidr_block
        :param cidr_block:
        :param label:
        :param zone:
        :return:
        """
        return self._provider.networking.subnets. \
            create(label=label, network=self.id, cidr_block=cidr_block)

    @property
    def gateways(self):
        return self._gateway_service


class AzureFloatingIPContainer(BaseFloatingIPContainer):

    def __init__(self, provider, gateway, network_id):
        super(AzureFloatingIPContainer, self).__init__(provider, gateway)
        self._network_id = network_id

    def get(self, fip_id):
        log.debug("Getting Azure Floating IP container with the id: %s",
                  fip_id)
        fip = [fip for fip in self if fip.id == fip_id]
        return fip[0] if fip else None

    def list(self, limit=None, marker=None):
        floating_ips = [AzureFloatingIP(self._provider, floating_ip,
                                        self._network_id)
                        for floating_ip in self._provider.azure_client.
                        list_floating_ips()]
        return ClientPagedResultList(self._provider, floating_ips,
                                     limit=limit, marker=marker)

    def create(self):
        public_ip_parameters = {
            'location': self._provider.azure_client.region_name,
            'public_ip_allocation_method': 'Static'
        }

        public_ip_name = 'cb-fip-' + uuid4().hex[:6]

        floating_ip = self._provider.azure_client.\
            create_floating_ip(public_ip_name, public_ip_parameters)
        return AzureFloatingIP(self._provider, floating_ip, self._network_id)


class AzureFloatingIP(BaseFloatingIP):

    def __init__(self, provider, floating_ip, network_id):
        super(AzureFloatingIP, self).__init__(provider)
        self._ip = floating_ip
        self._network_id = network_id

    @property
    def id(self):
        return self._ip.id

    @property
    def name(self):
        return self._ip.ip_address

    @property
    def resource_id(self):
        return self._ip.id

    @property
    def public_ip(self):
        return self._ip.ip_address

    @property
    def private_ip(self):
        return self._ip.ip_configuration.private_ip_address \
            if self._ip.ip_configuration else None

    @property
    def in_use(self):
        return True if self._ip.ip_configuration else False

    def delete(self):
        """
        Delete an existing floating ip.
        """
        self._provider.azure_client.delete_floating_ip(self.id)

    def refresh(self):
        net = self._provider.networking.networks.get(self._network_id)
        gw = net.gateways.get_or_create_inet_gateway()
        fip = gw.floating_ips.get(self.id)
        self._ip = fip._ip


class AzureRegion(BaseRegion):
    def __init__(self, provider, azure_region):
        super(AzureRegion, self).__init__(provider)
        self._azure_region = azure_region

    @property
    def id(self):
        return self._azure_region.name

    @property
    def name(self):
        return self._azure_region.name

    @property
    def zones(self):
        """
            Access information about placement zones within this region.
            As Azure does not have this feature, mapping the region
            name as zone id and name.
        """
        return [AzurePlacementZone(self._provider,
                                   self._azure_region.name,
                                   self._azure_region.name)]


class AzurePlacementZone(BasePlacementZone):
    """
    As Azure does not provide zones (limited support), we are mapping the
    region information in the zones.
    """
    def __init__(self, provider, zone, region):
        super(AzurePlacementZone, self).__init__(provider)
        self._azure_zone = zone
        self._azure_region = region

    @property
    def id(self):
        """
            Get the zone id
            :rtype: ``str``
            :return: ID for this zone as returned by the cloud middleware.
        """
        return self._azure_zone

    @property
    def name(self):
        """
            Get the zone name.
            :rtype: ``str``
            :return: Name for this zone as returned by the cloud middleware.
        """
        return self._azure_region

    @property
    def region_name(self):
        """
            Get the region that this zone belongs to.
            :rtype: ``str``
            :return: Name of this zone's region as returned by the
            cloud middleware
        """
        return self._azure_region


class AzureSubnet(BaseSubnet):
    _SUBNET_STATE_MAP = {
        'InProgress': SubnetState.PENDING,
        'Succeeded': SubnetState.AVAILABLE,
    }

    def __init__(self, provider, subnet):
        super(AzureSubnet, self).__init__(provider)
        self._subnet = subnet
        self._state = self._subnet.provisioning_state
        self._tag_name = None

    @property
    def id(self):
        return self._subnet.id

    @property
    def name(self):
        net_name = self.network_id.split('/')[-1]
        sn_name = self._subnet.name
        return '{0}/{1}'.format(net_name, sn_name)

    @property
    def label(self):
        # Although Subnet doesn't support labels, we use the parent Network's
        # tags to track the subnet's labels
        network = self._network
        az_network = network._network
        return az_network.tags.get(self.tag_name, None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        network = self._network
        az_network = network._network
        kwargs = {self.tag_name: value or ""}
        az_network.tags.update(**kwargs)
        self._provider.azure_client.update_network_tags(
            az_network.id, az_network)

    @property
    def tag_name(self):
        if not self._tag_name:
            self._tag_name = 'SubnetLabel_{0}'.format(self._subnet.name)
        return self._tag_name

    @property
    def resource_id(self):
        return self._subnet.id

    @property
    def zone(self):
        # pylint:disable=protected-access
        region = self._provider.compute.regions.get(
            self._network._network.location)
        return region.zones[0]

    @property
    def cidr_block(self):
        return self._subnet.address_prefix

    @property
    def network_id(self):
        return self._provider.azure_client.get_network_id_for_subnet(self.id)

    @property
    def _network(self):
        return self._provider.networking.networks.get(self.network_id)

    def delete(self):
        self._provider.azure_client.delete_subnet(self.id)

    @property
    def state(self):
        return self._SUBNET_STATE_MAP.get(self._state, NetworkState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this network by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._subnet = self._provider.azure_client. \
                get_subnet(self.id)
            self._state = self._subnet.provisioning_state
        except (CloudError, ValueError) as cloud_error:
            log.exception(cloud_error.message)
            # The subnet no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'


class AzureInstance(BaseInstance):

    INSTANCE_STATE_MAP = {
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

    def __init__(self, provider, vm_instance):
        super(AzureInstance, self).__init__(provider)
        self._vm = vm_instance
        self._update_state()
        if not self._vm.tags:
            self._vm.tags = {}

    @property
    def _nic_ids(self):
        return (nic.id for nic in self._vm.network_profile.network_interfaces)

    @property
    def _nics(self):
        return (self._provider.azure_client.get_nic(nic_id)
                for nic_id in self._nic_ids)

    @property
    def _public_ip_ids(self):
        return (ip_config.public_ip_address.id
                for nic in self._nics
                for ip_config in nic.ip_configurations
                if nic.ip_configurations and ip_config.public_ip_address)

    @property
    def id(self):
        """
        Get the instance identifier.
        """
        return self._vm.id

    @property
    def name(self):
        """
        Get the instance name.
        """
        return self._vm.name

    @property
    def resource_id(self):
        return self._vm.id

    @property
    def label(self):
        """
        Get the instance label.

        .. note:: an instance must have a (case sensitive) tag ``Label``
        """
        return self._vm.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the instance label.
        """
        self.assert_valid_resource_label(value)
        self._vm.tags.update(Label=value or "")
        self._provider.azure_client. \
            update_vm_tags(self.id, self._vm)

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        return [self._provider.azure_client.get_floating_ip(pip).ip_address
                for pip in self._public_ip_ids]

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return [ip_config.private_ip_address
                for nic in self._nics
                for ip_config in nic.ip_configurations
                if nic.ip_configurations and ip_config.private_ip_address]

    @property
    def vm_type_id(self):
        """
        Get the instance type name.
        """
        return self._vm.hardware_profile.vm_size

    @property
    def vm_type(self):
        """
        Get the instance type.
        """
        return self._provider.compute.vm_types.find(
            name=self.vm_type_id)[0]

    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).
        """
        self._provider.azure_client.restart_vm(self.id)

    def delete(self):
        """
        Permanently terminate this instance.
        After deleting the VM. we are deleting the network interface
        associated to the instance, public ip addresses associated to
        the instance and also removing OS disk and data disks where
        tag with name 'delete_on_terminate' has value True.
        """
        self._provider.azure_client.deallocate_vm(self.id)
        self._provider.azure_client.delete_vm(self.id)
        for public_ip_id in self._public_ip_ids:
            self._provider.azure_client.delete_floating_ip(public_ip_id)
        for nic_id in self._nic_ids:
            self._provider.azure_client.delete_nic(nic_id)
        for data_disk in self._vm.storage_profile.data_disks:
            if data_disk.managed_disk:
                if self._vm.tags.get('delete_on_terminate',
                                     'False') == 'True':
                    self._provider.azure_client.\
                        delete_disk(data_disk.managed_disk.id)
        if self._vm.storage_profile.os_disk.managed_disk:
            self._provider.azure_client. \
                delete_disk(self._vm.storage_profile.os_disk.managed_disk.id)

    @property
    def image_id(self):
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
    def zone_id(self):
        """
        Get the placement zone id where this instance is running.
        """
        return self._vm.location

    @property
    def subnet_id(self):
        """
        Return the first subnet id associated with the first network iface.

        An Azure instance can have multiple network interfaces attached with
        each interface having at most one subnet. This method will return only
        the subnet of the first attached network interface.
        """
        for nic_id in self._nic_ids:
            nic = self._provider.azure_client.get_nic(nic_id)
            for ipc in nic.ip_configurations:
                return ipc.subnet.id

    @property
    def vm_firewalls(self):
        return [self._provider.security.vm_firewalls.get(group_id)
                for group_id in self.vm_firewall_ids]

    @property
    def vm_firewall_ids(self):
        return [nic.network_security_group.id
                for nic in self._nics
                if nic.network_security_group]

    @property
    def key_pair_id(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return self._vm.tags.get('Key_Pair')

    def create_image(self, label, private_key_path=None):
        """
        Create a new image based on this instance. Documentation for create
        image available at https://docs.microsoft.com/en-us/azure/virtual-ma
        chines/linux/capture-image. In azure, we need to deprovision the VM
        before capturing.
        To deprovision, login to the VM and execute the `waagent deprovision`
        command. To do this programmatically, use pysftp to ssh into the VM
        and executing deprovision command. To SSH into the VM programmatically
        however, we need to pass private key file path, so we have modified the
        CloudBridge interface to pass the private key file path
        """

        self.assert_valid_resource_label(label)
        name = self._generate_name_from_label(label, 'cb-img')

        if not self._state == 'VM generalized':
            if not self._state == 'VM running':
                self._provider.azure_client.start_vm(self.id)

            # if private_key_path:
            self._deprovision(private_key_path)
            self._provider.azure_client.deallocate_vm(self.id)
            self._provider.azure_client.generalize_vm(self.id)

        create_params = {
            'location': self._provider.region_name,
            'source_virtual_machine': {
                'id': self.resource_id
            },
            'tags': {'Label': label}
        }

        image = self._provider.azure_client.create_image(name,
                                                         create_params)
        return AzureMachineImage(self._provider, image)

    def _deprovision(self, private_key_path):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        if private_key_path:
            with pysftp.\
                    Connection(self.public_ips[0],
                               username=self._provider.vm_default_user_name,
                               cnopts=cnopts,
                               private_key=private_key_path) as sftp:
                sftp.execute('sudo waagent -deprovision -force')
                sftp.close()

    def add_floating_ip(self, floating_ip):
        """
        Attaches public ip to the instance.
        """
        floating_ip_id = floating_ip.id if isinstance(
            floating_ip, AzureFloatingIP) else floating_ip
        nic = next(self._nics)
        nic.ip_configurations[0].public_ip_address = {
            'id': floating_ip_id
        }
        self._provider.azure_client.update_nic(nic.id, nic)

    def remove_floating_ip(self, floating_ip):
        """
        Remove a public IP address from this instance.
        """
        floating_ip_id = floating_ip.id if isinstance(
            floating_ip, AzureFloatingIP) else floating_ip
        nic = next(self._nics)
        for ip_config in nic.ip_configurations:
            if ip_config.public_ip_address.id == floating_ip_id:
                nic.ip_configurations[0].public_ip_address = None
                self._provider.azure_client.update_nic(nic.id, nic)

    def add_vm_firewall(self, fw):
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
        fw = (self._provider.security.vm_firewalls.get(fw)
              if isinstance(fw, str) else fw)
        nic = next(self._nics)
        if not nic.network_security_group:
            nic.network_security_group = NetworkSecurityGroup()
            nic.network_security_group.id = fw.resource_id
        else:
            existing_fw = self._provider.security.\
                vm_firewalls.get(nic.network_security_group.id)
            new_fw = self._provider.security.vm_firewalls.\
                create('{0}-{1}'.format(fw.name, existing_fw.name),
                       'Merged security groups {0} and {1}'.
                       format(fw.name, existing_fw.name))
            new_fw.add_rule(src_dest_fw=fw)
            new_fw.add_rule(src_dest_fw=existing_fw)
            nic.network_security_group.id = new_fw.resource_id

        self._provider.azure_client.update_nic(nic.id, nic)

    def remove_vm_firewall(self, fw):

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
        fw = (self._provider.security.vm_firewalls.get(fw)
              if isinstance(fw, str) else fw)
        if nic.network_security_group and \
                nic.network_security_group.id == fw.resource_id:
            nic.network_security_group = None
            self._provider.azure_client.update_nic(nic.id, nic)

    def _update_state(self):
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
    def state(self):
        return AzureInstance.INSTANCE_STATE_MAP.get(
            self._state, InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._vm = self._provider.azure_client.get_vm(self.id)
            if not self._vm.tags:
                self._vm.tags = {}
            self._update_state()
        except (CloudError, ValueError) as cloud_error:
            log.exception(cloud_error.message)
            # The volume no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'


class AzureLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider):
        super(AzureLaunchConfig, self).__init__(provider)


class AzureVMType(BaseVMType):

    def __init__(self, provider, vm_type):
        super(AzureVMType, self).__init__(provider)
        self._vm_type = vm_type

    @property
    def id(self):
        return self._vm_type.name

    @property
    def name(self):
        return self._vm_type.name

    @property
    def family(self):
        """
        Python sdk does not return family details.
        So, as of now populating it with 'Unknown'
        """
        return "Unknown"

    @property
    def vcpus(self):
        return self._vm_type.number_of_cores

    @property
    def ram(self):
        return int(self._vm_type.memory_in_mb) / 1024

    @property
    def size_root_disk(self):
        return self._vm_type.os_disk_size_in_mb / 1024

    @property
    def size_ephemeral_disks(self):
        return self._vm_type.resource_disk_size_in_mb / 1024

    @property
    def num_ephemeral_disks(self):
        """
        Azure by default adds one ephemeral disk. We can not add
        more ephemeral disks to VM explicitly
        So, returning it as Zero.
        """
        return 0

    @property
    def extra_data(self):
        return {
                    'max_data_disk_count':
                    self._vm_type.max_data_disk_count
               }


class AzureKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(AzureKeyPair, self).__init__(provider, key_pair)

    @property
    def id(self):
        return self._key_pair.Name

    @property
    def name(self):
        return self._key_pair.Name

    def delete(self):
        self._provider.azure_client.delete_public_key(self._key_pair)


class AzureRouter(BaseRouter):
    def __init__(self, provider, route_table):
        super(AzureRouter, self).__init__(provider)
        self._route_table = route_table
        if not self._route_table.tags:
            self._route_table.tags = {}

    @property
    def id(self):
        return self._route_table.id

    @property
    def name(self):
        return self._route_table.name

    @property
    def resource_id(self):
        return self._route_table.id

    @property
    def label(self):
        """
        Get the router label.

        .. note:: the router must have a (case sensitive) tag ``Label``
        """
        return self._route_table.tags.get('Label', None)

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        """
        Set the router label.
        """
        self.assert_valid_resource_label(value)
        self._route_table.tags.update(Label=value or "")
        self._provider.azure_client. \
            update_route_table_tags(self._route_table.name,
                                    self._route_table)

    def refresh(self):
        self._route_table = self._provider.azure_client. \
            get_route_table(self._route_table.name)

    @property
    def state(self):
        self.refresh()  # Explicitly refresh the local object
        if self._route_table.subnets:
            return RouterState.ATTACHED
        return RouterState.DETACHED

    @property
    def network_id(self):
        return None

    def delete(self):
        self._provider.azure_client.delete_route_table(self.name)

    def attach_subnet(self, subnet):
        self._provider.azure_client. \
            attach_subnet_to_route_table(subnet.id,
                                         self.resource_id)
        self.refresh()

    @property
    def subnets(self):
        if self._route_table.subnets:
            return [AzureSubnet(self._provider, sn)
                    for sn in self._route_table.subnets]
        return []

    def detach_subnet(self, subnet):
        self._provider.azure_client. \
            detach_subnet_to_route_table(subnet.id,
                                         self.resource_id)
        self.refresh()

    def attach_gateway(self, gateway):
        pass

    def detach_gateway(self, gateway):
        pass


class AzureInternetGateway(BaseInternetGateway):
    def __init__(self, provider, gateway, gateway_net):
        super(AzureInternetGateway, self).__init__(provider)
        self._gateway = gateway
        self._network_id = gateway_net.id if isinstance(
            gateway_net, AzureNetwork) else gateway_net
        self._state = ''
        self._fips_container = AzureFloatingIPContainer(
            provider, self, self._network_id)

    @property
    def id(self):
        return "cb-gateway-wrapper"

    @property
    def name(self):
        return "cb-gateway-wrapper"

    def refresh(self):
        pass

    @property
    def state(self):
        return self._state

    @property
    def network_id(self):
        return self._network_id

    def delete(self):
        pass

    @property
    def floating_ips(self):
        return self._fips_container
