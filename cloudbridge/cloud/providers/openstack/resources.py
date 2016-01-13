"""
DataTypes used by this provider
"""
import inspect
import json
import shutil

import ipaddress
from swiftclient.exceptions import ClientException

from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseBucketObject
from cloudbridge.cloud.base.resources import BaseInstance
from cloudbridge.cloud.base.resources import BaseInstanceType
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BaseMachineImage
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion
from cloudbridge.cloud.base.resources import BaseSecurityGroup
from cloudbridge.cloud.base.resources import BaseSecurityGroupRule
from cloudbridge.cloud.base.resources import BaseSnapshot
from cloudbridge.cloud.base.resources import BaseSubnet
from cloudbridge.cloud.base.resources import BaseVolume
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import VolumeState
from cloudbridge.cloud.providers.openstack import helpers as oshelpers


class OpenStackMachineImage(BaseMachineImage):

    # ref: http://docs.openstack.org/developer/glance/statuses.html
    IMAGE_STATE_MAP = {
        'QUEUED': MachineImageState.PENDING,
        'SAVING': MachineImageState.PENDING,
        'ACTIVE': MachineImageState.AVAILABLE,
        'KILLED': MachineImageState.ERROR,
        'DELETED': MachineImageState.ERROR,
        'PENDING_DELETE': MachineImageState.ERROR
    }

    def __init__(self, provider, os_image):
        super(OpenStackMachineImage, self).__init__(provider)
        if isinstance(os_image, OpenStackMachineImage):
            # pylint:disable=protected-access
            self._os_image = os_image._os_image
        else:
            self._os_image = os_image

    @property
    def id(self):
        """
        Get the image identifier.
        """
        return self._os_image.id

    @property
    def name(self):
        """
        Get the image name.
        """
        return self._os_image.name

    @property
    def description(self):
        """
        Get the image description.
        """
        return None

    def delete(self):
        """
        Delete this image
        """
        self._os_image.delete()

    @property
    def state(self):
        return OpenStackMachineImage.IMAGE_STATE_MAP.get(
            self._os_image.status, MachineImageState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        image = self._provider.compute.images.get(self.id)
        if image:
            self._os_image = image._os_image  # pylint:disable=protected-access
        else:
            # The image no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_image.status = 'unknown'


class OpenStackPlacementZone(BasePlacementZone):

    def __init__(self, provider, zone, region):
        super(OpenStackPlacementZone, self).__init__(provider)
        if isinstance(zone, OpenStackPlacementZone):
            self._os_zone = zone._os_zone  # pylint:disable=protected-access
            self._os_region = zone._os_region
        else:
            self._os_zone = zone
            self._os_region = region

    @property
    def id(self):
        """
        Get the zone id

        :rtype: ``str``
        :return: ID for this zone as returned by the cloud middleware.
        """
        return self._os_zone

    @property
    def name(self):
        """
        Get the zone name.

        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        # return self._os_zone.zoneName
        return self._os_zone

    @property
    def region(self):
        """
        Get the region that this zone belongs to.

        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        return self._os_region


class OpenStackInstanceType(BaseInstanceType):

    def __init__(self, provider, os_flavor):
        super(OpenStackInstanceType, self).__init__(provider)
        self._os_flavor = os_flavor

    @property
    def id(self):
        return self._os_flavor.id

    @property
    def name(self):
        return self._os_flavor.name

    @property
    def family(self):
        # TODO: This may not be standardised accross openstack
        # but NeCTAR is using it this way
        return self.extra_data.get('flavor_class:name')

    @property
    def vcpus(self):
        return self._os_flavor.vcpus

    @property
    def ram(self):
        return self._os_flavor.ram

    @property
    def size_root_disk(self):
        return self._os_flavor.disk

    @property
    def size_ephemeral_disks(self):
        return 0 if self._os_flavor.ephemeral == 'N/A' else \
            self._os_flavor.ephemeral

    @property
    def num_ephemeral_disks(self):
        return 0 if self._os_flavor.ephemeral == 'N/A' else \
            self._os_flavor.ephemeral

    @property
    def extra_data(self):
        extras = self._os_flavor.get_keys()
        extras['rxtx_factor'] = self._os_flavor.rxtx_factor
        extras['swap'] = self._os_flavor.swap
        extras['is_public'] = self._os_flavor.is_public
        return extras


class OpenStackInstance(BaseInstance):

    # ref: http://docs.openstack.org/developer/nova/v2/2.0_server_concepts.html
    # and http://developer.openstack.org/api-ref-compute-v2.html
    INSTANCE_STATE_MAP = {
        'ACTIVE': InstanceState.RUNNING,
        'BUILD': InstanceState.PENDING,
        'DELETED': InstanceState.TERMINATED,
        'ERROR': InstanceState.ERROR,
        'HARD_REBOOT': InstanceState.REBOOTING,
        'PASSWORD': InstanceState.PENDING,
        'PAUSED': InstanceState.STOPPED,
        'REBOOT': InstanceState.REBOOTING,
        'REBUILD': InstanceState.CONFIGURING,
        'RESCUE': InstanceState.CONFIGURING,
        'RESIZE': InstanceState.CONFIGURING,
        'REVERT_RESIZE': InstanceState.CONFIGURING,
        'SOFT_DELETED': InstanceState.STOPPED,
        'STOPPED': InstanceState.STOPPED,
        'SUSPENDED': InstanceState.STOPPED,
        'SHUTOFF': InstanceState.STOPPED,
        'UNKNOWN': InstanceState.UNKNOWN,
        'VERIFY_RESIZE': InstanceState.CONFIGURING
    }

    def __init__(self, provider, os_instance):
        super(OpenStackInstance, self).__init__(provider)
        self._os_instance = os_instance

    @property
    def id(self):
        """
        Get the instance identifier.
        """
        return self._os_instance.id

    @property
    def name(self):
        """
        Get the instance name.
        """
        return self._os_instance.name

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the instance name.
        """
        self._os_instance.name = value
        self._os_instance.update()

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        # Openstack doesn't provide an easy way to figure our whether an ip is
        # public or private, since the returned ips are grouped by an arbitrary
        # network label. Therefore, it's necessary to parse the address and
        # determine whether it's public or private
        return [address
                for _, addresses in self._os_instance.networks.items()
                for address in addresses
                if not ipaddress.ip_address(address).is_private]

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return [address
                for _, addresses in self._os_instance.networks.items()
                for address in addresses
                if ipaddress.ip_address(address).is_private]

    @property
    def instance_type(self):
        """
        Get the instance type.
        """
        return OpenStackInstanceType(self._provider, self._os_instance.flavor)

    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).
        """
        self._os_instance.reboot()

    def terminate(self):
        """
        Permanently terminate this instance.
        """
        self._os_instance.delete()

    @property
    def image_id(self):
        """
        Get the image ID for this instance.
        """
        return self._os_instance.image.get("id")

    @property
    def placement_zone(self):
        """
        Get the placement zone where this instance is running.
        """
        return OpenStackPlacementZone(
            self._provider,
            getattr(self._os_instance, 'OS-EXT-AZ:availability_zone', None),
            self._provider.region_name)

    @property
    def security_groups(self):
        """
        Get the security groups associated with this instance.
        """
        return [self._provider.security.security_groups.find(group['name'])[0]
                for group in self._os_instance.security_groups]

    @property
    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return self._os_instance.key_name

    def create_image(self, name):
        """
        Create a new image based on this instance.
        """
        image_id = self._os_instance.create_image(name)
        return OpenStackMachineImage(
            self._provider, self._provider.compute.images.get(image_id))

    def add_floating_ip(self, ip_address):
        """
        Add a floating IP address to this instance.
        """
        self._os_instance.add_floating_ip(ip_address)

    def remove_floating_ip(self, ip_address):
        """
        Remove a floating IP address from this instance.
        """
        self._os_instance.remove_floating_ip(ip_address)

    @property
    def state(self):
        return OpenStackInstance.INSTANCE_STATE_MAP.get(
            self._os_instance.status, InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        instance = self._provider.compute.instances.get(
            self.id)
        if instance:
            # pylint:disable=protected-access
            self._os_instance = instance._os_instance
        else:
            # The instance no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_instance.status = 'unknown'


class OpenStackRegion(BaseRegion):

    def __init__(self, provider, os_region):
        super(OpenStackRegion, self).__init__(provider)
        self._os_region = os_region

    @property
    def id(self):
        return self._os_region

    @property
    def name(self):
        return self._os_region

    @property
    def zones(self):
        # detailed must be set to ``False`` because the (default) ``True``
        # value requires Admin privileges
        if self.name == self._provider.region_name:  # optimisation
            zones = self._provider.nova.availability_zones.list(detailed=False)
        else:
            region_nova = self._provider._connect_nova_region(self.name)
            zones = region_nova.availability_zones.list(detailed=False)

        return [OpenStackPlacementZone(self._provider, z.zoneName,
                                       self._provider.region_name)
                for z in zones]


class OpenStackVolume(BaseVolume):

    # Ref: http://developer.openstack.org/api-ref-blockstorage-v2.html
    VOLUME_STATE_MAP = {
        'creating': VolumeState.CREATING,
        'available': VolumeState.AVAILABLE,
        'attaching': VolumeState.CONFIGURING,
        'in-use': VolumeState.IN_USE,
        'deleting': VolumeState.CONFIGURING,
        'error': VolumeState.ERROR,
        'error_deleting': VolumeState.ERROR,
        'backing-up': VolumeState.CONFIGURING,
        'restoring-backup': VolumeState.CONFIGURING,
        'error_restoring': VolumeState.ERROR,
        'error_extending': VolumeState.ERROR
    }

    def __init__(self, provider, volume):
        super(OpenStackVolume, self).__init__(provider)
        self._volume = volume

    @property
    def id(self):
        return self._volume.id

    @property
    def name(self):
        """
        Get the volume name.
        """
        return self._volume.name

    @name.setter
    def name(self, value):  # pylint:disable=arguments-differ
        """
        Set the volume name.
        """
        self._volume.name = value
        self._volume.update()

    def attach(self, instance, device):
        """
        Attach this volume to an instance.
        """
        instance_id = instance.id if isinstance(
            instance,
            OpenStackInstance) else instance
        self._volume.attach(instance_id, device)

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        self._volume.detach()

    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.
        """
        return self._provider.block_store.snapshots.create(
            name, self, description=description)

    def delete(self):
        """
        Delete this volume.
        """
        self._volume.delete()

    @property
    def state(self):
        return OpenStackVolume.VOLUME_STATE_MAP.get(
            self._volume.status, VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        vol = self._provider.block_store.volumes.get(
            self.id)
        if vol:
            self._volume = vol._volume  # pylint:disable=protected-access
        else:
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._volume.status = 'unknown'


class OpenStackSnapshot(BaseSnapshot):

    # Ref: http://developer.openstack.org/api-ref-blockstorage-v2.html
    SNAPSHOT_STATE_MAP = {
        'creating': SnapshotState.PENDING,
        'available': SnapshotState.AVAILABLE,
        'deleting': SnapshotState.CONFIGURING,
        'error': SnapshotState.ERROR,
        'error_deleting': SnapshotState.ERROR
    }

    def __init__(self, provider, snapshot):
        super(OpenStackSnapshot, self).__init__(provider)
        self._snapshot = snapshot

    @property
    def id(self):
        return self._snapshot.id

    @property
    def name(self):
        """
        Get the snapshot name.
        """
        return self._snapshot.name

    @name.setter
    def name(self, value):  # pylint:disable=arguments-differ
        """
        Set the snapshot name.
        """
        self._snapshot.add_tag('Name', value)
        self._snapshot.update()

    @property
    def state(self):
        return OpenStackSnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.status, SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        snap = self._provider.block_store.snapshots.get(
            self.id)
        if snap:
            self._snapshot = snap._snapshot  # pylint:disable=protected-access
        else:
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._snapshot.status = 'unknown'

    def delete(self):
        """
        Delete this snapshot.
        """
        self._snapshot.delete()

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.
        """
        vol_name = "Created from {0} ({1})".format(self.id, self.name)
        size = size if size else self._snapshot.size
        os_vol = self._provider.cinder.volumes.create(
            size, name=vol_name, availability_zone=placement,
            snapshot_id=self._snapshot.id)
        cb_vol = OpenStackVolume(self._provider, os_vol)
        cb_vol.name = vol_name
        return cb_vol


class OpenStackNetwork(BaseNetwork):

    # Ref: https://github.com/openstack/neutron/blob/master/neutron/plugins/
    #      common/constants.py
    _NETWORK_STATE_MAP = {
        'PENDING_CREATE': NetworkState.PENDING,
        'PENDING_UPDATE': NetworkState.PENDING,
        'PENDING_DELETE': NetworkState.PENDING,
        'CREATED': NetworkState.PENDING,
        'INACTIVE': NetworkState.PENDING,
        'DOWN': NetworkState.DOWN,
        'ERROR': NetworkState.ERROR,
        'ACTIVE': NetworkState.AVAILABLE
    }

    def __init__(self, provider, network):
        super(OpenStackNetwork, self).__init__(provider)
        self._network = network

    @property
    def id(self):
        return self._network.get('id', None)

    @property
    def name(self):
        return self._network.get('name', None)

    @property
    def state(self):
        return OpenStackNetwork._NETWORK_STATE_MAP.get(
            self._network.get('status', None),
            NetworkState.UNKNOWN)

    @property
    def cidr_block(self):
        # OpenStack does not define a CIDR block for networks
        return ''

    def delete(self):
        if self.id in str(self._provider.neutron.list_networks()):
            self._provider.neutron.delete_network(self.id)
        # Adhear to the interface docs
        if self.id not in str(self._provider.neutron.list_networks()):
            return True

    def subnets(self):
        subnets = (self._provider.neutron.list_subnets(network_id=self.id)
                   .get('subnets', []))
        return [OpenStackSubnet(self._provider, subnet) for subnet in subnets]

    def create_subnet(self, cidr_block, name=''):
        subnet_info = {'name': name, 'network_id': self.id,
                       'cidr': cidr_block, 'ip_version': 4}
        subnet = (self._provider.neutron.create_subnet({'subnet': subnet_info})
                  .get('subnet'))
        return OpenStackSubnet(self._provider, subnet)

    def refresh(self):
        """
        Refreshes the state of this network by re-querying the cloud provider
        for its latest state.
        """
        return self.state


class OpenStackSubnet(BaseSubnet):

    def __init__(self, provider, subnet):
        super(OpenStackSubnet, self).__init__(provider)
        self._subnet = subnet

    @property
    def id(self):
        return self._subnet.get('id', None)

    @property
    def name(self):
        return self._subnet.get('name', None)

    @property
    def cidr_block(self):
        return self._subnet.get('cidr', None)

    @property
    def network_id(self):
        return self._subnet.get('network_id', None)

    def delete(self):
        if self.id in str(self._provider.neutron.list_subnets()):
            self._provider.neutron.delete_subnet(self.id)
        # Adhear to the interface docs
        if self.id not in str(self._provider.neutron.list_subnets()):
            return True


class OpenStackKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(OpenStackKeyPair, self).__init__(provider, key_pair)

    @property
    def material(self):
        """
        Unencrypted private key.

        :rtype: str
        :return: Unencrypted private key or ``None`` if not available.

        """
        return getattr(self._key_pair, 'private_key', None)


class OpenStackSecurityGroup(BaseSecurityGroup):

    def __init__(self, provider, security_group):
        super(OpenStackSecurityGroup, self).__init__(provider, security_group)

    @property
    def rules(self):
        # Update SG object; otherwise, recenlty added rules do now show
        self._security_group = self._provider.nova.security_groups.get(
            self._security_group)
        return [OpenStackSecurityGroupRule(self._provider, r, self)
                for r in self._security_group.rules]

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

        :rtype: bool
        :return: True if successful.
        """
        if src_group:
            for protocol in ['tcp', 'udp']:
                if self._provider.nova.security_group_rules.create(
                   parent_group_id=self._security_group.id,
                   ip_protocol=protocol,
                   from_port=1,
                   to_port=65535,
                   group_id=src_group.id):
                    return True
        else:
            if self._provider.nova.security_group_rules.create(
               parent_group_id=self._security_group.id,
               ip_protocol=ip_protocol,
               from_port=from_port,
               to_port=to_port,
               cidr=cidr_ip):
                return True

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = [json.loads(r) for r in json_rules]
        return json.dumps(js, sort_keys=True)


class OpenStackSecurityGroupRule(BaseSecurityGroupRule):

    def __init__(self, provider, rule, parent):
        super(OpenStackSecurityGroupRule, self).__init__(
            provider, rule, parent)

    @property
    def ip_protocol(self):
        return self._rule.get('ip_protocol')

    @property
    def from_port(self):
        return self._rule.get('from_port')

    @property
    def to_port(self):
        return self._rule.get('to_port')

    @property
    def cidr_ip(self):
        return self._rule.get('ip_range', {}).get('cidr')

    @property
    def group(self):
        cg = self._rule.get('group', {}).get('name')
        if cg:
            security_groups = self._provider.nova.security_groups.list()
            for sg in security_groups:
                if sg.name == cg:
                    return OpenStackSecurityGroup(self._provider, sg)
        return None

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        js['group'] = self.group.id if self.group else ''
        js['parent'] = self.parent.id if self.parent else ''
        return json.dumps(js, sort_keys=True)


class OpenStackBucketObject(BaseBucketObject):

    def __init__(self, provider, cbcontainer, obj):
        super(OpenStackBucketObject, self).__init__(provider)
        self.cbcontainer = cbcontainer
        self._obj = obj

    @property
    def id(self):
        return self._obj.get("name")

    @property
    def name(self):
        """
        Get this object's name.
        """
        return self._obj.get("name")

    def download(self, target_stream):
        """
        Download this object and write its
        contents to the target_stream.
        """
        _, content = self._provider.swift.get_object(
            self.cbcontainer.name, self.name, resp_chunk_size=65536)
        shutil.copyfileobj(content, target_stream)

    def upload(self, data):
        """
        Set the contents of this object to the data read from the source
        string.
        """
        self._provider.swift.put_object(self.cbcontainer.name, self.name,
                                        data)

    def delete(self):
        """
        Delete this object.

        :rtype: bool
        :return: True if successful
        """
        try:
            self._provider.swift.delete_object(self.cbcontainer.name,
                                               self.name)
        except ClientException as err:
            if err.http_status == 404:
                return True
        return False


class OpenStackBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(OpenStackBucket, self).__init__(provider)
        self._bucket = bucket

    @property
    def id(self):
        return self._bucket.get("name")

    @property
    def name(self):
        """
        Get this bucket's name.
        """
        return self._bucket.get("name")

    def get(self, key):
        """
        Retrieve a given object from this bucket.
        """
        _, object_list = self._provider.swift.get_container(
            self.name, prefix=key)
        if object_list:
            return OpenStackBucketObject(self._provider, self,
                                         object_list[0])
        else:
            return None

    def list(self, limit=None, marker=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        _, object_list = self._provider.swift.get_container(
            self.name, limit=oshelpers.os_result_limit(self._provider, limit),
            marker=marker)
        cb_objects = [OpenStackBucketObject(
            self._provider, self, obj) for obj in object_list]

        return oshelpers.to_server_paged_list(
            self._provider,
            cb_objects,
            limit)

    def delete(self, delete_contents=False):
        """
        Delete this bucket.
        """
        self._provider.swift.delete_container(self.name)

    def create_object(self, object_name):
        self._provider.swift.put_object(self.name, object_name, None)
        return self.get(object_name)
