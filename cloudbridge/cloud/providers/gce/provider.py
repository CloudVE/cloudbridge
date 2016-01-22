"""
Provider implementation based on google-api-python-client library
for GCE.
"""

from cloudbridge.cloud.base import BaseCloudProvider
from .services import GCESecurityService


class GCECloudProvider(BaseCloudProvider):

    PROVIDER_ID = 'gce'

    def __init__(self, config):
        super(GCECloudProvider, self).__init__(config)
        self._security = GCESecurityService(self)

    @property
    def compute(self):
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

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
