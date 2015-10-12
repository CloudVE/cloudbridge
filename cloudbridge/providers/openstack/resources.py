"""
DataTypes used by this provider
"""
import shutil

import ipaddress
from swiftclient.exceptions import ClientException

from cloudbridge.providers.base import BaseInstance
from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseMachineImage
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.base import BaseSnapshot
from cloudbridge.providers.base import BaseVolume
from cloudbridge.providers.interfaces import Container
from cloudbridge.providers.interfaces import ContainerObject
from cloudbridge.providers.interfaces import InstanceState
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import MachineImageState
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import Region
from cloudbridge.providers.interfaces import SnapshotState
from cloudbridge.providers.interfaces import VolumeState


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
        self.provider = provider
        if isinstance(os_image, OpenStackMachineImage):
            self._os_image = os_image._os_image
        else:
            self._os_image = os_image

    @property
    def image_id(self):
        """
        Get the image identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        return self._os_image.id

    @property
    def name(self):
        """
        Get the image name.

        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._os_image.name

    @property
    def description(self):
        """
        Get the image description.

        :rtype: ``str``
        :return: Description for this image as returned by the cloud middleware
        """
        return self._os_image.description

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
        image = self.provider.images.get_image(self.image_id)
        if image:
            self._os_image = image._os_image
        else:
            # The image no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_image.status = 'unknown'


class OpenStackPlacementZone(PlacementZone):

    def __init__(self, provider, zone):
        self.provider = provider
        if isinstance(zone, OpenStackPlacementZone):
            self._os_zone = zone._os_zone
        else:
            self._os_zone = zone

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
        return self._os_zone.region_name


