"""
DataTypes used by this provider
"""
import inspect
import json

from azure.common import AzureException

from cloudbridge.cloud.base.resources import BaseAttachmentInfo, \
    BaseBucket, BaseBucketObject, BaseInstanceType, \
    BaseMachineImage, BaseNetwork, \
    BasePlacementZone, BaseRegion, \
    BaseSecurityGroup, BaseSecurityGroupRule, BaseSnapshot, BaseSubnet, \
    BaseVolume, ClientPagedResultList
from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.interfaces.resources import Instance, \
    MachineImageState, NetworkState, SnapshotState
from cloudbridge.cloud.providers.azure import helpers as azure_helpers

from msrestazure.azure_exceptions import CloudError

NETWORK_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                      '{resourceGroupName}/providers/Microsoft.Network/' \
                      'virtualNetworks/{virtualNetworkName}'
IMAGE_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                    '{resourceGroupName}/providers/Microsoft.Compute/' \
                    'images/{imageName}'
INSTANCE_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                       '{resourceGroupName}/providers/Microsoft.Compute/' \
                       'virtualMachines/{vmName}'
VOLUME_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                     '{resourceGroupName}/providers/Microsoft.Compute/' \
                     'disks/{diskName}'
SNAPSHOT_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                       '{resourceGroupName}/providers/Microsoft.Compute/' \
                       'snapshots/{snapshotName}'
NETWORK_SECURITY_GROUP_RESOURCE_ID = '/subscriptions/{subscriptionId}/' \
                                     'resourceGroups/{resourceGroupName}/' \
                                     'providers/Microsoft.Network/' \
                                     'networkSecurityGroups/' \
                                     '{networkSecurityGroupName}'
NETWORK_SECURITY_RULE_RESOURCE_ID = '/subscriptions/{subscriptionId}/' \
                                    'resourceGroups/{resourceGroupName}/' \
                                    'providers/Microsoft.Network/' \
                                    'networkSecurityGroups/' \
                                    '{networkSecurityGroupName}' \
                                    '/securityRules/{securityRuleName}'
SUBNET_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                     '{resourceGroupName}/providers/Microsoft.Network' \
                     '/virtualNetworks/{virtualNetworkName}/subnets' \
                     '/{subnetName}'
PUBLIC_IP_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups' \
                        '/{resourceGroupName}/providers/Microsoft.Network' \
                        '/publicIPAddresses/{publicIpAddressName}'
ROUTE_TABLE_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups' \
                          '/{resourceGroupName}/providers/Microsoft.Network' \
                          '/routeTables/{routeTableName}'
ROUTE_RESOURCE_ID = '/subscriptions/{subscriptionId}/resourceGroups/' \
                    '{resourceGroupName}/providers/Microsoft.Network' \
                    '/routeTables/{routeTableName}/routes/{routeName}'
NETWORK_INTERFACE_RESOURCE_ID = '/subscriptions/{subscriptionId}/' \
                                'resourceGroups/{resourceGroupName}' \
                                '/providers/Microsoft.Network/' \
                                'networkInterfaces/{networkInterfaceName}'

RESOURCE_GROUP_NAME = 'resourceGroupName'
SUBSCRIPTION_ID = 'subscriptionId'
NETWORK_NAME = 'virtualNetworkName'
IMAGE_NAME = 'imageName'
VM_NAME = 'vmName'
VOLUME_NAME = 'diskName'
SNAPSHOT_NAME = 'snapshotName'
SECURITY_GROUP_NAME = 'networkSecurityGroupName'
SECURITY_GROUP_RULE_NAME = 'securityRuleName'
SUBNET_NAME = 'subnetName'
PUBLIC_IP_NAME = 'publicIpAddressName'
ROUTE_TABLE_NAME = 'routeTableName'
ROUTE_NAME = 'routeName'
NETWORK_INTERFACE_NAME = 'networkInterfaceName'


