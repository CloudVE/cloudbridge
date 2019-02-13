import logging

from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import \
    BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService

from .helpers import BotoEC2Service
from .resources import AWSFloatingIP

log = logging.getLogger(__name__)


class AWSBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(AWSBucketObjectSubService, self).__init__(provider, bucket)


class AWSGatewaySubService(BaseGatewaySubService):

    def __init__(self, provider, network):
        super(AWSGatewaySubService, self).__init__(provider, network)


class AWSVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(AWSVMFirewallRuleSubService, self).__init__(provider, firewall)


class AWSFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(AWSFloatingIPSubService, self).__init__(provider, gateway)
        self.svc = BotoEC2Service(provider=self._provider,
                                  cb_resource=AWSFloatingIP,
                                  boto_collection_name='vpc_addresses')

    def get(self, fip_id):
        log.debug("Getting AWS Floating IP Service with the id: %s", fip_id)
        return self.svc.get(fip_id)

    def list(self, limit=None, marker=None):
        log.debug("Listing all floating IPs under gateway %s", self.gateway)
        return self.svc.list(limit=limit, marker=marker)

    def create(self):
        log.debug("Creating a floating IP under gateway %s", self.gateway)
        ip = self._provider.ec2_conn.meta.client.allocate_address(
            Domain='vpc')
        return AWSFloatingIP(
            self._provider,
            self._provider.ec2_conn.VpcAddress(ip.get('AllocationId')))
