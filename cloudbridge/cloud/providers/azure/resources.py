"""
DataTypes used by this provider
"""
import inspect
import json

from azure.common import AzureException


from cloudbridge.cloud.base.resources import BaseAttachmentInfo, \
    BaseBucket, BaseBucketObject, BaseSecurityGroup, \
    BaseSecurityGroupRule, BaseSnapshot, BaseVolume, \
    ClientPagedResultList
from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.interfaces.resources import Instance, SnapshotState
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
    def description(self):
        return self._security_group.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._security_group.tags.update(Description=value)
        print(self._security_group.tags)
        self._provider.azure_client.\
            update_security_group_tags(self.name, self._security_group.tags)

    @property
    def rules(self):
        security_group_rules = []
        for custom_rule in self._security_group.security_rules:
            sg_custom_rule = AzureSecurityGroupRule(self._provider,
                                                    custom_rule, self)
            security_group_rules.append(sg_custom_rule)
        return security_group_rules

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
            security_group = self._security_group.name
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
                create_security_group_rule(security_group,
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
        'Failed': VolumeState.ERROR
    }

    def __init__(self, provider, volume):
        super(AzureVolume, self).__init__(provider)
        self._volume = volume
        self._url_params = azure_helpers.\
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
    def name(self):
        """
        Get the volume name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._volume.name

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the volume name.
        """
        # self._volume.name = value
        pass

    @property
    def description(self):
        return self._volume.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._volume.tags.update(Description=value)
        self._provider.azure_client.\
            update_disk_tags(self._url_params.get(VOLUME_NAME),
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
            self._provider.azure_client.attach_disk(params.get(VM_NAME),
                                                    self.name, self.id)
            return True
        except CloudError:
            return False

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        try:
            self._provider.azure_client.detach_disk(self.id)
            return True
        except CloudError:
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
            self._provider.azure_client.\
                delete_disk(self._url_params.get(VOLUME_NAME))
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
            print('Volume status ' + self._status)
            self._volume = self._provider.azure_client.\
                get_disk(self._url_params.get(VOLUME_NAME))
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
        'Updating': SnapshotState.CONFIGURING,
        'Deleting': SnapshotState.CONFIGURING,
        'Deleted': SnapshotState.UNKNOWN
    }

    def __init__(self, provider, snapshot):
        super(AzureSnapshot, self).__init__(provider)
        self._snapshot = snapshot
        self._description = None
        self._url_params = azure_helpers.\
            parse_url(SNAPSHOT_RESOURCE_ID, snapshot.id)
        self._status = self._snapshot.provisioning_state
        if not self._snapshot.tags:
            self._snapshot.tags = {}

    @property
    def id(self):
        return self._snapshot.id

    @property
    def name(self):
        """
        Get the snapshot name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._snapshot.name

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the snapshot name.
        """
        # self._snapshot.name = value
        pass

    @property
    def description(self):
        return self._snapshot.tags.get('Description', None)

    @description.setter
    def description(self, value):
        self._snapshot.tags.update(Description=value)
        self._provider.azure_client.\
            update_snapshot_tags(self.name, self._snapshot.tags)

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
            self._snapshot = self._provider.azure_client.\
                get_snapshot(self.name)
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
            self._provider.azure_client.delete_snapshot(self.name)
            return True
        except CloudError:
            return False

    def create_volume(self, placement=None,
                      size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.
        """
        self._provider.azure_client.\
            create_snapshot_disk(self.name + '_disk',
                                 self.id, region=placement)
        azure_vol = self._provider.azure_client.get_disk(self.name + '_disk')
        cb_vol = AzureVolume(self._provider, azure_vol)
        return cb_vol