class OpenStackInstanceType(InstanceType):

    def __init__(self, os_flavor):
        self.os_flavor = os_flavor

    @property
    def id(self):
        return self.os_flavor.id

    @property
    def name(self):
        return self.os_flavor.name

    def __repr__(self):
        return "<CB-OSInstanceType: {0}={1}>".format(self.id, self.name)


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
        self.provider = provider
        self._os_instance = os_instance

    @property
    def instance_id(self):
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
                for addresses in self._os_instance.networks.itervalues()
                for address in addresses
                if not ipaddress.ip_address(address).is_private]

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return [address
                for addresses in self._os_instance.networks.itervalues()
                for address in addresses
                if ipaddress.ip_address(address).is_private]

    @property
    def instance_type(self):
        """
        Get the instance type.
        """
        return OpenStackInstanceType(self._os_instance.flavor)

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
            self.provider,
            getattr(self._os_instance, 'OS-EXT-AZ:availability_zone', None))

    @property
    def mac_address(self):
        """
        Get the MAC address for this instance.
        """
        raise NotImplementedError(
            'mac_address not implemented by this provider')

    @property
    def security_groups(self):
        """
        Get the security groups associated with this instance.
        """
        security_groups = []
        for group in self._os_instance.security_groups:
            security_groups.append(self.provider.nova.security_groups.find(
                name=group.get('name')))
        return [OpenStackSecurityGroup(self.provider, group)
                for group in security_groups]

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
            self.provider, self.provider.images.get_image(image_id))

    @property
    def state(self):
        return OpenStackInstance.INSTANCE_STATE_MAP.get(
            self._os_instance.status, InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        instance = self.provider.compute.get_instance(
            self.instance_id)
        if instance:
            self._os_instance = instance._os_instance
        else:
            # The instance no longer exists and cannot be refreshed.
            # set the status to unknown
            self._os_instance.status = 'unknown'

    def __repr__(self):
        return "<CB-OSInstance: {0} ({1})>".format(self.name, self.instance_id)


class OpenStackRegion(Region):

    def __init__(self, provider, os_region):
        self.provider = provider
        self._os_region = os_region

    @property
    def name(self):
        return self._os_region.zoneName

    def __repr__(self):
        return "<CB-OSRegion: {0}>".format(self.name)


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
        self.provider = provider
        self._volume = volume

    @property
    def volume_id(self):
        return self._volume.id

    @property
    def name(self):
        """
        Get the volume name.
        """
        return self._volume.name

    @name.setter
    def name(self, value):
        """
        Set the volume name.
        """
        self._volume.name = value
        self._volume.update()

    def attach(self, instance, device):
        """
        Attach this volume to an instance.
        """
        instance_id = instance.instance_id if isinstance(
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
        return self.provider.block_store.snapshots.create_snapshot(
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
        vol = self.provider.block_store.volumes.get_volume(
            self.volume_id)
        if vol:
            self._volume = vol._volume
        else:
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._volume.status = 'unknown'

    def __repr__(self):
        return "<CB-OSVolume: {0} ({1})>".format(self.volume_id, self.name)


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
        self.provider = provider
        self._snapshot = snapshot

    @property
    def snapshot_id(self):
        return self._snapshot.id

    @property
    def name(self):
        """
        Get the snapshot name.
        """
        return self._snapshot.name

    @name.setter
    def name(self, value):
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
        snap = self.provider.block_store.snapshots.get_snapshot(
            self.snapshot_id)
        if snap:
            self._snapshot = snap._snapshot
        else:
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._snapshot.status = 'unknown'

    def delete(self):
        """
        Delete this snapshot.
        """
        self._snapshot.delete()

    def __repr__(self):
        return "<CB-OSSnapshot: {0} ({1}>".format(self.snapshot_id, self.name)


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
        if hasattr(self._key_pair, 'private_key'):
            return self._key_pair.private_key
        return None


class OpenStackSecurityGroup(BaseSecurityGroup):

    def __init__(self, provider, security_group):
        super(OpenStackSecurityGroup, self).__init__(provider, security_group)

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
                self.provider.nova.security_group_rules.create(
                    parent_group_id=self._security_group.id,
                    ip_protocol=protocol,
                    from_port=1,
                    to_port=65535,
                    group_id=src_group.id)
        else:
            return self.provider.nova.security_group_rules.create(
                parent_group_id=self._security_group.id,
                ip_protocol=ip_protocol,
                from_port=from_port,
                to_port=to_port,
                cidr=cidr_ip)


class OpenStackContainerObject(ContainerObject):

    def __init__(self, provider, cbcontainer, obj):
        self.provider = provider
        self.cbcontainer = cbcontainer
        self._obj = obj

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
        _, content = self.provider.swift.get_object(
            self.cbcontainer.name, self.name, resp_chunk_size=65536)
        shutil.copyfileobj(content, target_stream)

    def upload(self, data):
        """
        Set the contents of this object to the data read from the source
        string.
        """
        self.provider.swift.put_object(self.cbcontainer.name, self.name,
                                       data)

    def delete(self):
        """
        Delete this object.

        :rtype: bool
        :return: True if successful
        """
        try:
            self.provider.swift.delete_object(self.cbcontainer.name, self.name)
        except ClientException as err:
            if err.http_status == 404:
                return True
        return False

    def __repr__(self):
        return "<CB-OpenStackContainerObject: {0}>".format(self.name)


class OpenStackContainer(Container):

    def __init__(self, provider, container):
        self.provider = provider
        self._container = container

    @property
    def name(self):
        """
        Get this container's name.
        """
        return self._container.get("name")

    def get(self, key):
        """
        Retrieve a given object from this container.
        """
        _, object_list = self.provider.swift.get_container(
            self.name, prefix=key)
        if object_list:
            return OpenStackContainerObject(self.provider, self,
                                            object_list[0])
        else:
            return None

    def list(self):
        """
        List all objects within this container.

        :rtype: ContainerObject
        :return: List of all available ContainerObjects within this container
        """
        _, object_list = self.provider.swift.get_container(self.name)
        return [
            OpenStackContainer(self.provider, o) for o in object_list]

    def delete(self, delete_contents=False):
        """
        Delete this container.
        """
        self.provider.swift.delete_container(self.name)

    def create_object(self, object_name):
        self.provider.swift.put_object(self.name, object_name, None)
        return self.get(object_name)

    def __repr__(self):
        return "<CB-OpenStackContainer: {0}>".format(self.name)
