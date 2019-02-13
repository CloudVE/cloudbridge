import logging

from openstack.exceptions import NotFoundException
from openstack.exceptions import ResourceNotFound

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import BaseGatewaySubService
from cloudbridge.cloud.base.subservices import \
    BaseVMFirewallRuleSubService

from .resources import OpenStackFloatingIP

log = logging.getLogger(__name__)


class OpenStackBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(OpenStackBucketObjectSubService, self).__init__(provider, bucket)


class OpenStackGatewaySubService(BaseGatewaySubService):

    def __init__(self, provider, network):
        super(OpenStackGatewaySubService, self).__init__(provider, network)


class OpenStackFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(OpenStackFloatingIPSubService, self).__init__(provider, gateway)

    def get(self, fip_id):
        try:
            return OpenStackFloatingIP(
                self._provider, self._provider.os_conn.network.get_ip(fip_id))
        except (ResourceNotFound, NotFoundException):
            log.debug("Floating IP %s not found.", fip_id)
            return None

    def list(self, limit=None, marker=None):
        fips = [OpenStackFloatingIP(self._provider, fip)
                for fip in self._provider.os_conn.network.ips(
                    floating_network_id=self.gateway.id
                )]
        return ClientPagedResultList(self._provider, fips,
                                     limit=limit, marker=marker)

    def create(self):
        return OpenStackFloatingIP(
            self._provider, self._provider.os_conn.network.create_ip(
                floating_network_id=self.gateway.id))


class OpenStackVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(OpenStackVMFirewallRuleSubService, self).__init__(
            provider, firewall)
