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
from cloudbridge.providers.interfaces import Instance
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import KeyPair


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

        # self.Compute = EC2ComputeService(self)
        # self.Images = EC2ImageService(self)
        self.security = OpenStackSecurityService(self)
        # self.BlockStore = EC2BlockStore(self)
        # self.ObjectStore = EC2ObjectStore(self)

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
