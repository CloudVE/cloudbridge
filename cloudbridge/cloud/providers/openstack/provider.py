"""
Provider implementation based on OpenStack Python clients for OpenStack
compatible clouds.
"""

import os

from cinderclient import client as cinder_client
from keystoneclient import client as keystone_client
from keystoneclient import session
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
from novaclient import shell as nova_shell
from swiftclient import client as swift_client

from cloudbridge.cloud.base import BaseCloudProvider

from .services import OpenStackBlockStoreService
from .services import OpenStackComputeService
from .services import OpenStackNetworkService
from .services import OpenStackObjectStoreService
from .services import OpenStackSecurityService


class OpenStackCloudProvider(BaseCloudProvider):

    PROVIDER_ID = 'openstack'

    def __init__(self, config):
        super(OpenStackCloudProvider, self).__init__(config)

        # Initialize cloud connection fields
        self.username = self._get_config_value(
            'os_username', os.environ.get('OS_USERNAME', None))
        self.password = self._get_config_value(
            'os_password', os.environ.get('OS_PASSWORD', None))
        self.tenant_name = self._get_config_value(
            'os_tenant_name', os.environ.get('OS_TENANT_NAME', None))
        self.auth_url = self._get_config_value(
            'os_auth_url', os.environ.get('OS_AUTH_URL', None))
        self.region_name = self._get_config_value(
            'os_region_name', os.environ.get('OS_REGION_NAME', None))
        self.project_name = self._get_config_value(
            'os_project_name', os.environ.get('OS_PROJECT_NAME', None))
        self.project_domain_name = self._get_config_value(
            'os_project_domain_name',
            os.environ.get('OS_PROJECT_DOMAIN_NAME', None))
        self.user_domain_name = self._get_config_value(
            'os_user_domain_name', os.environ.get('OS_USER_DOMAIN_NAME', None))
        self.identity_api_version = self._get_config_value(
            'os_identity_api_version',
            os.environ.get('OS_IDENTITY_API_VERSION', None))
        # Allow individual service connections to have their own values but
        # default to a the ones defined above.
        self.swift_username = self._get_config_value(
            'os_swift_username',
            os.environ.get('OS_SWIFT_USERNAME', self.username))
        self.swift_password = self._get_config_value(
            'os_swift_password',
            os.environ.get('OS_SWIFT_PASSWORD', self.password))
        self.swift_tenant_name = self._get_config_value(
            'os_swift_tenant_name',
            os.environ.get('OS_SWIFT_TENANT_NAME', self.tenant_name))
        self.swift_auth_url = self._get_config_value(
            'os_swift_auth_url',
            os.environ.get('OS_SWIFT_AUTH_URL', self.auth_url))
        self.swift_region_name = self._get_config_value(
            'os_swift_region_name',
            os.environ.get('OS_SWIFT_REGION_NAME', self.region_name))

        # Service connections, lazily initialized
        self._nova = None
        self._keystone = None
        self._glance = None
        self._cinder = None
        self._swift = None
        self._neutron = None

        # Initialize provider services
        self._compute = OpenStackComputeService(self)
        self._network = OpenStackNetworkService(self)
        self._security = OpenStackSecurityService(self)
        self._block_store = OpenStackBlockStoreService(self)
        self._object_store = OpenStackObjectStoreService(self)

    @property
    def nova(self):
        if not self._nova:
            self._nova = self._connect_nova()
        return self._nova

    @property
    def keystone(self):
        if not self._keystone:
            self._keystone = self._connect_keystone()
        return self._keystone

    @property
    def _keystone_version(self):
        """
        Return the numberic version of remote server Keystone.

        :rtype: ``int``
        :return: Keystone version as an int (currently, 2 or 3).
        """
        ks_version = keystone_client.Client(auth_url=self.auth_url).version
        if ks_version == 'v3':
            return 3
        return 2

    @property
    def _keystone_session(self):
        """
        Connect to Keystone and return a session object.

        :rtype: :class:`keystoneclient.session.Session`
        :return: A Keystone session object.
        """
        def connect_v2():
            from keystoneclient.auth.identity import Password as password_v2
            auth = password_v2(self.auth_url, username=self.username,
                               password=self.password,
                               tenant_name=self.tenant_name)
            return session.Session(auth=auth)

        def connect_v3():
            from keystoneclient.auth.identity.v3 import Password as password_v3
            auth = password_v3(auth_url=self.auth_url,
                               username=self.username,
                               password=self.password,
                               user_domain_name=self.user_domain_name,
                               project_domain_name=self.project_domain_name,
                               project_name=self.project_name)
            return session.Session(auth=auth)

        return connect_v3() if self._keystone_version == 3 else connect_v2()

