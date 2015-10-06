"""
DataTypes used by this provider
"""

from cloudbridge.providers.base import BaseInstance
from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseMachineImage
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.base import BaseSnapshot
from cloudbridge.providers.base import BaseVolume
from cloudbridge.providers.interfaces import InstanceState
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import MachineImageState
from cloudbridge.providers.interfaces import SnapshotState
from cloudbridge.providers.interfaces import VolumeState
from cloudbridge.providers.interfaces.resources import PlacementZone


class AWSMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'pending': MachineImageState.PENDING,
        'available': MachineImageState.AVAILABLE,
        'failed': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
        self.provider = provider
        if isinstance(image, AWSMachineImage):
            self._ec2_image = image._ec2_image
        else:
            self._ec2_image = image

    @property
    def image_id(self):
        """
        Get the image identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        return self._ec2_image.id

    @property
    def name(self):
        """
        Get the image name.

        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._ec2_image.name

    @property
    def description(self):
        """
        Get the image description.

        :rtype: ``str``
        :return: Description for this image as returned by the cloud middleware
        """
        return self._ec2_image.description

    def delete(self):
        """
        Delete this image
        """
        self._ec2_image.deregister()

    @property
    def state(self):
        return AWSMachineImage.IMAGE_STATE_MAP.get(
            self._ec2_image.state, MachineImageState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        self._ec2_image = self.provider.images.get_image(
            self.image_id)._ec2_image


class AWSPlacementZone(PlacementZone):

    def __init__(self, provider, zone):
        self.provider = provider
        if isinstance(zone, AWSPlacementZone):
            self._aws_zone = zone._aws_zone
        else:
            self._aws_zone = zone

    @property
    def name(self):
        """
        Get the zone name.

        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        return self._aws_zone

    @property
    def region(self):
        """
        Get the region that this zone belongs to.

        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        return self._aws_zone.region_name


class AWSInstanceType(InstanceType):

    def __init__(self, instance_type):
        self.instance_type = instance_type

    @property
    def id(self):
        return self.instance_type

    @property
    def name(self):
        return self.instance_type

    def __repr__(self):
        return "<CB-AWSInstanceType: {0}>".format(self.id)


class AWSInstance(BaseInstance):

    # ref:
    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
    INSTANCE_STATE_MAP = {
        'pending': InstanceState.PENDING,
        'running': InstanceState.RUNNING,
        'shutting-down': InstanceState.CONFIGURING,
        'terminated': InstanceState.TERMINATED,
        'stopping': InstanceState.CONFIGURING,
        'stopped': InstanceState.STOPPED
    }

    def __init__(self, provider, ec2_instance):
        self.provider = provider
        self._ec2_instance = ec2_instance

    @property
    def instance_id(self):
        """
        Get the instance identifier.
        """
        return self._ec2_instance.id

    @property
    def name(self):
        """
        Get the instance name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._ec2_instance.tags.get('Name')

    @name.setter
    def name(self, value):
        """
        Set the instance name.
        """
        self._ec2_instance.add_tag('Name', value)

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        return [self._ec2_instance.ip_address]

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return [self._ec2_instance.private_ip_address]

    @property
    def instance_type(self):
        """
        Get the instance type.
        """
        return AWSInstanceType(self._ec2_instance.instance_type)

    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).
        """
        self._ec2_instance.reboot()

    def terminate(self):
        """
        Permanently terminate this instance.
        """
        self._ec2_instance.terminate()

    def image_id(self):
        """
        Get the image ID for this insance.
        """
        return self._ec2_instance.image_id

    @property
    def placement_zone(self):
        """
        Get the placement zone where this instance is running.
        """
        return AWSPlacementZone(self.provider, self._ec2_instance.placement)

    @property
    def mac_address(self):
        """
        Get the MAC address for this instance.
        """
        raise NotImplementedError(
            'mac_address not implemented by this provider')

    @property
    def security_group_ids(self):
        """
        Get the security group IDs associated with this instance.
        """
        return [BaseSecurityGroup(group.name)
                for group in self._ec2_instance.groups]

    @property
    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return BaseKeyPair(self._ec2_instance.key_name)

    def create_image(self, name):
        """
        Create a new image based on this instance.
        """
        image_id = self._ec2_instance.create_image(name)
        image = self.provider.images.get_image(image_id)
        return AWSMachineImage(self.provider, image)

    @property
    def state(self):
        return AWSInstance.INSTANCE_STATE_MAP.get(
            self._ec2_instance.state, InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        self._ec2_instance.update()

    def __repr__(self):
        return "<CB-AWSInstance: {0}({1})>".format(self.name, self.instance_id)


class AWSVolume(BaseVolume):

    # Ref:
    # http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/
    # ApiReference-cmd-DescribeVolumes.html
    VOLUME_STATE_MAP = {
        'creating': VolumeState.CREATING,
        'available': VolumeState.AVAILABLE,
        'in-use': VolumeState.IN_USE,
        'deleting': VolumeState.CONFIGURING,
        'deleted': VolumeState.DELETED,
        'error': VolumeState.ERROR
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

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._volume.tags.get('Name')

    @name.setter
    def name(self, value):
        """
        Set the volume name.
        """
        self._volume.add_tag('Name', value)

    def attach(self, instance, device):
        """
        Attach this volume to an instance.
        """
        instance_id = instance.instance_id if isinstance(
            instance,
            AWSInstance) else instance
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
        snap = AWSSnapshot(
            self.provider,
            self._volume.create_snapshot(
                description=description))
        snap.name = name
        return snap

    def delete(self):
        """
        Delete this volume.
        """
        self._volume.delete()

    @property
    def state(self):
        return AWSVolume.VOLUME_STATE_MAP.get(
            self._volume.status, VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        self._volume.update()

    def __repr__(self):
        return "<CB-AWSVolume: {0} ({1})>".format(self.volume_id, self.name)


class AWSSnapshot(BaseSnapshot):

    # Ref: http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/
    # ApiReference-cmd-DescribeSnapshots.html
    SNAPSHOT_STATE_MAP = {
        'pending': SnapshotState.PENDING,
        'completed': SnapshotState.AVAILABLE,
        'error': SnapshotState.ERROR
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

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._snapshot.tags.get('Name')

    @name.setter
    def name(self, value):
        """
        Set the snapshot name.
        """
        self._snapshot.add_tag('Name', value)

    @property
    def state(self):
        return AWSSnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.status, SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        self._snapshot.update()

    def delete(self):
        """
        Delete this snapshot.
        """
        self._snapshot.delete()

    def __repr__(self):
        return "<CB-AWSVolume: {0} ({1}>".format(self.snapshot_id, self.name)
