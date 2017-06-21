"""
DataTypes used by this provider
"""
import inspect
import json
import logging
import time


from azure.common import AzureException

from azure.mgmt.network.models import NetworkSecurityGroup

from cloudbridge.cloud.base.resources import BaseAttachmentInfo, \
    BaseBucket, BaseBucketObject, BaseFloatingIP, \
    BaseInstance, BaseInstanceType, BaseKeyPair,\
    BaseLaunchConfig, BaseMachineImage, BaseNetwork, \
    BasePlacementZone, BaseRegion, BaseSecurityGroup, \
    BaseSecurityGroupRule, BaseSnapshot, BaseSubnet, \
    BaseVolume, ClientPagedResultList
from cloudbridge.cloud.interfaces import InstanceState, VolumeState
from cloudbridge.cloud.interfaces.resources import Instance, \
    MachineImageState, NetworkState, SnapshotState
from cloudbridge.cloud.providers.azure import helpers as azure_helpers

from msrestazure.azure_exceptions import CloudError

import pysftp

log = logging.getLogger(__name__)

NETWORK_INTERFACE_RESOURCE_ID = '/subscriptions/{subscriptionId}/' \
                                'resourceGroups/{resourceGroupName}' \
                                '/providers/Microsoft.Network/' \
                                'networkInterfaces/{networkInterfaceName}'
PUBLIC_IP_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups' \
                        '/{resourceGroupName}/providers/Microsoft.Network' \
                        '/publicIPAddresses/{publicIpAddressName}'
SUBNET_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                     '{resourceGroupName}/providers/Microsoft.Network' \
                     '/virtualNetworks/{virtualNetworkName}/subnets' \
                     '/{subnetName}'
VOLUME_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                     '{resourceGroupName}/providers/Microsoft.Compute/' \
                     'disks/{diskName}'
SECURITY_GROUP_RESOURCE_ID = '/subscriptions/{subscriptionId}/' \
                             'resourceGroups/{resourceGroupName}/' \
                             'providers/Microsoft.Network/' \
                             'networkSecurityGroups/' \
                             '{networkSecurityGroupName}'
SNAPSHOT_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                       '{resourceGroupName}/providers/Microsoft.Compute/' \
                       'snapshots/{snapshotName}'
IMAGE_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                    '{resourceGroupName}/providers/Microsoft.Compute/' \
                    'images/{imageName}'
INSTANCE_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                       '{resourceGroupName}/providers/Microsoft.Compute/' \
                       'virtualMachines/{vmName}'

NETWORK_NAME = 'virtualNetworkName'
NETWORK_INTERFACE_NAME = 'networkInterfaceName'
PUBLIC_IP_NAME = 'publicIpAddressName'
IMAGE_NAME = 'imageName'
VM_NAME = 'vmName'
VOLUME_NAME = 'diskName'
SECURITY_GROUP_NAME = 'networkSecurityGroupName'
SNAPSHOT_NAME = 'snapshotName'


