"""
Provider implementation based on openstack python client for OpenStack
compatible clouds.
"""

import os

from cinderclient import client as cinder_client
from keystoneclient import client as keystone_client
from keystoneclient import session
from keystoneclient.auth.identity import Password
from novaclient import client as nova_client
from swiftclient import client as swift_client

from cloudbridge.providers.base import BaseCloudProvider

from .services import OpenStackBlockStoreService
from .services import OpenStackComputeService
from .services import OpenStackImageService
from .services import OpenStackObjectStoreService
from .services import OpenStackSecurityService


class OpenStackCloudProviderV1(BaseCloudProvider):

    def __init__(self, config):
        super(OpenStackCloudProviderV1, self).__init__(config)

        self.username = self._get_config_value(
            'username', os.environ.get('OS_USERNAME', None))
        self.password = self._get_config_value(
            'password', os.environ.get('OS_PASSWORD', None))
        self.tenant_name = self._get_config_value(
            'tenant_name', os.environ.get('OS_TENANT_NAME', None))
        self.auth_url = self._get_config_value(
            'auth_url', os.environ.get('OS_AUTH_URL', None))
        self.region_name = self._get_config_value(
            'region_name', os.environ.get('OS_REGION_NAME', None))

        self.nova = self._connect_nova()
        self.keystone = self._connect_keystone()
        self.cinder = self._connect_cinder()
        self.swift = self._connect_swift()

        self._compute = OpenStackComputeService(self)
        self._images = OpenStackImageService(self)
        self._security = OpenStackSecurityService(self)
        self._block_store = OpenStackBlockStoreService(self)
        self._object_store = OpenStackObjectStoreService(self)

    @property
    def compute(self):
        return self._compute

    @property
    def images(self):
        return self._images

    @property
    def security(self):
        return self._security

    @property
    def block_store(self):
        return self._block_store

    @property
    def object_store(self):
        return self._object_store

    def _connect_nova(self):
        """
        Get an openstack nova client object for the given cloud.
        """
        api_version = self._get_config_value(
            'os_compute_api_version',
            os.environ.get('OS_COMPUTE_API_VERSION', 2))
        service_name = self._get_config_value(
            'nova_service_name',
            os.environ.get('NOVA_SERVICE_NAME', None))

        return nova_client.Client(
            api_version, username=self.username, api_key=self.password,
            project_id=self.tenant_name, auth_url=self.auth_url,
            region_name=self.region_name, service_name=service_name)

    def _connect_keystone(self):
        """
        Get an openstack keystone client object for the given cloud.
        """
        auth = Password(self.auth_url, username=self.username,
                        password=self.password, tenant_name=self.tenant_name)
        # Wow, the internal keystoneV2 implementation is terribly buggy. It
        # needs both a separate Session object and the username, password again
        # for things to work correctly. Plus, a manual call to authenticate()
        # is also required if the service  catalogue needs to be queried
        keystone = keystone_client.Client(
            session=session.Session(auth=auth),
            auth_url=self.auth_url,
            username=self.username,
            password=self.password,
            tenant_name=self.tenant_name,
            region_name=self.region_name)
        keystone.authenticate()
        return keystone

    def _connect_cinder(self):
        """
        Get an openstack cinder client object for the given cloud.
        """
        api_version = self._get_config_value(
            'os_volume_api_version',
            os.environ.get('OS_VOLUME_API_VERSION', 2))

        return cinder_client.Client(
            api_version, username=self.username, api_key=self.password,
            project_id=self.tenant_name, auth_url=self.auth_url)

    def _connect_swift(self):
        """
        Get an openstack swift client object for the given cloud.
        """
        os_options = {'region_name': self.region_name}
        return swift_client.Connection(
            authurl=self.auth_url, auth_version='2', user=self.username,
            key=self.password, tenant_name=self.tenant_name,
            os_options=os_options)
