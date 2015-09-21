"""
Provider implementation based on boto library for EC2-compatible clouds.
"""

import os
from novaclient import client
from cloudbridge.providers.interfaces import CloudProvider
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import KeyPair


class OpenStackCloudProviderV1(CloudProvider):

    def __init__(self, config):
        self.config = config

        # Initialize cloud connection fields
        if isinstance(config, dict):
            self.api_version = config.get(
                'api_version', os.environ.get('OS_COMPUTE_API_VERSION', 2))
            self.username = config.get('username', os.environ.get('OS_USERNAME', None))
            self.password = config.get('password', os.environ.get('OS_PASSWORD', None))
            self.tenant_name = config.get('tenant_name', os.environ.get('OS_TENANT_NAME', None))
            self.auth_url = config.get('auth_url', os.environ.get('OS_AUTH_URL', None))
        else:
            self.username = config.username if hasattr(config, 'username') and \
                config.username else os.environ.get('OS_USERNAME')
            self.password = config.password if hasattr(config, 'password') and \
                config.password else os.environ.get('OS_PASSWORD')
            self.tenant_name = config.tenant_name if hasattr(config, 'tenant_name') \
                and config.tenant_name else os.environ.get('OS_TENANT_NAME')
            self.auth_url = config.auth_url if hasattr(config, 'auth_url') and \
                config.auth_url else os.environ.get('OS_AUTH_URL')
            self.region_name = config.region_name if hasattr(config, 'region_name') \
                and config.region_name else os.environ.get('OS_REGION_NAME')

        # Create a connection object
        self.nova = self._connect_nova()

        # Initialize provider services
        self.compute = None  # OpenStackComputeService(self)
        self.images = None  # OpenStackImageService(self)
        self.security = OpenStackSecurityService(self)
        self.block_store = None  # OpenStackBlockStore(self)
        self.object_store = None  # OpenStackObjectStore(self)

    def _connect_nova(self):
        """
        Get an openstack client object for the given cloud.
        """
        return client.Client(self.api_version, self.username, self.password, self.tenant_name, self.auth_url)


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
        return [KeyPair(kp.id) for kp in key_pairs]
