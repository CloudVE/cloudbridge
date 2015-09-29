"""
DataTypes used by this provider
"""

from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.interfaces import Instance


class EC2Instance(Instance):

    def __init__(self, provider, ec2_instance):
        self.provider = provider
        self._ec2_instance = ec2_instance

    def instance_id(self):
        """
        Get the instance identifier.
        """
        return self._ec2_instance.id

    @property
    def name(self):
        """
        Get the instance name.
        """
        return self._ec2_instance.tags['Name']

    @name.setter
    def name(self, value):
        """
        Set the instance name.
        """
        self._ec2_instance.add_tag('Name', value)

    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        return [self._ec2_instance.ip_address]

    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return [self._ec2_instance.private_ip_address]

    def instance_type(self):
        """
        Get the instance type.
        """
        return [self._ec2_instance.instance_type]

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

    def placement_zone(self):
        """
        Get the placement zone where this instance is running.
        """
        return self._ec2_instance.placement

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
        return [BaseSecurityGroup(group.name) for group in self._ec2_instance.groups]

    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return BaseKeyPair(self._ec2_instance.key_name)