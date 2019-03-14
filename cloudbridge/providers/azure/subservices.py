import logging

from cloudbridge.base.subservices import BaseBucketObjectSubService
from cloudbridge.base.subservices import BaseFloatingIPSubService
from cloudbridge.base.subservices import BaseGatewaySubService
from cloudbridge.base.subservices import BaseSubnetSubService
from cloudbridge.base.subservices import BaseVMFirewallRuleSubService

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

    def __init__(self, provider, gateway):
        super(AzureFloatingIPSubService, self).__init__(provider, gateway)


class AzureSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider, network):
        super(AzureSubnetSubService, self).__init__(provider, network)
