"""
Provider implementation based on google-api-python-client library
for GCP.
"""
import json
import logging
import os
import re
import time
from string import Template

import googleapiclient
from googleapiclient import discovery

from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials

from cloudbridge.base import BaseCloudProvider
from cloudbridge.interfaces.exceptions import ProviderConnectionException

from .services import GCPComputeService
from .services import GCPNetworkingService
from .services import GCPSecurityService
from .services import GCPStorageService

log = logging.getLogger(__name__)


class GCPResourceUrl(object):

    def __init__(self, resource, connection):
        self._resource = resource
        self._connection = connection
        self.parameters = {}

    def get_resource(self):
        """
        The format of the returned resource is explained in details in
        https://cloud.google.com/compute/docs/reference/latest/ and
        https://cloud.google.com/storage/docs/json_api/v1/.

        Example:
            When requesting a subnet resource, the output looks like:

            {'kind': 'compute#subnetwork',
             'id': '6662746501848591938',
             'creationTimestamp': '2017-10-13T12:53:17.445-07:00',
             'name': 'testsubnet-2',
             'network':
                     'https://www.googleapis.com/compute/v1/projects/galaxy-on-gcp/global/networks/testnet',
             'ipCidrRange': '10.128.0.0/20',
             'gatewayAddress': '10.128.0.1',
             'region':
                     'https://www.googleapis.com/compute/v1/projects/galaxy-on-gcp/regions/us-central1',
             'selfLink':
                     'https://www.googleapis.com/compute/v1/projects/galaxy-on-gcp/regions/us-central1/subnetworks/testsubnet-2',
             'privateIpGoogleAccess': false}
        """
        discovery_object = getattr(self._connection, self._resource)()
        return discovery_object.get(**self.parameters).execute()


class GCPResources(object):

    def __init__(self, connection, **kwargs):
        self._connection = connection
        self._parameter_defaults = kwargs

        # Resource descriptions are already pulled into the internal
        # _resourceDesc field of the connection.
        #
        # FIX_IF_NEEDED: We could fetch compute resource descriptions from
        # https://www.googleapis.com/discovery/v1/apis/compute/v1/rest and
        # storage resource descriptions from
        # https://www.googleapis.com/discovery/v1/apis/storage/v1/rest
        # ourselves.
        #
        # Resource descriptions are in JSON format which are then parsed into a
        # Python dictionary. The main fields we are interested are:
        #
        # {
        #   "rootUrl": "https://www.googleapis.com/",
        #   "servicePath": COMPUTE OR STORAGE SERVICE PATH
        #   "resources": {
        #     RESOURCE_NAME: {
        #       "methods": {
        #         "get": {
        #           "path": RESOURCE PATH PATTERN
        #           "parameters": {
        #             PARAMETER: {
        #               "pattern": REGEXP FOR VALID VALUES
        #               ...
        #             },
        #             ...
        #           },
        #           "parameterOrder": [LIST OF PARAMETERS]
        #         },
        #         ...
        #       }
        #     },
        #     ...
        #   }
        #   ...
        # }
        # pylint:disable=protected-access
        desc = connection._resourceDesc
        self._root_url = desc['rootUrl']
        self._service_path = desc['servicePath']
        self._resources = {}

        # We will not mutate self._desc; it's OK to use items() in Python 2.x.
        for resource, resource_desc in desc['resources'].items():
            methods = resource_desc.get('methods', {})
            if not methods.get('get'):
                continue
            method = methods['get']
            parameters = method['parameterOrder']

            # We would like to change a path like
            # {project}/regions/{region}/addresses/{address} to a pattern like
            # (PROJECT REGEX)/regions/(REGION REGEX)/addresses/(ADDRESS REGEX).
            template = Template('${'.join(method['path'].split('{')))
            mapping = {}
            for parameter in parameters:
                parameter_desc = method['parameters'][parameter]
                if 'pattern' in parameter_desc:
                    mapping[parameter] = '(%s)' % parameter_desc['pattern']
                else:
                    mapping[parameter] = '([^/]+)'
            pattern = template.substitute(**mapping)

            # Store the parameters and the regex pattern of this resource.
            self._resources[resource] = {'parameters': parameters,
                                         'pattern': re.compile(pattern)}

    def parse_url(self, url):
        """
        Build a GCPResourceUrl from a resource's URL string. One can then call
        the get() method on the returned object to fetch resource details from
        GCP servers.

        Example:
            If the input url is the following

            https://www.googleapis.com/compute/v1/projects/galaxy-on-gcp/regions/us-central1/subnetworks/testsubnet-2

            then parse_url will return a GCPResourceURL and the parameters
            field of the returned object will look like:

            {'project': 'galaxy-on-gcp',
             'region': 'us-central1',
             'subnetwork': 'testsubnet-2'}
        """
        url = url.strip()
        if url.startswith(self._root_url):
            url = url[len(self._root_url):]
        if url.startswith(self._service_path):
            url = url[len(self._service_path):]

        for resource, desc in self._resources.items():
            m = re.match(desc['pattern'], url)
            if m is None or len(m.group(0)) < len(url):
                continue
            out = GCPResourceUrl(resource, self._connection)
            for index, parameter in enumerate(desc['parameters']):
                out.parameters[parameter] = m.group(index + 1)
            return out

    def get_resource_url_with_default(self, resource, url_or_name, **kwargs):
        """
        Build a GCPResourceUrl from a service's name and resource url or name.
        If the url_or_name is a valid GCP resource URL, then we build the
        GCPResourceUrl object by parsing this URL. If the url_or_name is its
        short name, then we build the GCPResourceUrl object by constructing
        the resource URL with default project, region, zone values.
        """
        # If url_or_name is a valid GCP resource URL, then parse it.
        if url_or_name.startswith(self._root_url):
            return self.parse_url(url_or_name)
        # Otherwise, construct resource URL with default values.
        if resource not in self._resources:
            log.warning('Unknown resource: %s', resource)
            return None

        parameter_defaults = self._parameter_defaults.copy()
        parameter_defaults.update(kwargs)

        parsed_url = GCPResourceUrl(resource, self._connection)
        for key in self._resources[resource]['parameters']:
            parsed_url.parameters[key] = parameter_defaults.get(
                key, url_or_name)
        return parsed_url