class AzureSecurityGroup(BaseSecurityGroup):
    def __init__(self, provider, security_group):
        super(AzureSecurityGroup, self).__init__(provider, security_group)
        self._security_group = security_group
        if not self._security_group.tags:
            self._security_group.tags = {}

    @property
    def network_id(self):
        return None

    @property
    def resource_id(self):
        return self._security_group.id

    @property
    def id(self):
        return self._security_group.name

    @property
    def name(self):
        return self._security_group.tags.get('Name', self._security_group.name)

    @name.setter
    def name(self, value):
        self._security_group.tags.update(Name=value)
        self._provider.azure_client. \
            update_security_group_tags(self.id,
                                       self._security_group.tags)

    @property
    def description(self):
        return self._security_group.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._security_group.tags.update(Description=value)
        self._provider.azure_client.\
            update_security_group_tags(self.id,
                                       self._security_group.tags)

    @property
    def rules(self):
        """
        The default rules are not returned, only custom rules.
        """
        security_group_rules = []
        for custom_rule in self._security_group.security_rules:
            sg_custom_rule = AzureSecurityGroupRule(self._provider,
                                                    custom_rule, self)
            security_group_rules.append(sg_custom_rule)
        return security_group_rules

    def delete(self):
        try:
            self._provider.azure_client.\
                delete_security_group(self.id)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

    def add_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        """
        Create a security group rule.

        You need to pass in either ``src_group`` OR ``ip_protocol``,
        ``from_port``, ``to_port``, and ``cidr_ip``.  In other words, either
        you are authorizing another group or you are authorizing some
        ip-based rule.

        :type ip_protocol: str
        :param ip_protocol: Either ``tcp`` | ``udp`` | ``icmp``

        :type from_port: int
        :param from_port: The beginning port number you are enabling

        :type to_port: int
        :param to_port: The ending port number you are enabling

        :type cidr_ip: str or list of strings
        :param cidr_ip: The CIDR block you are providing access to.

        :type src_group: ``object`` of :class:`.SecurityGroup`
        :param src_group: The Security Group you are granting access to.

        :rtype: :class:``.SecurityGroupRule``
        :return: Rule object if successful or ``None``.
        """

        # If cidr_ip is None, default values is set as 0.0.0.0/0
        if not cidr_ip:
            cidr_ip = '0.0.0.0/0'

        # If the SG with same parameters exist already,
        # then, it is returned instead of creating a new one.
        rule = self.get_rule(ip_protocol, from_port,
                             to_port, cidr_ip, src_group)
        if not rule:
            # resource_group = self._provider.resource_group
            count = len(self.rules) + 1
            rule_name = "Rule - " + str(count)
            priority = count * 100
            destination_port_range = "*"
            destination_address_prefix = "*"
            access = "Allow"
            direction = "Inbound"
            parameters = {"protocol": ip_protocol,
                          "source_port_range":
                              str(from_port) + "-" + str(to_port),
                          "destination_port_range": destination_port_range,
                          "priority": priority,
                          "source_address_prefix": cidr_ip,
                          "destination_address_prefix":
                              destination_address_prefix,
                          "access": access, "direction": direction}
            result = self._provider.azure_client. \
                create_security_group_rule(self.id,
                                           rule_name, parameters)
            self._security_group.security_rules.append(result)
            return AzureSecurityGroupRule(self._provider, result, self)

        return rule

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        for rule in self.rules:
            if (rule.ip_protocol == ip_protocol and
                rule.from_port == str(from_port) and
                rule.to_port == str(to_port) and
                    rule.cidr_ip == cidr_ip):
                return rule
        return None

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = [json.loads(r) for r in json_rules]
        if js.get('network_id'):
            js.pop('network_id')  # Omit for consistency across cloud providers
        return json.dumps(js, sort_keys=True)


class AzureSecurityGroupRule(BaseSecurityGroupRule):
    def __init__(self, provider, rule, parent):
        super(AzureSecurityGroupRule, self).__init__(provider, rule, parent)

    @property
    def id(self):
        return self._rule.name

    @property
    def name(self):
        return self._rule.name

    @property
    def ip_protocol(self):
        return self._rule.protocol

    @property
    def from_port(self):
        if self._rule.source_port_range == '*':
            return self._rule.source_port_range
        source_port_range = self._rule.source_port_range
        port_range_split = source_port_range.split('-', 1)
        return port_range_split[0]

    @property
    def to_port(self):
        if self._rule.source_port_range == '*':
            return self._rule.source_port_range
        source_port_range = self._rule.source_port_range
        port_range_split = source_port_range.split('-', 1)
        return port_range_split[1]

    @property
    def cidr_ip(self):
        return self._rule.source_address_prefix

    @property
    def group(self):
        return self.parent

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        js['group'] = self.group.id if self.group else ''
        js['parent'] = self.parent.id if self.parent else ''
        return json.dumps(js, sort_keys=True)

    def delete(self):
        security_group = self.parent.name
        self._provider.azure_client. \
            delete_security_group_rule(self.id, security_group)
        for i, o in enumerate(self.parent._security_group.security_rules):
            if o.name == self.name:
                del self.parent._security_group.security_rules[i]
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
        """
        Get this object's name.
        """
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
            get_blob_content(self._container.name, self._key.name)
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
                self._container.name, self.name, data)
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
                self._container.name, self.name, path)
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
        try:
            self._provider.azure_client.delete_blob(
                self._container.name, self.name)
            return True
        except AzureException as azureEx:
            log.exception(azureEx)
            return False

    def generate_url(self, expires_in=0):
        """
        Generate a URL to this object.
        """
        return self._provider.azure_client.get_blob_url(
            self._container.name, self.name)


