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
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import KeyPair


class OpenStackCloudProviderV1(BaseCloudProvider):

    def __init__(self, config):
        self.config = config

        # Initialize optional fields
        if isinstance(config, dict):
            self.api_version = config.get(
                'api_version', os.environ.get('OS_COMPUTE_API_VERSION', 2))
            self.username = config.get('username', os.environ.get('OS_USERNAME', None))
            self.password = config.get('password', os.environ.get('OS_PASSWORD', None))
            self.tenant_name = config.get('tenant_name', os.environ.get('OS_TENANT_NAME', None))
            self.auth_url = config.get('auth_url', os.environ.get('OS_AUTH_URL', None))
        else:
            self.api_version = config.api_version if hasattr(
                config, 'api_version') and config.api_version else os.environ.get('OS_COMPUTE_API_VERSION', None)
            self.username = config.username if hasattr(
                config, 'username') and config.username else os.environ.get('OS_USERNAME', None)
            self.password = config.password if hasattr(
                config, 'password') and config.password else os.environ.get('OS_PASSWORD', None)
            self.tenant_name = config.tenant_name if hasattr(
                config, 'tenant_name') and config.tenant_name else os.environ.get('OS_TENANT_NAME', None)
            self.auth_url = config.auth_url if hasattr(
                config, 'auth_url') and config.auth_url else os.environ.get('OS_AUTH_URL', None)

        self._nova = self._connect_nova()
        self._keystone = self._connect_keystone()

        # self.Compute = EC2ComputeService(self)
        # self.Images = EC2ImageService(self)
        self.security = OpenStackSecurityService(self)
        # self.BlockStore = EC2BlockStore(self)
        # self.ObjectStore = EC2ObjectStore(self)

    def _connect_nova(self):
        """
        Get an openstack client object for the given cloud.
        """
        return nova_client.Client(self.api_version, self.username, self.password, self.tenant_name, self.auth_url)

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
        key_pairs = self.provider._nova.keypairs.list()
        return [KeyPair(kp.id) for kp in key_pairs]

    def list_security_groups(self):
        """
        Create a new security group

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        groups = self.provider._nova.security_groups.list()
        return [BaseSecurityGroup(group.name) for group in groups]