class GCPCloudProvider(BaseCloudProvider):

    PROVIDER_ID = 'gcp'

    def __init__(self, config):
        super(GCPCloudProvider, self).__init__(config)

        # Disable warnings about file_cache not being available when using
        # oauth2client >= 4.0.0.
        logging.getLogger('googleapiclient.discovery_cache').setLevel(
                logging.ERROR)

        # Initialize cloud connection fields
        self.credentials_file = self._get_config_value(
                'gcp_service_creds_file',
                os.getenv('GCP_SERVICE_CREDS_FILE'))
        self.credentials_dict = self._get_config_value(
                'gcp_service_creds_dict',
                json.loads(os.getenv('GCP_SERVICE_CREDS_DICT', '{}')))
        self.credentials_obj = self._get_config_value('gcp_credentials_obj')
        self.vm_default_user_name = self._get_config_value(
            'gcp_vm_default_username',
            os.getenv('GCP_VM_DEFAULT_USERNAME', "cbuser"))

        # If 'gcp_service_creds_dict' is not passed in from config and
        # self.credentials_file is available, read and parse the json file to
        # self.credentials_dict.
        if self.credentials_file and not self.credentials_dict:
            with open(self.credentials_file) as creds_file:
                self.credentials_dict = json.load(creds_file)
        self._region_name = self._get_config_value(
            'gcp_region_name',
            os.environ.get('GCP_DEFAULT_REGION') or 'us-central1')
        self._zone_name = self._get_config_value(
            'gcp_zone_name', os.environ.get('GCP_ZONE_NAME'))

        if self.credentials_dict and 'project_id' in self.credentials_dict:
            self.project_name = self.credentials_dict['project_id']
        else:
            self.project_name = os.environ.get('GCP_PROJECT_NAME')

        # service connections, lazily initialized
        self._gcp_compute = None
        self._gcp_storage = None
        self._compute_resources_cache = None
        self._storage_resources_cache = None

        # Initialize provider services
        self._compute = GCPComputeService(self)
        self._security = GCPSecurityService(self)
        self._networking = GCPNetworkingService(self)
        self._storage = GCPStorageService(self)

    # Override base class implementation because it will cause
    # an infinite loop
    @property
    def zone_name(self):
        return self._zone_name

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
    def gcp_compute(self):
        if not self._gcp_compute:
            self._gcp_compute = self._connect_gcp_compute()
        return self._gcp_compute

    @property
    def gcp_storage(self):
        if not self._gcp_storage:
            self._gcp_storage = self._connect_gcp_storage()
        return self._gcp_storage

    @property
    def _compute_resources(self):
        if not self._compute_resources_cache:
            self._compute_resources_cache = GCPResources(
                    self.gcp_compute,
                    project=self.project_name,
                    region=self.region_name,
                    zone=self.zone_name)
        return self._compute_resources_cache

    @property
    def _storage_resources(self):
        if not self._storage_resources_cache:
            self._storage_resources_cache = GCPResources(self.gcp_storage)
        return self._storage_resources_cache

    @property
    def _credentials(self):
        if not self.credentials_obj:
            if self.credentials_dict:
                self.credentials_obj = (
                        ServiceAccountCredentials.from_json_keyfile_dict(
                                self.credentials_dict))
            else:
                self.credentials_obj = (
                        GoogleCredentials.get_application_default())
        return self.credentials_obj

    def sign_blob(self, string_to_sign):
        return self._credentials.sign_blob(string_to_sign)[1]

    @property
    def client_id(self):
        return self._credentials.service_account_email

    def _connect_gcp_storage(self):
        return discovery.build('storage', 'v1', credentials=self._credentials,
                               cache_discovery=False)

    def _connect_gcp_compute(self):
        return discovery.build('compute', 'v1', credentials=self._credentials,
                               cache_discovery=False)

    def wait_for_operation(self, operation, region=None, zone=None):
        args = {'project': self.project_name, 'operation': operation['name']}
        if not region and not zone:
            operations = self.gcp_compute.globalOperations()
        elif zone:
            operations = self.gcp_compute.zoneOperations()
            args['zone'] = zone
        else:
            operations = self.gcp_compute.regionOperations()
            args['region'] = region

        while True:
            result = operations.get(**args).execute()
            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(0.5)

    def parse_url(self, url):
        out = self._compute_resources.parse_url(url)
        return out if out else self._storage_resources.parse_url(url)

    def get_resource(self, resource, url_or_name, **kwargs):
        if not url_or_name:
            return None
        resource_url = (
            self._compute_resources.get_resource_url_with_default(
                resource, url_or_name, **kwargs) or
            self._storage_resources.get_resource_url_with_default(
                resource, url_or_name, **kwargs))
        if resource_url is None:
            return None
        try:
            return resource_url.get_resource()
        except googleapiclient.errors.HttpError as http_error:
            if http_error.resp.status in [404]:
                # 404 = not found
                return None
            else:
                raise

    def authenticate(self):
        try:
            self.gcp_compute
            return True
        except Exception as e:
            raise ProviderConnectionException(
                'Authentication with Google cloud provider failed: %s', e)