class AzureBucket(BaseBucket):
    def __init__(self, provider, bucket):
        super(AzureBucket, self).__init__(provider)
        self._bucket = bucket

    @property
    def id(self):
        return self._bucket.name

    @property
    def name(self):
        """
        Get this bucket's name.
        """
        return self._bucket.name

    def get(self, key):
        """
        Retrieve a given object from this bucket.
        """
        try:
            obj = self._provider.azure_client.get_blob(self.name, key)
            return AzureBucketObject(self._provider, self, obj)
        except AzureException as azureEx:
            log.exception(azureEx)
            return None

    def list(self, limit=None, marker=None, prefix=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        objects = [AzureBucketObject(self._provider, self, obj)
                   for obj in
                   self._provider.azure_client.list_blobs(
                       self.name, prefix=prefix)]
        return ClientPagedResultList(self._provider, objects,
                                     limit=limit, marker=marker)

    def delete(self, delete_contents=True):
        """
        Delete this bucket.
        """
        try:
            self._provider.azure_client.delete_container(self.name)
            return True
        except AzureException as azureEx:
            log.exception(azureEx)
            return False

    def create_object(self, name):
        self._provider.azure_client.create_blob_from_text(
            self.name, name, '')
        return self.get(name)

    def exists(self, name):
        """
        Determine if an object with given name exists in this bucket.
        """
        return True if self.get(name) else False


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
        elif self._volume.owner_id:
            self._state = 'Attached'
        else:
            self._state = 'Unattached'

    @property
    def id(self):
        return self._volume.name

    @property
    def resource_id(self):
        return self._volume.id

    @property
    def tags(self):
        return self._volume.tags

    @property
    def name(self):
        """
        Get the volume name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._volume.tags.get('Name', self._volume.name)

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the volume name.
        """
        # self._volume.name = value
        self._volume.tags.update(Name=value)
        self._provider.azure_client. \
            update_disk_tags(self.id,
                             self._volume.tags)

    @property
    def description(self):
        return self._volume.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._volume.tags.update(Description=value)
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
        if self._volume.creation_data.source_uri:
            url_params = azure_helpers.\
                parse_url(SNAPSHOT_RESOURCE_ID,
                          self._volume.creation_data.source_uri)
            return self._provider.block_store.snapshots. \
                get(url_params.get(SNAPSHOT_NAME))
        return None

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
        if self._volume.owner_id:
            url_params = azure_helpers.parse_url(INSTANCE_RESOURCE_ID,
                                                 self._volume.owner_id)
            return BaseAttachmentInfo(self,
                                      url_params.get(VM_NAME),
                                      None)
        else:
            return None

    def attach(self, instance, device=None):
        """
        Attach this volume to an instance.
        """
        try:
            instance_id = instance.id if isinstance(
                instance,
                Instance) else instance
            vm = self._provider.azure_client.get_vm(instance_id)

            vm.storage_profile.data_disks.append({
                'lun': len(vm.storage_profile.data_disks),
                'name': self.id,
                'create_option': 'attach',
                'managed_disk': {
                    'id': self.resource_id
                }
            })
            self._provider.azure_client \
                .create_vm(instance_id, vm)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        virtual_machine = None
        for index, vm in enumerate(
                self._provider.azure_client.list_vm()):
            for item in vm.storage_profile.data_disks:
                if item.managed_disk and \
                                item.managed_disk.id == self.resource_id:
                    vm.storage_profile.data_disks.remove(item)
                    virtual_machine = vm
                    break
            if virtual_machine:
                break

        if virtual_machine:
            self._provider.azure_client.create_vm(
                virtual_machine.name,
                virtual_machine
            )
            return True
        return False

    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.
        """
        return self._provider.block_store.snapshots.create(name, self)

    def delete(self):
        """
        Delete this volume.
        """
        try:
            self._provider.azure_client. \
                delete_disk(self.id)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

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
        except (CloudError, ValueError) as cloudError:
            log.exception(cloudError.message)
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
        return self._snapshot.name

    @property
    def resource_id(self):
        return self._snapshot.id

    @property
    def name(self):
        """
        Get the snapshot name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._snapshot.tags.get('Name', self._snapshot.name)

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the snapshot name.
        """
        # self._snapshot.name = value
        self._snapshot.tags.update(Name=value)
        self._provider.azure_client. \
            update_snapshot_tags(self.id,
                                 self._snapshot.tags)

    @property
    def description(self):
        return self._snapshot.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._snapshot.tags.update(Description=value)
        self._provider.azure_client. \
            update_snapshot_tags(self.id,
                                 self._snapshot.tags)

    @property
    def size(self):
        return self._snapshot.disk_size_gb

    @property
    def volume_id(self):
        url_params = azure_helpers.\
            parse_url(VOLUME_RESOURCE_ID,
                      self._snapshot.creation_data.source_uri)
        return url_params.get(VOLUME_NAME)

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
        except (CloudError, ValueError) as cloudError:
            log.exception(cloudError.message)
            # The snapshot no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'

    def delete(self):
        """
        Delete this snapshot.
        """
        try:
            self._provider.azure_client.delete_snapshot(self.id)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

    def create_volume(self, placement=None,
                      size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.
        """
        return self._provider.block_store.volumes. \
            create(self.id, self.size,
                   zone=placement, snapshot=self)


class AzureMachineImage(BaseMachineImage):
    IMAGE_STATE_MAP = {
        'InProgress': MachineImageState.PENDING,
        'Succeeded': MachineImageState.AVAILABLE,
        'Failed': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
        super(AzureMachineImage, self).__init__(provider)
        self._image = image
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
        return self._image.name

    @property
    def resource_id(self):
        return self._image.id

    @property
    def name(self):
        """
        Get the image name.

        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._image.tags.get('Name', self._image.name)

    @name.setter
    def name(self, value):
        """
        Set the image name.
        """
        self._image.tags.update(Name=value)
        self._provider.azure_client. \
            update_image_tags(self.id, self._image.tags)

    @property
    def description(self):
        """
        Get the image description.

        :rtype: ``str``
        :return: Description for this image as returned by the cloud middleware
        """
        return self._image.tags.get('Description', None)

    @description.setter
    def description(self, value):
        """
        Set the image name.
        """
        self._image.tags.update(Description=value)
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
        return self._image.storage_profile.os_disk.disk_size_gb

    def delete(self):
        """
        Delete this image
        """
        self._provider.azure_client.delete_image(self.id)

    @property
    def state(self):
        return AzureMachineImage.IMAGE_STATE_MAP.get(
            self._state, MachineImageState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._image = self._provider.azure_client\
                .get_image(self.id)
            self._state = self._image.provisioning_state
        except CloudError as cloudError:
            log.exception(cloudError.message)
            # image no longer exists
            self._state = "unknown"


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

    @property
    def id(self):
        return self._network.name

    @property
    def resource_id(self):
        return self._network.id

    @property
    def name(self):
        """
        Get the network name.

        .. note:: the network must have a (case sensitive) tag ``Name``
        """
        return self._network.tags.get('Name', self._network.name)

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the network name.
        """
        self._network.tags.update(Name=value)
        self._provider.azure_client.\
            update_network_tags(self.id, self._network.tags)

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
        except (CloudError, ValueError) as cloudError:
            log.exception(cloudError.message)
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
        try:
            self._provider.azure_client.\
                delete_network(self.id)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

    def subnets(self):
        """
        List all the subnets in this network
        :return:
        """
        return self._provider.network.subnets.list(network=self.id)

    def create_subnet(self, cidr_block, name=None, zone=None):
        """
        Create the subnet with cidr_block
        :param cidr_block:
        :param name:
        :param zone:
        :return:
        """
        return self._provider.network.subnets.\
            create(network=self.id, cidr_block=cidr_block, name=name)


class AzureFloatingIP(BaseFloatingIP):

    def __init__(self, provider, floating_ip):
        super(AzureFloatingIP, self).__init__(provider)
        self._ip = floating_ip

    @property
    def id(self):
        return self._ip.name

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

    def in_use(self):
        return True if self._ip.ip_configuration else False

    def delete(self):
        """
        Delete an existing floating ip.
        """
        try:
            self._provider.azure_client.delete_floating_ip(self.id)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False


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

    def __init__(self, provider, subnet):
        super(AzureSubnet, self).__init__(provider)
        self._subnet = subnet
        self._url_params = azure_helpers\
            .parse_url(SUBNET_RESOURCE_ID, subnet.id)
        self._network = self._provider.azure_client.\
            get_network(self._url_params.get(NETWORK_NAME))

    @property
    def id(self):
        return self._subnet.name

    @property
    def resource_id(self):
        return self._subnet.id

    @property
    def name(self):
        """
        Get the subnet name.

        .. note:: the subnet must have a (case sensitive) tag ``Name``
        """
        return self._subnet.name

    @property
    def zone(self):
        region = self._provider.\
            compute.regions.get(self._network.location)
        return region.zones[0]

    @property
    def cidr_block(self):
        return self._subnet.address_prefix

    @property
    def network_id(self):
        return self._url_params.get(NETWORK_NAME)

    def delete(self):
        """
        Delete the subnet
        :return:
        """
        try:
            self._provider.azure_client.\
                delete_subnet(self.network_id,
                              self.id)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False


class AzureInstance(BaseInstance):

    INSTANCE_STATE_MAP = {
        'InProgress': InstanceState.PENDING,
        'Creating': InstanceState.PENDING,
        'VM running': InstanceState.RUNNING,
        'Updating': InstanceState.CONFIGURING,
        'Deleted': InstanceState.TERMINATED,
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
        self._get_network_attributes()
        if not self._vm.tags:
            self._vm.tags = {}

    def _get_network_attributes(self):
        """
        This method used identify the public , private ip addresses
        and security groups associated with network interfaces.
        :return:
        """
        self._private_ips = []
        self._public_ips = []
        self._security_group_ids = []
        self._public_ip_ids = []
        self._nic_ids = []
        for nic in self._vm.network_profile.network_interfaces:
            nic_params = azure_helpers.\
                parse_url(NETWORK_INTERFACE_RESOURCE_ID, nic.id)
            nic_name = nic_params.get(NETWORK_INTERFACE_NAME)
            self._nic_ids.append(nic_name)
            nic = self._provider.azure_client.get_nic(nic_name)
            if nic.network_security_group:
                sg_params = azure_helpers. \
                    parse_url(SECURITY_GROUP_RESOURCE_ID,
                              nic.network_security_group.id)
                self._security_group_ids.\
                    append(sg_params.get(SECURITY_GROUP_NAME))
            if nic.ip_configurations:
                for ip_config in nic.ip_configurations:
                    self._private_ips.append(ip_config.private_ip_address)
                    if ip_config.public_ip_address:
                        url_params = azure_helpers.\
                            parse_url(PUBLIC_IP_RESOURCE_ID,
                                      ip_config.public_ip_address.id)
                        public_ip_name = url_params.get(PUBLIC_IP_NAME)
                        public_ip = self._provider.azure_client.\
                            get_public_ip(public_ip_name)
                        self._public_ip_ids.append(public_ip_name)
                        self._public_ips.append(public_ip.ip_address)

    @property
    def id(self):
        """
        Get the instance identifier.
        """
        return self._vm.name

    @property
    def resource_id(self):
        return self._vm.id

    @property
    def name(self):
        """
        Get the instance name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._vm.tags.get('Name', self._vm.name)

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the instance name.
        """
        self._vm.tags.update(Name=value)
        self._provider.azure_client.\
            update_vm_tags(self.id, self._vm.tags)

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        return self._public_ips

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return self._private_ips

    @property
    def instance_type_id(self):
        """
        Get the instance type name.
        """
        return self._vm.hardware_profile.vm_size

    @property
    def instance_type(self):
        """
        Get the instance type.
        """
        return self._provider.compute.instance_types.find(
            name=self.instance_type_id)[0]

    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).
        """
        self._provider.azure_client.restart_vm(self.id)

    def terminate(self):
        """
        Permanently terminate this instance.
        After deleting the VM. we are deleting the network interface
        associated to the instance, public ip addresses associated to
        the instance and also removing OS disk and data disks where
        tag with name 'delete_on_terminate' has value True.
        """
        self._provider.azure_client.deallocate_vm(self.id)
        self._provider.azure_client.delete_vm(self.id)
        for nic_id in self._nic_ids:
            self._provider.azure_client.delete_nic(nic_id)
        for public_ip_id in self._public_ip_ids:
            self._provider.azure_client.delete_public_ip(public_ip_id)
        for data_disk in self._vm.storage_profile.data_disks:
            if data_disk.managed_disk:
                disk_params = azure_helpers.\
                    parse_url(VOLUME_RESOURCE_ID,
                              data_disk.managed_disk.id)
                disk = self._provider.azure_client.\
                    get_disk(disk_params.get(VOLUME_NAME))
                if disk and disk.tags \
                        and disk.tags.get('delete_on_terminate',
                                          'False') == 'True':
                    self._provider.azure_client.\
                        delete_disk(disk_params.get(VOLUME_NAME))
        if self._vm.storage_profile.os_disk.managed_disk:
            disk_params = azure_helpers. \
                parse_url(VOLUME_RESOURCE_ID,
                          self._vm.storage_profile.os_disk.managed_disk.id)
            self._provider.azure_client. \
                delete_disk(disk_params.get(VOLUME_NAME))

    @property
    def image_id(self):
        """
        Get the image ID for this insance.
        """
        image_ref_id = self._vm.storage_profile.image_reference.id
        if image_ref_id:
            url_params = azure_helpers.parse_url(IMAGE_RESOURCE_ID,
                                                 image_ref_id)
            return url_params.get(IMAGE_NAME)
        else:
            return None

    @property
    def zone_id(self):
        """
        Get the placement zone id where this instance is running.
        """
        return self._vm.location

    @property
    def security_groups(self):
        """
        Get the security groups associated with this instance.
        """
        return [self._provider.security.security_groups.get(group_id)
                for group_id in self._security_group_ids]

    @property
    def security_group_ids(self):
        """
        Get the security groups IDs associated with this instance.
        """
        return self._security_group_ids

    @property
    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return self._vm.tags.get('Key_Pair')

    def create_image(self, name, private_key_path=None):
        """
        Create a new image based on this instance.
        Documentation for create image available at
        https://docs.microsoft.com/en-us/azure/virtual-machines/linux/capture-image  # noqa
        In azure, need to deprovision the VM before capturing.
        To deprovision, login to VM and execute waagent deprovision command.
        To do this programmatically, using pysftp to ssh into the VM
        and executing deprovision command.
        To SSH into the VM programmatically, need pass private key file path,
        so we have modified the Cloud Bridge interface to pass
        the private key file path
        """

        if not self._state == 'VM generalized':
            if not self._state == 'VM running':
                self._provider.azure_client.start_vm(self.id)
                time.sleep(10)  # Some time is required
                self._get_network_attributes()

            # if private_key_path:
            self._deprovision(private_key_path)
            self._provider.azure_client.deallocate_vm(self.id)
            self._provider.azure_client.generalize_vm(self.id)

        create_params = {
            'location': self._provider.region_name,
            'source_virtual_machine': {
                'id': self.resource_id
            },
            'tags': {'Name': name}
        }
        self._provider.azure_client.\
            create_image(name, create_params)
        image = self._provider.azure_client.\
            get_image(name)

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

    def add_floating_ip(self, ip_address):
        """
        Attaches public ip to the instance
        :param ip_address:
        :return:
        """
        try:
            ip_addresses = [ip for ip in
                            self._provider.azure_client.list_floating_ips()
                            if ip.ip_address and ip.ip_address == ip_address]
            if len(ip_addresses) > 0:
                """
                Add an elastic IP address to this instance.
                """
                nic = self._provider.azure_client.get_nic(self._nic_ids[0])

                nic.ip_configurations[0].public_ip_address = {
                    'id': ip_addresses[0].id
                }
                self._provider.azure_client.create_nic(self._nic_ids[0], nic)
                return True
            return False
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

    def remove_floating_ip(self, ip_address=None):
        """
        Remove a public IP address from this instance.
        """
        try:
            nic = self._provider.azure_client.get_nic(self._nic_ids[0])
            nic.ip_configurations[0].public_ip_address = None
            self._provider.azure_client.create_nic(self._nic_ids[0], nic)
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

    def add_security_group(self, sg):
        '''
        :param sg:
        :return: None

        This method adds the security group to VM instance.
        In Azure, security group added to Network interface.
        Azure supports to add only one security group to
        network interface, we are adding the provided security group
        if not associated any security group to NIC
        else replacing the existing security group.
        '''

        nic = self._provider.azure_client.get_nic(self._nic_ids[0])
        if not nic.network_security_group:
            nic.network_security_group = NetworkSecurityGroup()

        sg = (self._provicer.security.security_groups.get(sg)
              if isinstance(sg, str) else sg)
        nic.network_security_group.id = sg.resource_id

        self._provider.azure_client.create_nic(self._nic_ids[0], nic)

    def remove_security_group(self, sg):

        '''
                :param sg:
                :return: None

                This method removes the security group to VM instance.
                In Azure, security group added to Network interface.
                Azure supports to add only one security group to
                network interface, we are removing the provided security group
                if it associated to NIC
                else we are ignoring.
                '''

        nic = self._provider.azure_client.get_nic(self._nic_ids[0])
        sg = (self._provicer.security.security_groups.get(sg)
              if isinstance(sg, str) else sg)
        if nic.network_security_group and \
                nic.network_security_group.id == sg.resource_id:
            nic.network_security_group = None
            self._provider.azure_client.create_nic(self._nic_ids[0], nic)

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
            self._get_network_attributes()
        except (CloudError, ValueError) as cloudError:
            log.exception(cloudError.message)
            # The volume no longer exists and cannot be refreshed.
            # set the state to unknown
            self._state = 'unknown'


class AzureLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider):
        super(AzureLaunchConfig, self).__init__(provider)


class AzureInstanceType(BaseInstanceType):

    def __init__(self, provider, instance_type):
        super(AzureInstanceType, self).__init__(provider)
        self._inst_type = instance_type

    @property
    def id(self):
        return self._inst_type.name

    @property
    def name(self):
        return self._inst_type.name

    @property
    def family(self):
        """
        Python sdk does not return family details.
        So, as of now populating it with 'Unknown'
        """
        return "Unknown"

    @property
    def vcpus(self):
        return self._inst_type.number_of_cores

    @property
    def ram(self):
        return self._inst_type.memory_in_mb

    @property
    def size_root_disk(self):
        return self._inst_type.os_disk_size_in_mb / 1024

    @property
    def size_ephemeral_disks(self):
        return self._inst_type.resource_disk_size_in_mb / 1024

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
                    self._inst_type.max_data_disk_count
               }


class AzureKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(AzureKeyPair, self).__init__(provider, key_pair)
        self._material = None

    @property
    def id(self):
        return self._key_pair.Name

    @property
    def name(self):
        return self._key_pair.Name

    @property
    def key(self):
        return self._key_pair.Key

    @property
    def material(self):
        """
        Unencrypted private key.

        :rtype: str
        :return: Unencrypted private key or ``None`` if not available.

        """
        return self._material

    @material.setter
    def material(self, value):
        self._material = value

    def delete(self):
        try:
            self._provider.azure_client.\
                delete_public_key(self._key_pair)
            return True
        except CloudError:
            return False
