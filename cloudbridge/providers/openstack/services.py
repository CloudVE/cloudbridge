"""
Services implemented by this provider
"""

from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import InstanceTypesService
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import SecurityGroup
from cloudbridge.providers.interfaces import SecurityService

from .types import OpenStackInstance
from .types import OpenStackInstanceType


class OpenStackSecurityService(SecurityService):

    def __init__(self, provider):
        self.provider = provider

    def list_key_pairs(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self.provider.nova.keypairs.list()
        return [BaseKeyPair(kp.id) for kp in key_pairs]

    def list_security_groups(self):
        """
        Create a new security group

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        groups = self.provider.nova.security_groups.list()
        return [BaseSecurityGroup(group.name) for group in groups]


class OpenStackInstanceTypesService(InstanceTypesService):

    def __init__(self, provider):
        self.provider = provider

    def list(self):
        return [OpenStackInstanceType(f) for f in self.provider.nova.flavors.list()]

    def find_by_name(self, name):
        return next((itype for itype in self.list() if itype.name == name), None)


class OpenStackComputeService(ComputeService):

    def __init__(self, provider):
        self.provider = provider
        self.instance_types = OpenStackInstanceTypesService(self.provider)

    def create_instance(self, name, image, instance_type, zone=None, keypair=None, security_groups=None,
                        user_data=None, block_device_mapping=None, network_interfaces=None, **kwargs):
        """
        Creates a new virtual machine instance.
        """
        image_id = image.image_id if isinstance(image, MachineImage) else image
        instance_size = instance_type.name if isinstance(
            instance_type,
            InstanceType) else self.instance_types.find_by_name(instance_type).id
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        keypair_name = keypair.name if isinstance(keypair, KeyPair) else keypair
        if security_groups:
            if isinstance(security_groups, list) and isinstance(security_groups[0], SecurityGroup):
                security_groups_list = [sg.name for sg in security_groups]
            else:
                security_groups_list = security_groups
        else:
            security_groups_list = None

        os_instance = self.provider.nova.servers.create(name, image_id,
                                                        instance_size,
                                                        min_count=1,
                                                        max_count=1,
                                                        availability_zone=zone_name,
                                                        key_name=keypair_name,
                                                        security_groups=security_groups_list,
                                                        userdata=user_data
                                                        )
        return OpenStackInstance(self.provider, os_instance)
