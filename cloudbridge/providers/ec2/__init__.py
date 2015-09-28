"""
Provider implementation based on boto library for EC2-compatible clouds.
"""

import boto
import os
from boto.ec2.regioninfo import RegionInfo

from cloudbridge.providers.base import BaseCloudProvider
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import SecurityGroup
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import Instance


class EC2CloudProviderV1(BaseCloudProvider):

    def __init__(self, config):
        super(EC2CloudProviderV1, self).__init__(config)
        self.cloud_type = 'ec2'

        # Initialize cloud connection fields
        self.a_key = self._get_config_value('access_key', os.environ.get('EC2_ACCESS_KEY', None))
        self.s_key = self._get_config_value('secret_key', os.environ.get('EC2_SECRET_KEY', None))
        self.is_secure = self._get_config_value('is_secure', True)
        self.region_name = self._get_config_value('region_name', 'us-east-1')
        self.region_endpoint = self._get_config_value(
            'region_endpoint', 'ec2.us-east-1.amazonaws.com')
        self.ec2_port = self._get_config_value('ec2_port', '')
        self.ec2_conn_path = self._get_config_value('ec2_port', '/')

        # Create a connection object
        self.ec2_conn = self._connect_ec2()

        # Initialize provider services
        self.compute = EC2ComputeService(self)
        self.images = None  # EC2ImageService(self)
        self.security = EC2SecurityService(self)
        self.block_store = None  # EC2BlockStore(self)
        self.object_store = None  # EC2ObjectStore(self)

    def _connect_ec2(self):
        """
        Get a boto connection object for the given cloud.
        """
        r = RegionInfo(name=self.region_name, endpoint=self.region_endpoint)
        ec2_conn = boto.connect_ec2(aws_access_key_id=self.a_key,
                                    aws_secret_access_key=self.s_key,
                                    # api_version is needed for availability zone support for EC2
                                    api_version='2012-06-01' if self.cloud_type == 'ec2' else None,
                                    is_secure=self.is_secure,
                                    region=r,
                                    port=self.ec2_port,
                                    path=self.ec2_conn_path,
                                    validate_certs=False)
        return ec2_conn


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
