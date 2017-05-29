"""Provider implementation based on OpenStack Python clients for OpenStack."""

import inspect

import os

from cinderclient import client as cinder_client

from cloudbridge.cloud.base import BaseCloudProvider

from keystoneauth1 import session

from keystoneclient import client as keystone_client

from neutronclient.v2_0 import client as neutron_client

from novaclient import client as nova_client
from novaclient import shell as nova_shell

from swiftclient import client as swift_client

from .services import OpenStackBlockStoreService
from .services import OpenStackComputeService
from .services import OpenStackNetworkService
from .services import OpenStackObjectStoreService
from .services import OpenStackSecurityService


class OpenStackCloudProvider(BaseCloudProvider):
    """OpenStack provider implementation."""

    PROVIDER_ID = 'openstack'

    def __init__(self, config):
        super(OpenStackCloudProvider, self).__init__(config)
        self.cloud_type = 'openstack'

        # Initialize cloud connection fields
        self.username = self._get_config_value(
            'os_username', os.environ.get('OS_USERNAME', None))
        self.password = self._get_config_value(
            'os_password', os.environ.get('OS_PASSWORD', None))
        self.project_name = self._get_config_value(
            'os_project_name', os.environ.get('OS_PROJECT_NAME', None) or
            os.environ.get('OS_TENANT_NAME', None))
        self.auth_url = self._get_config_value(
            'os_auth_url', os.environ.get('OS_AUTH_URL', None))
        self.region_name = self._get_config_value(
            'os_region_name', os.environ.get('OS_REGION_NAME', None))
        self.project_domain_name = self._get_config_value(
            'os_project_domain_name',
            os.environ.get('OS_PROJECT_DOMAIN_NAME', None))
        self.user_domain_name = self._get_config_value(
            'os_user_domain_name', os.environ.get('OS_USER_DOMAIN_NAME', None))

        # Service connections, lazily initialized
        self._nova = None
        self._keystone = None
        self._glance = None
        self._cinder = None
        self._swift = None
        self._neutron = None

        # Additional cached variables
        self._cached_keystone_session = None

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
        Return the numeric version of remote Keystone server.

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

        :rtype: :class:`keystoneauth1.session.Session`
        :return: A Keystone session object.
        """
        if self._cached_keystone_session:
            return self._cached_keystone_session

        if self._keystone_version == 3:
            from keystoneauth1.identity.v3 import Password as Password_v3
            auth = Password_v3(auth_url=self.auth_url,
                               username=self.username,
                               password=self.password,
                               user_domain_name=self.user_domain_name,
                               project_domain_name=self.project_domain_name,
                               project_name=self.project_name)
            self._cached_keystone_session = session.Session(auth=auth)
        else:
            from keystoneauth1.identity.v2 import Password as Password_v2
            auth = Password_v2(self.auth_url, username=self.username,
                               password=self.password,
                               tenant_name=self.project_name)
            self._cached_keystone_session = session.Session(auth=auth)
        return self._cached_keystone_session

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
        """Get an OpenStack Nova (compute) client object."""
        # Force reauthentication with Keystone
        self._cached_keystone_session = None

        api_version = self._get_config_value(
            'os_compute_api_version',
            os.environ.get('OS_COMPUTE_API_VERSION', 2))
        service_name = self._get_config_value(
            'nova_service_name',
            os.environ.get('NOVA_SERVICE_NAME', None))

        if self.config.debug_mode:
            nova_shell.OpenStackComputeShell().setup_debugging(True)

        nova = nova_client.Client(
                api_version, session=self._keystone_session,
                auth_url=self.auth_url,
                region_name=region_name,
                service_name=service_name,
                http_log_debug=True if self.config.debug_mode else False)
        return nova

    def _connect_keystone(self):
        """Get an OpenStack Keystone (identity) client object."""
        if self._keystone_version == 3:
            return keystone_client.Client(session=self._keystone_session,
                                          auth_url=self.auth_url)
        else:
            # Wow, the internal keystoneV2 implementation is terribly buggy. It
            # needs both a separate Session object and the username, password
            # again for things to work correctly. Plus, a manual call to
            # authenticate() is also required if the service catalog needs
            # to be queried.
            keystone = keystone_client.Client(
                session=self._keystone_session,
                auth_url=self.auth_url,
                username=self.username,
                password=self.password,
                project_name=self.project_name,
                region_name=self.region_name)
            keystone.authenticate()
            return keystone

    def _connect_cinder(self):
        """Get an OpenStack Cinder (block storage) client object."""
        api_version = self._get_config_value(
            'os_volume_api_version',
            os.environ.get('OS_VOLUME_API_VERSION', 2))

        return cinder_client.Client(api_version,
                                    auth_url=self.auth_url,
                                    session=self._keystone_session,
                                    region_name=self.region_name)

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

    @staticmethod
    def _clean_options(options, method_to_match):
        """
        Returns a **copy** of the source options with all keys that are not in
        the ``method_to_match`` parameter list removed.

        .. note:: If ``options`` has the ``os_options`` key it will have
            both the key and its value removed. This is because any entries
            in this dictionary value will override our settings. This
            situation is only going to happen when the `_connect_swift`
            method is called by the SwiftService to manufacture new
            connections.

        .. seealso::
            https://docs.openstack.org/developer/python-swiftclient/swiftclient.html#module-swiftclient.client

        :param options: The source options.
        :type options: ``dict``
        :param method_to_match: The method whose signature is to be matched
        :type method_to_match: A callable
        :return: A copy of the source options with all keys that are not in the
            ``method_to_match`` parameter list removed. If options is ``None``
            then this will be an empty dictionary
        :rtype: ``dict``
        """
        result = {}
        if options:
            try:
                method_signature = inspect.signature(method_to_match)
                parameters = set(method_signature.parameters.keys())
            except AttributeError:
                parameters = set(inspect.getargspec(method_to_match).args)
            result = {key: val for key, val in options.items() if
                      key in parameters}
            # Don't allow the options to override our authentication
            result.pop('os_options', None)
        return result

    def _connect_swift(self, options=None):
        """
        Get an OpenStack Swift (object store) client connection.

        :param options: A dictionary of options from which values will be
            passed to the connection.
        :return: A Swift client connection using the auth credentials held by
            the OpenStackCloudProvider instance
        """
        clean_options = self._clean_options(options,
                                            swift_client.Connection.__init__)
        storage_url = self._get_config_value(
            'os_storage_url', os.environ.get('OS_STORAGE_URL', None))
        auth_token = self._get_config_value(
            'os_auth_token', os.environ.get('OS_AUTH_TOKEN', None))
        if storage_url and auth_token:
            clean_options['preauthurl'] = storage_url
            clean_options['preauthtoken'] = auth_token
        else:
            clean_options['authurl'] = self.auth_url
            clean_options['session'] = self._keystone_session
        return swift_client.Connection(**clean_options)

    def _connect_neutron(self):
        """Get an OpenStack Neutron (networking) client object cloud."""
        return neutron_client.Client(auth_url=self.auth_url,
                                     session=self._keystone_session,
                                     region_name=self.region_name)
