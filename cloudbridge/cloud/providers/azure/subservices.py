import logging
from uuid import uuid4

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import \
    BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService
from cloudbridge.cloud.interfaces.resources import TrafficDirection

from .resources import AzureFloatingIP
from .resources import AzureVMFirewallRule

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

    def list(self, limit=None, marker=None):
        # Filter out firewall rules with priority < 3500 because values
        # between 3500 and 4096 are assumed to be owned by cloudbridge
        # default rules.
        # pylint:disable=protected-access
        rules = [AzureVMFirewallRule(self.firewall, rule) for rule
                 in self.firewall._vm_firewall.security_rules
                 if rule.priority < 3500]
        return ClientPagedResultList(self._provider, rules,
                                     limit=limit, marker=marker)

    def create(self, direction, protocol=None, from_port=None, to_port=None,
               cidr=None, src_dest_fw=None):
        if protocol and from_port and to_port:
            return self._create_rule(direction, protocol, from_port,
                                     to_port, cidr)
        elif src_dest_fw:
            result = None
            fw = (self._provider.security.vm_firewalls.get(src_dest_fw)
                  if isinstance(src_dest_fw, str) else src_dest_fw)
            for rule in fw.rules:
                result = self._create_rule(
                    rule.direction, rule.protocol, rule.from_port,
                    rule.to_port, rule.cidr)
            return result
        else:
            return None

    def _create_rule(self, direction, protocol, from_port, to_port, cidr):

        # If cidr is None, default values is set as 0.0.0.0/0
        if not cidr:
            cidr = '0.0.0.0/0'

        count = len(self.firewall._vm_firewall.security_rules) + 1
        rule_name = "cb-rule-" + str(count)
        priority = 1000 + count
        destination_port_range = str(from_port) + "-" + str(to_port)
        source_port_range = '*'
        destination_address_prefix = "*"
        access = "Allow"
        direction = ("Inbound" if direction == TrafficDirection.INBOUND
                     else "Outbound")
        parameters = {"priority": priority,
                      "protocol": protocol,
                      "source_port_range": source_port_range,
                      "source_address_prefix": cidr,
                      "destination_port_range": destination_port_range,
                      "destination_address_prefix": destination_address_prefix,
                      "access": access,
                      "direction": direction}
        result = self._provider.azure_client. \
            create_vm_firewall_rule(self.firewall.id,
                                    rule_name, parameters)
        # pylint:disable=protected-access
        self.firewall._vm_firewall.security_rules.append(result)
        return AzureVMFirewallRule(self.firewall, result)


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
