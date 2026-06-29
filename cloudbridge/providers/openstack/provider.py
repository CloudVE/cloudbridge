"""Provider implementation based on OpenStack Python clients for OpenStack."""
from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from keystoneauth1 import session

from keystoneclient import client as keystone_client

from neutronclient.v2_0 import client as neutron_client

from novaclient import client as nova_client
from novaclient import shell as nova_shell

from openstack import connection

from swiftclient import client as swift_client

from cloudbridge.base import BaseCloudProvider
from cloudbridge.base.helpers import get_env
from cloudbridge.base.services import BaseCloudService
from cloudbridge.interfaces.exceptions import ProviderConnectionException
from cloudbridge.interfaces.services import ComputeService
from cloudbridge.interfaces.services import DnsService
from cloudbridge.interfaces.services import NetworkingService
from cloudbridge.interfaces.services import SecurityService
from cloudbridge.interfaces.services import StorageService

from .services import OpenStackComputeService
from .services import OpenStackDnsService
from .services import OpenStackNetworkingService
from .services import OpenStackSecurityService
from .services import OpenStackStorageService


class OpenStackCloudProvider(BaseCloudProvider):
    """OpenStack provider implementation."""

    PROVIDER_ID: str = 'openstack'

    def __init__(self, config: dict[str, Any]) -> None:
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
        self._nova: Any = None
        self._keystone: Any = None
        self._swift: Any = None
        self._neutron: Any = None
        self._os_conn: Any = None

        # Additional cached variables
        self._cached_keystone_session: Any = None

        # Initialize provider services
        self._compute = OpenStackComputeService(self)
        self._networking = OpenStackNetworkingService(self)
        self._security = OpenStackSecurityService(self)
        self._storage = OpenStackStorageService(self)
        self._dns = OpenStackDnsService(self)

    @property
    def nova(self) -> Any:
        if not self._nova:
            self._nova = self._connect_nova()
        return self._nova

    @property
    def keystone(self) -> Any:
        if not self._keystone:
            self._keystone = self._connect_keystone()
        return self._keystone

    @property
    def _keystone_version(self) -> int:
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
    def _keystone_session(self) -> Any:
        """
        Connect to Keystone and return a session object.

        :rtype: :class:`keystoneauth1.session.Session`
        :return: A Keystone session object.
        """
        if self._cached_keystone_session:
            return self._cached_keystone_session

        if self._keystone_version == 3:
            from keystoneauth1.identity import v3
            auth: Any
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

    def _connect_openstack(self) -> Any:
        return connection.Connection(
            region_name=self.region_name,
            user_agent='cloudbridge',
            auth_url=self.auth_url,
            session=self._keystone_session,
        )

    @property
    def swift(self) -> Any:
        if not self._swift:
            self._swift = self._connect_swift()
        return self._swift

    @property
    def neutron(self) -> Any:
        if not self._neutron:
            self._neutron = self._connect_neutron()
        return self._neutron

    @property
    def os_conn(self) -> Any:
        if not self._os_conn:
            self._os_conn = self._connect_openstack()
        return self._os_conn

    @property
    def compute(self) -> ComputeService:
        return self._compute

    @property
    def networking(self) -> NetworkingService:
        return self._networking

    @property
    def security(self) -> SecurityService:
        return self._security

    @property
    def storage(self) -> StorageService:
        return self._storage

    @property
    def dns(self) -> DnsService:
        return self._dns

    def _connect_nova(self) -> Any:
        return self._connect_nova_region(self.region_name)

    def _connect_nova_region(self, region_name: str | None) -> Any:
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

    def _connect_keystone(self) -> Any:
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
    def _clean_options(options: dict[str, Any] | None,
                       method_to_match: Callable[..., Any]) -> dict[str, Any]:
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
        result: dict[str, Any] = {}
        if options:
            method_signature = inspect.signature(method_to_match)
            parameters = set(method_signature.parameters.keys())
            result = {key: val for key, val in options.items() if
                      key in parameters}
            # Don't allow the options to override our authentication
            result.pop('os_options', None)
        return result

    def _connect_swift(self, options: dict[str, Any] | None = None) -> Any:
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

    def _connect_neutron(self) -> Any:
        """Get an OpenStack Neutron (networking) client object cloud."""
        return neutron_client.Client(auth_url=self.auth_url,
                                     session=self._keystone_session,
                                     region_name=self.region_name)

    def service_zone_name(self, service: BaseCloudService) -> str | None:
        # ``service_zone_name`` is an OpenStack-specific attribute set in each
        # service's __init__; it is not declared on the typed service
        # interfaces, so reach it through ``Any``.
        networking: Any = self.networking
        security: Any = self.security
        compute: Any = self.compute
        storage: Any = self.storage
        # ``zone_name`` is typed ``str | None`` on the interface, but the base
        # implementation may return a dict at runtime (via ast.literal_eval);
        # bind it to ``Any`` so the dict branches type-check.
        zone_name: Any = self.zone_name
        service_name = service._service_event_pattern
        if "networking" in service_name:
            if networking.service_zone_name:
                return networking.service_zone_name
            elif (isinstance(zone_name, dict) and
                  zone_name.get("networking_zone")):
                return zone_name.get("networking_zone")
        elif "security" in service_name:
            if security.service_zone_name:
                return security.service_zone_name
            elif (isinstance(zone_name, dict) and
                  zone_name.get("security_zone")):
                return zone_name.get("security_zone")
        elif "compute" in service_name:
            if compute.service_zone_name:
                return compute.service_zone_name
            elif (isinstance(zone_name, dict) and
                  zone_name.get("compute_zone")):
                return zone_name.get("compute_zone")
        elif "storage" in service_name:
            if storage.service_zone_name:
                return storage.service_zone_name
            elif (isinstance(zone_name, dict) and
                  zone_name.get("storage_zone")):
                return zone_name.get("storage_zone")
        elif (isinstance(zone_name, dict) and
              zone_name.get("default_zone")):
            return zone_name.get("default_zone")
        elif isinstance(zone_name, str):
            return zone_name
        else:
            return None
        # The branches above only return when an inner condition matched;
        # fall through to ``None`` otherwise (preserving the original
        # implicit return).
        return None
