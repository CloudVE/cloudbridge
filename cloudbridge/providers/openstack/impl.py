"""
Provider implementation based on openstack python client for OpenStack compatible clouds.
"""

import os

from keystoneclient import client as keystone_client
from keystoneclient import session
from keystoneclient.auth.identity import Password
from novaclient import client as nova_client

from cloudbridge.providers.base import BaseCloudProvider

from .services import OpenStackComputeService
from .services import OpenStackImageService
from .services import OpenStackSecurityService


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
        self.images = OpenStackImageService(self)
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
