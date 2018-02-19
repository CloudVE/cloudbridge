"""
Provider implementation based on google-api-python-client library
for GCE.
"""
import copy
import json
import logging
import os
import re
import time
from string import Template

import cloudbridge as cb
from cloudbridge.cloud.base import BaseCloudProvider

import googleapiclient
from googleapiclient import discovery

from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials

from .services import GCEComputeService
from .services import GCENetworkingService
from .services import GCESecurityService
from .services import GCPStorageService


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
            When requesting a subnetwork resource the output looks like:

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

    def __init__(self, connection, project_name, region_name, default_zone):
        self._connection = connection
        self._parameter_defaults = {
            'project': project_name,
            'region': region_name,
            'zone': default_zone,
        }

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

    def get_resource_url_with_default(self, resource, url_or_name,
                                      project=None, region=None, zone=None):
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
            return None

        parameter_defaults = copy.copy(self._parameter_defaults)
        if region:
            parameter_defaults['region'] = region
        if zone:
            parameter_defaults['zone'] = zone
        parsed_url = GCPResourceUrl(resource, self._connection)
        for key in self._resources[resource]['parameters']:
            parsed_url.parameters[key] = parameter_defaults.get(
                key, url_or_name)
        return parsed_url


class GCECloudProvider(BaseCloudProvider):

    PROVIDER_ID = 'gce'

    def __init__(self, config):
        super(GCECloudProvider, self).__init__(config)

        # Disable warnings about file_cache not being available when using
        # oauth2client >= 4.0.0.
        logging.getLogger('googleapicliet.discovery_cache').setLevel(
                logging.ERROR)

        # Initialize cloud connection fields
        self.credentials_file = self._get_config_value(
                'gce_service_creds_file',
                os.environ.get('GCE_SERVICE_CREDS_FILE'))
        self.credentials_dict = self._get_config_value(
                'gce_service_creds_dict',
                json.loads(os.getenv('GCE_SERVICE_CREDS_DICT', '{}')))
        # If 'gce_service_creds_dict' is not passed in from config and
        # self.credentials_file is available, read and parse the json file to
        # self.credentials_dict.
        if self.credentials_file and not self.credentials_dict:
            with open(self.credentials_file) as creds_file:
                self.credentials_dict = json.load(creds_file)
        self.default_zone = self._get_config_value(
            'gce_default_zone',
            os.environ.get('GCE_DEFAULT_ZONE') or 'us-central1-a')
        self.region_name = self._get_config_value(
            'gce_region_name',
            os.environ.get('GCE_DEFAULT_REGION') or 'us-central1')

        if self.credentials_dict and 'project_id' in self.credentials_dict:
            self.project_name = self.credentials_dict['project_id']
        else:
            self.project_name = os.environ.get('GCE_PROJECT_NAME')

        # service connections, lazily initialized
        self._gce_compute = None
        self._gcs_storage = None

        # Initialize provider services
        self._compute = GCEComputeService(self)
        self._security = GCESecurityService(self)
        self._networking = GCENetworkingService(self)
        self._storage = GCPStorageService(self)

        self._compute_resources = GCPResources(
            self.gce_compute, self.project_name, self.region_name,
            self.default_zone)
        self._storage_resources = GCPResources(
            self.gcs_storage, self.project_name, self.region_name,
            self.default_zone)

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
    def gce_compute(self):
        if not self._gce_compute:
            self._gce_compute = self._connect_gce_compute()
        return self._gce_compute

    @property
    def gcs_storage(self):
        if not self._gcs_storage:
            self._gcs_storage = self._connect_gcs_storage()
        return self._gcs_storage

    @property
    def _credentials(self):
        if self.credentials_dict:
            return ServiceAccountCredentials.from_json_keyfile_dict(
                self.credentials_dict)
        else:
            return GoogleCredentials.get_application_default()

    def _connect_gcs_storage(self):
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

    def get_resource(self, resource, url_or_name, project=None, region=None,
                     zone=None):
        resource_url = (
            self._compute_resources.get_resource_url_with_default(
                resource, url_or_name, project, region, zone) or
            self._storage_resources.get_resource_url_with_default(
                resource, url_or_name, project, region, zone))
        if resource_url is None:
            return None
        try:
            return resource_url.get_resource()
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
            return None
