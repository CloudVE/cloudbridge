"""
Services implemented by this provider
"""

from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import ImageService
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import SecurityGroup
from cloudbridge.providers.interfaces import SecurityService

from .types import EC2Instance
from .types import EC2MachineImage


class EC2SecurityService(SecurityService):

    def __init__(self, provider):
        self.provider = provider

    def list_key_pairs(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self.provider.ec2_conn.get_all_key_pairs()
        return [BaseKeyPair(kp.name) for kp in key_pairs]

    def list_security_groups(self):
        """
        Create a new security group

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        groups = self.provider.ec2_conn.get_all_security_groups()
        return [BaseSecurityGroup(group.name) for group in groups]


class EC2ImageService(ImageService):

    def __init__(self, provider):
        self.provider = provider

    def get_image(self, id):
        """
        Returns an Image given its id
        """
        image = self.provider.ec2_conn.get_image(id)
        if image:
            return EC2MachineImage(self.provider, image)
        else:
            return None

    def find_image(self, name):
        """
        Searches for an image by a given list of attributes
        """
        raise NotImplementedError(
            'find_image not implemented by this provider')

    def list_images(self):
        """
        List all images.
        """
        # TODO: get_all_images returns too many images - some kind of filtering
        # abilities are needed. Forced to "self" for now
        images = self.provider.ec2_conn.get_all_images(owner="self")
        return [EC2MachineImage(self.provider, image) for image in images]


class EC2ComputeService(ComputeService):

    def __init__(self, provider):
        self.provider = provider

    def create_instance(self, name, image, instance_type, zone=None, keypair=None, security_groups=None,
                        user_data=None, block_device_mapping=None, network_interfaces=None, **kwargs):
        """
        Creates a new virtual machine instance.
        """
        image_id = image.image_id if isinstance(image, MachineImage) else image
        instance_size = instance_type.name if isinstance(
            instance_type,
            InstanceType) else instance_type
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        keypair_name = keypair.name if isinstance(keypair, KeyPair) else keypair
        if security_groups:
            if isinstance(security_groups, list) and isinstance(security_groups[0], SecurityGroup):
                security_groups_list = [sg.name for sg in security_groups]
            else:
                security_groups_list = security_groups
        else:
            security_groups_list = None

        reservation = self.provider.ec2_conn.run_instances(image_id=image_id,
                                                           instance_type=instance_size,
                                                           min_count=1,
                                                           max_count=1,
                                                           placement=zone_name,
                                                           key_name=keypair_name,
                                                           security_groups=security_groups_list,
                                                           user_data=user_data
                                                           )
        if reservation:
            instance = EC2Instance(self.provider, reservation.instances[0])
            instance.name = name
        return instance
