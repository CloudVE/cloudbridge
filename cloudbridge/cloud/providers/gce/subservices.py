import logging
import uuid

from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import \
    BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService

from .resources import GCEFloatingIP

log = logging.getLogger(__name__)


class GCSBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(GCSBucketObjectSubService, self).__init__(provider, bucket)


class GCEGatewaySubService(BaseGatewaySubService):
    def __init__(self, provider, network):
        super(GCEGatewaySubService, self).__init__(provider, network)


class GCEVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(GCEVMFirewallRuleSubService, self).__init__(provider)


class GCEFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(GCEFloatingIPSubService, self).__init__(provider, gateway)

    def get(self, floating_ip_id):
        fip = self._provider.get_resource('addresses', floating_ip_id)
        return (GCEFloatingIP(self._provider, self.gateway, fip)
                if fip else None)

    def list(self, limit=None, marker=None):
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self._provider
                        .gce_compute
                        .addresses()
                        .list(project=self._provider.project_name,
                              region=self._provider.region_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        ips = [GCEFloatingIP(self._provider, self.gateway, ip)
               for ip in response.get('items', [])]
        if len(ips) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(ips))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=ips)

    def create(self):
        region_name = self._provider.region_name
        ip_name = 'ip-{0}'.format(uuid.uuid4())
        response = (self._provider
                    .gce_compute
                    .addresses()
                    .insert(project=self._provider.project_name,
                            region=region_name,
                            body={'name': ip_name})
                    .execute())
        self._provider.wait_for_operation(response, region=region_name)
        return self.get(ip_name)
