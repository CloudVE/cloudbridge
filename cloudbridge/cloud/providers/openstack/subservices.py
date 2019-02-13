import logging

from openstack.exceptions import HttpException
from openstack.exceptions import NotFoundException
from openstack.exceptions import ResourceNotFound

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import BaseGatewaySubService
from cloudbridge.cloud.base.subservices import \
    BaseVMFirewallRuleSubService
from cloudbridge.cloud.interfaces.exceptions import InvalidValueException
from cloudbridge.cloud.interfaces.resources import TrafficDirection

from .resources import OpenStackFloatingIP
from .resources import OpenStackVMFirewall
from .resources import OpenStackVMFirewallRule

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

    def list(self, limit=None, marker=None):
        # pylint:disable=protected-access
        rules = [OpenStackVMFirewallRule(self.firewall, r)
                 for r in self.firewall._vm_firewall.security_group_rules]
        return ClientPagedResultList(self._provider, rules,
                                     limit=limit, marker=marker)

    def create(self,  direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        src_dest_fw_id = (src_dest_fw.id if isinstance(src_dest_fw,
                                                       OpenStackVMFirewall)
                          else src_dest_fw)

        try:
            if direction == TrafficDirection.INBOUND:
                os_direction = 'ingress'
            elif direction == TrafficDirection.OUTBOUND:
                os_direction = 'egress'
            else:
                raise InvalidValueException("direction", direction)
            # pylint:disable=protected-access
            rule = self._provider.os_conn.network.create_security_group_rule(
                security_group_id=self.firewall.id,
                direction=os_direction,
                port_range_max=to_port,
                port_range_min=from_port,
                protocol=protocol,
                remote_ip_prefix=cidr,
                remote_group_id=src_dest_fw_id)
            self.firewall.refresh()
            return OpenStackVMFirewallRule(self.firewall, rule.to_dict())
        except HttpException as e:
            self.firewall.refresh()
            # 409=Conflict, raised for duplicate rule
            if e.status_code == 409:
                existing = self.find(direction=direction, protocol=protocol,
                                     from_port=from_port, to_port=to_port,
                                     cidr=cidr, src_dest_fw_id=src_dest_fw_id)
                return existing[0]
            else:
                raise e
