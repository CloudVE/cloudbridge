"""
DataTypes used by this provider
"""

from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.interfaces import Instance
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import MachineImage


class OpenStackImage(MachineImage):

    def __init__(self, provider, os_image):
        self.provider = provider
        if isinstance(os_image):
            self._os_image = os_image._os_image
        else:
            self._os_image = os_image

    def image_id(self):
        """
        Get the image identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        return self._os_image.id

    def name(self):
        """
        Get the image name.

        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._os_image.name

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
        return "<OSInstanceType: {0}={1}>".format(self.id, self.name)


class OpenStackInstance(Instance):

    def __init__(self, provider, os_instance):
        self.provider = provider
        self._os_instance = os_instance

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

    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        return self._os_instance.networks['public']

    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return self._os_instance.networks['private']

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

    def image_id(self):
        """
        Get the image ID for this insance.
        """
        return self._os_instance.image_id

    def placement_zone(self):
        """
        Get the placement zone where this instance is running.
        """
        return self._os_instance.availability_zone

    def mac_address(self):
        """
        Get the MAC address for this instance.
        """
        raise NotImplementedError(
            'mac_address not implemented by this provider')

    def security_group_ids(self):
        """
        Get the security group IDs associated with this instance.
        """
        return [BaseSecurityGroup(group.name) for group in self._os_instance.security_groups]

    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return BaseKeyPair(self._os_instance.key_name)

    def create_image(self, name):
        """
        Create a new image based on this instance.
        """
        image_id = self._os_instance.create_image(name)
        return OpenStackImage(self.provider, self.provider.images.get(image_id))