#     @property
#     def glance(self):
#         if not self._glance:
#             self._glance = self._connect_glance()
#         return self._glance

    @property
    def cinder(self):
        if not self._cinder:
            self._cinder = self._connect_cinder()
        return self._cinder

    @property
    def swift(self):
        if not self._swift:
            self._swift = self._connect_swift()
        return self._swift

    @property
    def neutron(self):
        if not self._neutron:
            self._neutron = self._connect_neutron()
        return self._neutron

    @property
    def compute(self):
        return self._compute

    @property
    def network(self):
        return self._network

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
        return self._connect_nova_region(self.region_name)

    def _connect_nova_region(self, region_name):
        """
        Get an OpenStack Nova (compute) client object for the given cloud.
        """
        def connect_pwd():
            """
            Connect using username and password parameters.
            """
            nova = nova_client.Client(
                api_version, username=self.username, api_key=self.password,
                project_id=self.tenant_name, auth_url=self.auth_url,
                region_name=region_name, service_name=service_name,
                http_log_debug=True if self.config.debug_mode else False)
            nova.authenticate()
            return nova

        def connect_sess():
            """
            Connect using a Keystone session object.
            """
            return nova_client.Client(
                api_version, session=self._keystone_session,
                service_name=service_name,
                http_log_debug=True if self.config.debug_mode else False)

        api_version = self._get_config_value(
            'os_compute_api_version',
            os.environ.get('OS_COMPUTE_API_VERSION', 2))
        service_name = self._get_config_value(
            'nova_service_name',
            os.environ.get('NOVA_SERVICE_NAME', None))

        if self.config.debug_mode:
            nova_shell.OpenStackComputeShell().setup_debugging(True)

        return connect_sess() if self._keystone_version == 3 else connect_pwd()

    def _connect_keystone(self):
        """
        Get an OpenStack Keystone (identity) client object for the given cloud.
        """
        def connect_v2():
            # Wow, the internal keystoneV2 implementation is terribly buggy. It
            # needs both a separate Session object and the username, password
            # again for things to work correctly. Plus, a manual call to
            # authenticate() is also required if the service catalogue needs
            # to be queried.
            keystone = keystone_client.Client(
                session=self._keystone_session,
                auth_url=self.auth_url,
                username=self.username,
                password=self.password,
                tenant_name=self.tenant_name,
                region_name=self.region_name)
            keystone.authenticate()
            return keystone

        def connect_v3():
            return keystone_client.Client(session=self._keystone_session,
                                          auth_url=self.auth_url)

        return connect_v3() if self._keystone_version == 3 else connect_v2()

    def _connect_cinder(self):
        """
        Get an OpenStack Cinder (block storage) client object for the given
        cloud.
        """
        def connect_pwd():
            """
            Connect using username and password parameters.
            """
            return cinder_client.Client(
                api_version, username=self.username, api_key=self.password,
                project_id=self.tenant_name, auth_url=self.auth_url)

        def connect_sess():
            """
            Connect using a Keystone session object.
            """
            return cinder_client.Client(
                api_version, session=self._keystone_session)

        api_version = self._get_config_value(
            'os_volume_api_version',
            os.environ.get('OS_VOLUME_API_VERSION', 2))

        return connect_sess() if self._keystone_version == 3 else connect_pwd()

#     def _connect_glance(self):
#         """
#         Get an OpenStack Glance (VM images) client object for the given
#         cloud.
#         """
#         api_version = self._get_config_value(
#             'os_image_api_version',
#             os.environ.get('OS_IMAGE_API_VERSION', 1))
#
#         return glance_client.Client(version=api_version,
#                                     session=self.keystone.session)

    def _connect_swift(self):
        """
        Get an OpenStack Swift (object store) client object for the given
        cloud.
        """
        os_options = {'region_name': self.swift_region_name}
        return swift_client.Connection(
            authurl=self.swift_auth_url, auth_version='2',
            user=self.swift_username, key=self.swift_password,
            tenant_name=self.swift_tenant_name,
            os_options=os_options)

    def _connect_neutron(self):
        """
        Get an OpenStack Neutron (networking) client object for the given
        cloud.
        """
        def connect_pwd():
            """
            Connect using username and password parameters.
            """
            return neutron_client.Client(
                username=self.username, password=self.password,
                tenant_name=self.tenant_name, auth_url=self.auth_url)

        def connect_sess():
            """
            Connect using a Keystone session object.
            """
            return neutron_client.Client(session=self._keystone_session)

        return connect_sess() if self._keystone_version == 3 else connect_pwd()
