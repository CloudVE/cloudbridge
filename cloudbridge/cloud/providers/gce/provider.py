"""
Provider implementation based on google-api-python-client library
for GCE.
"""


from cloudbridge.cloud.base import BaseCloudProvider
import json
import os
import time

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials

from .services import GCEComputeService
from .services import GCESecurityService


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

        # Initialize provider services
        self._compute = GCEComputeService(self)
        self._security = GCESecurityService(self)

    @property
    def compute(self):
        return self._compute

    @property
    def network(self):
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def security(self):
        return self._security

    @property
    def block_store(self):
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def object_store(self):
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def gce_compute(self):
        if not self._gce_compute:
            self._gce_compute = self._connect_gce_compute()
        return self._gce_compute

    def _connect_gce_compute(self):
        if self.credentials_dict:
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                self.credentials_dict)
        else:
            credentials = GoogleCredentials.get_application_default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def wait_for_global_operation(self, operation):
        while True:
            result = self.gce_compute.globalOperations().get(
                project=self.project_name,
                operation=operation['name']).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(0.5)
