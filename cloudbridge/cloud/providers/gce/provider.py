"""
Provider implementation based on google-api-python-client library
for GCE.
"""


from cloudbridge.cloud.base import BaseCloudProvider
import httplib2
import json
import os
import re
from string import Template
import time

from googleapiclient import discovery
import googleapiclient.http
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials

from .services import GCEBlockStoreService
from .services import GCEComputeService
from .services import GCENetworkService
from .services import GCESecurityService


class GCPResourceUrl(object):

    def __init__(self, resource, connection):
        self._resource = resource
        self._connection = connection
        self.parameters = {}

    def get(self):
        discovery_object = getattr(self._connection, self._resource)()
        return discovery_object.get(**self.parameters).execute()


class GCPResources(object):

    def __init__(self, connection):
        self._connection = connection

        # Resource descriptions are already pulled into the internal
        # _resourceDesc field of the connection.
        #
        # TODO: We could fetch compute resource descriptions from
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
        desc = connection._resourceDesc
        self._root_url = desc['rootUrl']
        self._service_path = desc['servicePath']
        self._resources = {}

        # We will not mutate self._desc; it's OK to use items() in Python 2.x.
        for resource, resource_desc in desc['resources'].items():
            if 'methods' not in resource_desc:
                continue
            methods = resource_desc['methods']
            if 'get' not in methods:
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
        """
        url = url.strip()
        if url.startswith(self._root_url): url = url[len(self._root_url):]
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


class GCECloudProvider(BaseCloudProvider):

    PROVIDER_ID = 'gce'

    def __init__(self, config):
        super(GCECloudProvider, self).__init__(config)

        # Initialize cloud connection fields
        self.client_email = self._get_config_value(
            'gce_client_email', os.environ.get('GCE_CLIENT_EMAIL'))
        self.project_name = self._get_config_value(
            'gce_project_name', os.environ.get('GCE_PROJECT_NAME'))
        self.credentials_file = self._get_config_value(
            'gce_service_creds_file', os.environ.get('GCE_SERVICE_CREDS_FILE'))
        self.credentials_dict = self._get_config_value(
            'gce_service_creds_dict', {})
        # If 'gce_service_creds_dict' is not passed in from config and
        # self.credentials_file is available, read and parse the json file to
        # self.credentials_dict.
        if self.credentials_file and not self.credentials_dict:
            with open(self.credentials_file) as creds_file:
                self.credentials_dict = json.load(creds_file)
        self.default_zone = self._get_config_value(
            'gce_default_zone', os.environ.get('GCE_DEFAULT_ZONE'))
        self.region_name = self._get_config_value(
            'gce_region_name', 'us-central1')

        # service connections, lazily initialized
        self._gce_compute = None
        self._gcp_storage = None

        # Initialize provider services
        self._compute = GCEComputeService(self)
        self._security = GCESecurityService(self)
        self._network = GCENetworkService(self)
        self._block_store = GCEBlockStoreService(self)

        self._compute_resources = GCPResources(self.gce_compute)
        self._storage_resources = GCPResources(self.gcp_storage)

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
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def gce_compute(self):
        if not self._gce_compute:
            self._gce_compute = self._connect_gce_compute()
        return self._gce_compute

    @property
    def gcp_storage(self):
        if not self._gcp_storage:
            self._gcp_storage = self._connect_gcp_storage()
        return self._gcp_storage

    @property
    def _credentials(self):
        if self.credentials_dict:
            return ServiceAccountCredentials.from_json_keyfile_dict(
                self.credentials_dict)
        else:
            return GoogleCredentials.get_application_default()

    def get_gce_resource_data(self, uri):
        """
        Retrieves GCE resoure data given its resource URI.
        """
        http = httplib2.Http()
        http = self._credentials.authorize(http)
        def _postproc(*kwargs):
            if len(kwargs) >= 2:
                # The first argument is request, and the second is response.
                resource_dict = json.loads(kwargs[1])
                return resource_dict
        request = googleapiclient.http.HttpRequest(http=http,
                                                   postproc=_postproc,
                                                   uri=uri)
        # The response is a dict representing the GCE resource data.
        response = request.execute()
        return response

    def wait_for_global_operation(self, operation):
        while True:
            result = self.gce_compute.globalOperations().get(
                project=self.project_name,
                operation=operation['name']).execute()

    def _connect_gcp_storage(self):
        return discovery.build('storage', 'v1', credentials=self._credentials)

    def _connect_gce_compute(self):
        return discovery.build('compute', 'v1', credentials=self._credentials)

    def wait_for_operation(self, operation, region=None, zone=None):
        args = {'project': self.project_name, 'operation': operation['name']}
        if not region and not zone:
            operations = self.gce_compute.globalOperations()
        elif zone:
            operations = self.gce_compute.zoneOperations()
            args['zone'] = zone
        else:
            operations = self.gce_compute.regionOperations()
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
