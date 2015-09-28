"""
Provider implementation based on boto library for EC2-compatible clouds.
"""

import os
from novaclient import client as nova_client
from keystoneclient import client as keystone_client
from keystoneclient import session
from keystoneclient.auth.identity import Password

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
from cloudbridge.providers.interfaces import InstanceTypesService
from cloudbridge.providers.interfaces import Instance


class OpenStackCloudProviderV1(BaseCloudProvider):

    def __init__(self, config):
        super(OpenStackCloudProviderV1, self).__init__(config)

        self.api_version = self._get_config_value(
            'api_version', os.environ.get('OS_COMPUTE_API_VERSION', 2))
        self.username = self._get_config_value('username', os.environ.get('OS_USERNAME', None))
        self.password = self._get_config_value('password', os.environ.get('OS_PASSWORD', None))
        self.tenant_name = self._get_config_value(
            'tenant_name', os.environ.get('OS_TENANT_NAME', None))
        self.auth_url = self._get_config_value('auth_url', os.environ.get('OS_AUTH_URL', None))

        self.nova = self._connect_nova()
        self.keystone = self._connect_keystone()

        self.compute = OpenStackComputeService(self)
        # self.images = EC2ImageService(self)
        self.security = OpenStackSecurityService(self)
        # self.block_store = EC2BlockStore(self)
        # self.object_store = EC2ObjectStore(self)

    def _connect_nova(self):
        """
        Get an openstack client object for the given cloud.
        """
        return nova_client.Client(
            self.api_version, self.username, self.password, self.tenant_name, self.auth_url)

    def _connect_keystone(self):
        """
        Get an openstack client object for the given cloud.
        """
        auth = Password(self.auth_url, username=self.username, password=self.password,
                        tenant_name=self.tenant_name)
        # Wow, the internal keystoneV2 implementation is terribly buggy. It needs both a separate Session object
        # and the username, password again for things to work correctly. Plus, a manual call to authenticate() is
        # also required if the service  catalogue needs to be queried
        keystone = keystone_client.Client(session=session.Session(auth=auth), auth_url=self.auth_url, username=self.username,
                                          password=self.password, tenant_name=self.tenant_name)
        keystone.authenticate()
        return keystone


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
        return self._ec2_instance.id

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
