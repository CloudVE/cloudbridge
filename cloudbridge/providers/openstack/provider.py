"""Provider implementation based on OpenStack Python clients for OpenStack."""

import inspect

from keystoneauth1 import session

from keystoneclient import client as keystone_client

from neutronclient.v2_0 import client as neutron_client

from novaclient import client as nova_client
from novaclient import shell as nova_shell

from openstack import connection

from swiftclient import client as swift_client

from cloudbridge.base import BaseCloudProvider
from cloudbridge.base.helpers import get_env

from cloudbridge.interfaces.exceptions import ProviderConnectionException

from .services import OpenStackComputeService
from .services import OpenStackDnsService
from .services import OpenStackNetworkingService
from .services import OpenStackSecurityService
from .services import OpenStackStorageService


class OpenStackCloudProvider(BaseCloudProvider):
    """OpenStack provider implementation."""

    PROVIDER_ID = 'openstack'

    def __init__(self, config):
        super(OpenStackCloudProvider, self).__init__(config)

        # Initialize cloud connection fields
        self.app_cred_id = self._get_config_value(
            'os_application_credential_id', get_env('OS_APPLICATION_CREDENTIAL_ID'))
        self.app_cred_secret = self._get_config_value(
            'os_application_credential_secret', get_env('OS_APPLICATION_CREDENTIAL_SECRET'))
        self.username = self._get_config_value(
            'os_username', get_env('OS_USERNAME'))
        self.password = self._get_config_value(
            'os_password', get_env('OS_PASSWORD'))
        self.project_name = self._get_config_value(
            'os_project_name', get_env('OS_PROJECT_NAME')
            or get_env('OS_TENANT_NAME'))
        self.auth_url = self._get_config_value(
            'os_auth_url', get_env('OS_AUTH_URL'))
        self._region_name = self._get_config_value(
            'os_region_name', get_env('OS_REGION_NAME'))
        self._zone_name = self._get_config_value(
            'os_zone_name', get_env('OS_ZONE_NAME'))
        self.project_domain_id = self._get_config_value(
            'os_project_domain_id',
            get_env('OS_PROJECT_DOMAIN_ID'))
        self.project_domain_name = self._get_config_value(
            'os_project_domain_name',
            get_env('OS_PROJECT_DOMAIN_NAME'))
        self.user_domain_name = self._get_config_value(
            'os_user_domain_name',
            get_env('OS_USER_DOMAIN_NAME'))

        # Service connections, lazily initialized
        self._nova = None
        self._keystone = None
        self._swift = None
        self._neutron = None
        self._os_conn = None

        # Additional cached variables
        self._cached_keystone_session = None

        # Initialize provider services
        self._compute = OpenStackComputeService(self)
        self._networking = OpenStackNetworkingService(self)
        self._security = OpenStackSecurityService(self)
        self._storage = OpenStackStorageService(self)
        self._dns = OpenStackDnsService(self)

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
            from keystoneauth1.identity import v3
            if self.username and self.password:
                auth = v3.Password(auth_url=self.auth_url,
                                   username=self.username,
                                   password=self.password,
                                   user_domain_name=self.user_domain_name,
                                   project_domain_id=self.project_domain_id,
                                   project_domain_name=self.project_domain_name,
                                   project_name=self.project_name)
            elif self.app_cred_id and self.app_cred_secret:
                auth = v3.ApplicationCredential(auth_url=self.auth_url,
                                                application_credential_id=self.app_cred_id,
                                                application_credential_secret=self.app_cred_secret)
            else:
                raise ProviderConnectionException("""No valid credentials were found. You must supply either
                                                     'os_username' and 'os_password', or 'os_application_credential_id'
                                                     and 'os_application_credential_secret'""")
            self._cached_keystone_session = session.Session(auth=auth)
        else:
            from keystoneauth1.identity import v2
            auth = v2.Password(self.auth_url, username=self.username,
                               password=self.password,
                               tenant_name=self.project_name)
            self._cached_keystone_session = session.Session(auth=auth)
        return self._cached_keystone_session

    def _connect_openstack(self):
        return connection.Connection(
            region_name=self.region_name,
            user_agent='cloudbridge',
            auth_url=self.auth_url,
            session=self._keystone_session,
        )

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
    def os_conn(self):
        if not self._os_conn:
            self._os_conn = self._connect_openstack()
        return self._os_conn

    @property
    def compute(self):
        return self._compute

    @property
    def networking(self):
        return self._networking

    @property
    def security(self):
        return self._security

    @property
    def storage(self):
        return self._storage

    @property
    def dns(self):
        return self._dns

    def _connect_nova(self):
        return self._connect_nova_region(self.region_name)

    def _connect_nova_region(self, region_name):
        """Get an OpenStack Nova (compute) client object."""
        # Force reauthentication with Keystone
        self._cached_keystone_session = None

        api_version = self._get_config_value(
            'os_compute_api_version',
            get_env('OS_COMPUTE_API_VERSION', 2))
        service_name = self._get_config_value(
            'nova_service_name',
            get_env('NOVA_SERVICE_NAME', None))

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
        clean_options = self._clean_options(
            options, swift_client.Connection.__init__)
        storage_url = self._get_config_value(
            'os_storage_url', get_env('OS_STORAGE_URL', None))
        auth_token = self._get_config_value(
            'os_auth_token', get_env('OS_AUTH_TOKEN', None))
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

    def service_zone_name(self, service):
        service_name = service._service_event_pattern
        if "networking" in service_name:
            if self.networking.service_zone_name:
                return self.networking.service_zone_name
            elif (isinstance(self.zone_name, dict) and
                  self.zone_name.get("networking_zone")):
                return self.zone_name.get("networking_zone")
        elif "security" in service_name:
            if self.security.service_zone_name:
                return self.security.service_zone_name
            elif (isinstance(self.zone_name, dict) and
                  self.zone_name.get("security_zone")):
                return self.zone_name.get("security_zone")
        elif "compute" in service_name:
            if self.compute.service_zone_name:
                return self.compute.service_zone_name
            elif (isinstance(self.zone_name, dict) and
                  self.zone_name.get("compute_zone")):
                return self.zone_name.get("compute_zone")
        elif "storage" in service_name:
            if self.storage.service_zone_name:
                return self.storage.service_zone_name
            elif (isinstance(self.zone_name, dict) and
                  self.zone_name.get("storage_zone")):
                return self.zone_name.get("storage_zone")
        elif (isinstance(self.zone_name, dict) and
              self.zone_name.get("default_zone")):
            return self.zone_name.get("default_zone")
        elif isinstance(self.zone_name, str):
            return self.zone_name
        else:
            return None