class AzureSecurityGroup(BaseSecurityGroup):
    def __init__(self, provider, security_group):
        super(AzureSecurityGroup, self).__init__(provider, security_group)
        self._security_group = security_group
        if not self._security_group.tags:
            self._security_group.tags = {}

    @property
    def network_id(self):
        return self._security_group.resource_guid

    @property
    def resource_name(self):
        return self._security_group.name

    @property
    def name(self):
        return self._security_group.tags.get('Name', self._security_group.name)

    @name.setter
    def name(self, value):
        self._security_group.tags.update(Name=value)
        self._provider.azure_client. \
            update_security_group_tags(self.resource_name,
                                       self._security_group.tags)

    @property
    def description(self):
        return self._security_group.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._security_group.tags.update(Description=value)
        self._provider.azure_client.\
            update_security_group_tags(self.resource_name,
                                       self._security_group.tags)

    @property
    def rules(self):
        security_group_rules = []
        for custom_rule in self._security_group.security_rules:
            sg_custom_rule = AzureSecurityGroupRule(self._provider,
                                                    custom_rule, self)
            security_group_rules.append(sg_custom_rule)
        return security_group_rules

    def delete(self):
        try:
            self._provider.azure_client.\
                delete_security_group(self.resource_name)
            return True
        except CloudError:
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

        if not cidr_ip:
            cidr_ip = '0.0.0.0/0'

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
                create_security_group_rule(self.resource_name,
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
    def name(self):
        return self._rule.name

    @property
    def id(self):
        return self._rule.id

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
            delete_security_group_rule(self.name, security_group)
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
        except AzureException:
            return False

    def upload_from_file(self, path):
        """
        Store the contents of the file pointed by the "path" variable.
        """
        try:
            self._provider.azure_client.create_blob_from_file(
                self._container.name, self.name, path)
            return True
        except AzureException:
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
        except AzureException:
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
        except AzureException:
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
        except AzureException:
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
        self._url_params = azure_helpers. \
            parse_url(VOLUME_RESOURCE_ID, volume.id)
        self._description = None
        self._status = 'unknown'
        self.update_status()
        if not self._volume.tags:
            self._volume.tags = {}

    def update_status(self):
        if not self._volume.provisioning_state == 'Succeeded':
            self._status = self._volume.provisioning_state
        elif self._volume.owner_id:
            self._status = 'Attached'
        else:
            self._status = 'Unattached'

    @property
    def id(self):
        return self._volume.id

    @property
    def resource_name(self):
        return self._volume.name

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
            update_disk_tags(self.resource_name,
                             self._volume.tags)

    @property
    def description(self):
        return self._volume.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._volume.tags.update(Description=value)
        self._provider.azure_client. \
            update_disk_tags(self.resource_name,
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
            return self._provider.block_store.snapshots. \
                get(self._volume.creation_data.source_uri)
        return None

    @property
    def attachments(self):
        if self._volume.owner_id:
            return BaseAttachmentInfo(self,
                                      self._volume.owner_id,
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
            params = azure_helpers.parse_url(INSTANCE_RESOURCE_ID,
                                             instance_id)

            vm = self._provider.azure_client.get_vm(params.get(VM_NAME))

            vm.storage_profile.data_disks.append({
                'lun': len(vm.storage_profile.data_disks),
                'name': self.resource_name,
                'create_option': 'attach',
                'managed_disk': {
                    'id': self.id
                }
            })
            self._provider.azure_client \
                .create_or_update_vm(params.get(VM_NAME), vm)
            return True
        except CloudError:
            return False

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        virtual_machine = None
        for index, vm in enumerate(
                self._provider.azure_client.list_vm()):
            for item in vm.storage_profile.data_disks:
                if item.managed_disk and item.managed_disk.id == self.id:
                    vm.storage_profile.data_disks.remove(item)
                    virtual_machine = vm
                    break
            if virtual_machine:
                break

        if virtual_machine:
            self._provider.azure_client.create_or_update_vm(
                virtual_machine.name,
                virtual_machine
            )
            return True
        return False

    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.
        """
        return self._provider.block_store.snapshots.create(name, self.id)

    def delete(self):
        """
        Delete this volume.
        """
        try:
            self._provider.azure_client. \
                delete_disk(self.resource_name)
            return True
        except CloudError:
            return False

    @property
    def state(self):
        return AzureVolume.VOLUME_STATE_MAP.get(
            self._status, VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._volume = self._provider.azure_client. \
                get_disk(self.resource_name)
            self.update_status()
        except (CloudError, ValueError):
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._status = 'unknown'


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
        self._url_params = azure_helpers. \
            parse_url(SNAPSHOT_RESOURCE_ID, snapshot.id)
        self._status = self._snapshot.provisioning_state
        if not self._snapshot.tags:
            self._snapshot.tags = {}

    @property
    def id(self):
        return self._snapshot.id

    @property
    def resource_name(self):
        return self._snapshot.name

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
            update_snapshot_tags(self.resource_name,
                                 self._snapshot.tags)

    @property
    def description(self):
        return self._snapshot.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._snapshot.tags.update(Description=value)
        self._provider.azure_client. \
            update_snapshot_tags(self.resource_name,
                                 self._snapshot.tags)

    @property
    def size(self):
        return self._snapshot.disk_size_gb

    @property
    def volume_id(self):
        return self._snapshot.creation_data.source_uri

    @property
    def create_time(self):
        return self._snapshot.time_created.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @property
    def state(self):
        return AzureSnapshot.SNAPSHOT_STATE_MAP.get(
            self._status, SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._snapshot = self._provider.azure_client. \
                get_snapshot(self.resource_name)
            self._status = self._snapshot.provisioning_state
        except (CloudError, ValueError):
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._status = 'unknown'

    def delete(self):
        """
        Delete this snapshot.
        """
        try:
            self._provider.azure_client.delete_snapshot(self.resource_name)
            return True
        except CloudError:
            return False

    def create_volume(self, placement=None,
                      size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.
        """
        return self._provider.block_store.volumes. \
            create(self.resource_name, self.size,
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
        self._url_params = azure_helpers. \
            parse_url(IMAGE_RESOURCE_ID, image.id)
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
            update_image_tags(self.resource_name, self._image.tags)

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
            update_image_tags(self.resource_name, self._image.tags)

    @property
    def resource_name(self):
        return self._image.name

    @property
    def min_disk(self):
        """
        Returns the minimum size of the disk that's required to
        boot this image (in GB)

        :rtype: ``int``
        :return: The minimum disk size needed by this image
        """
        return self._image.storage_profile.os_disk.disk_size_gb

    def delete(self):
        """
        Delete this image
        """
        self._provider.azure_client.delete_image(self.resource_name)

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
                .get_image(self.resource_name)
            self._state = self._image.provisioning_state
        except CloudError:
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
        return self._network.id

    @property
    def name(self):
        """
        Get the network name.

        .. note:: the network must have a (case sensitive) tag ``Name``
        """
        return self._network.tags.get('Name', self._network.name)

    @property
    def resource_name(self):
        return self._network.name

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the network name.
        """
        self._network.tags.update(Name=value)
        self._provider.azure_client.\
            update_network_tags(self.resource_name, self._network.tags)

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
                get_network(self.resource_name)
            self._state = self._network.provisioning_state
        except (CloudError, ValueError):
            # The network no longer exists and cannot be refreshed.
            # set the status to unknown
            self._state = 'unknown'

    @property
    def cidr_block(self):
        return self._network.address_space.address_prefixes[0]

    def delete(self):
        """
        Delete an existing network.
        """
        try:
            self._provider.azure_client.\
                delete_network(self.resource_name)
            return True
        except CloudError:
            return False

    def subnets(self):
        return self._provider.network.subnets.list(network=self.id)

    def create_subnet(self, cidr_block, name=None, zone=None):
        return self._provider.network.subnets.\
            create(network=self.id, cidr_block=cidr_block, name=name)


class AzureRegion(BaseRegion):
    def __init__(self, provider, azure_region):
        super(AzureRegion, self).__init__(provider)
        self._azure_region = azure_region

    @property
    def id(self):
        return self._azure_region.id

    @property
    def name(self):
        return self._azure_region.name

    @property
    def zones(self):
        """
            Access information about placement zones within this region.
        """
        # As Azure does not have zones feature, mapping the region
        # information in the zones.
        return [AzurePlacementZone(self._provider,
                                   self._azure_region.id,
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
        return self._network.location

    @property
    def cidr_block(self):
        return self._subnet.address_prefix

    @property
    def network_id(self):
        return self._network.id

    def delete(self):
        try:
            self._provider.azure_client.\
                delete_subnet(self._url_params.get(NETWORK_NAME),
                              self._url_params.get(SUBNET_NAME))
            return True
        except CloudError as cloudError:
            return False


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
        return 1

    @property
    def extra_data(self):
        return None
