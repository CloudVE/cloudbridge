import logging
from uuid import uuid4

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import \
    BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService

from .resources import AzureFloatingIP

log = logging.getLogger(__name__)


class AzureBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(AzureBucketObjectSubService, self).__init__(provider, bucket)


class AzureGatewaySubService(BaseGatewaySubService):
    def __init__(self, provider, network):
        super(AzureGatewaySubService, self).__init__(provider, network)


class AzureVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(AzureVMFirewallRuleSubService, self).__init__(provider, firewall)


class AzureFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway, network_id):
        super(AzureFloatingIPSubService, self).__init__(provider, gateway)
        self._network_id = network_id

    def get(self, fip_id):
        log.debug("Getting Azure Floating IP container with the id: %s",
                  fip_id)
        fip = [fip for fip in self if fip.id == fip_id]
        return fip[0] if fip else None

    def list(self, limit=None, marker=None):
        floating_ips = [AzureFloatingIP(self._provider, floating_ip,
                                        self._network_id)
                        for floating_ip in self._provider.azure_client.
                        list_floating_ips()]
        return ClientPagedResultList(self._provider, floating_ips,
                                     limit=limit, marker=marker)

    def create(self):
        public_ip_parameters = {
            'location': self._provider.azure_client.region_name,
            'public_ip_allocation_method': 'Static'
        }

        public_ip_name = 'cb-fip-' + uuid4().hex[:6]

        floating_ip = self._provider.azure_client.\
            create_floating_ip(public_ip_name, public_ip_parameters)
        return AzureFloatingIP(self._provider, floating_ip, self._network_id)
