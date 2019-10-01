import logging

from cloudbridge.interfaces.subservices import BucketObjectSubService
from cloudbridge.interfaces.subservices import FloatingIPSubService
from cloudbridge.interfaces.subservices import GatewaySubService
from cloudbridge.interfaces.subservices import SubnetSubService
from cloudbridge.interfaces.subservices import VMFirewallRuleSubService

from .resources import BasePageableObjectMixin

log = logging.getLogger(__name__)


class BaseBucketObjectSubService(BasePageableObjectMixin,
                                 BucketObjectSubService):

    def __init__(self, provider, bucket):
        self.__provider = provider
        self.bucket = bucket

    @property
    def _provider(self):
        return self.__provider

    def get(self, name):
        return self._provider.storage._bucket_objects.get(self.bucket, name)

    def list(self, limit=None, marker=None, prefix=None):
        return self._provider.storage._bucket_objects.list(self.bucket, limit,
                                                           marker, prefix)

    def find(self, **kwargs):
        return self._provider.storage._bucket_objects.find(self.bucket,
                                                           **kwargs)

    def create(self, name):
        return self._provider.storage._bucket_objects.create(self.bucket, name)


class BaseGatewaySubService(GatewaySubService, BasePageableObjectMixin):

    def __init__(self, provider, network):
        self._network = network
        self.__provider = provider

    @property
    def _provider(self):
        return self.__provider

    def get_or_create(self):
        return (self._provider.networking
                              ._gateways
                              .get_or_create(self._network))

    def delete(self, gateway):
        return (self._provider.networking
                              ._gateways
                              .delete(self._network, gateway))

    def list(self, limit=None, marker=None):
        return (self._provider.networking
                              ._gateways
                              .list(self._network, limit, marker))


class BaseVMFirewallRuleSubService(BasePageableObjectMixin,
                                   VMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        self.__provider = provider
        self._firewall = firewall

    @property
    def _provider(self):
        return self.__provider

    def get(self, rule_id):
        return self._provider.security._vm_firewall_rules.get(self._firewall,
                                                              rule_id)

    def list(self, limit=None, marker=None):
        return self._provider.security._vm_firewall_rules.list(self._firewall,
                                                               limit, marker)

    def create(self, direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        return (self._provider
                    .security
                    ._vm_firewall_rules
                    .create(self._firewall, direction, protocol, from_port,
                            to_port, cidr, src_dest_fw))

    def find(self, **kwargs):
        return self._provider.security._vm_firewall_rules.find(self._firewall,
                                                               **kwargs)

    def delete(self, rule_id):
        return (self._provider
                    .security
                    ._vm_firewall_rules
                    .delete(self._firewall, rule_id))


class BaseFloatingIPSubService(FloatingIPSubService, BasePageableObjectMixin):

    def __init__(self, provider, gateway):
        self.__provider = provider
        self.gateway = gateway

    @property
    def _provider(self):
        return self.__provider

    def get(self, fip_id):
        return self._provider.networking._floating_ips.get(self.gateway,
                                                           fip_id)

    def list(self, limit=None, marker=None):
        return self._provider.networking._floating_ips.list(self.gateway,
                                                            limit, marker)

    def find(self, **kwargs):
        return self._provider.networking._floating_ips.find(self.gateway,
                                                            **kwargs)

    def create(self):
        return self._provider.networking._floating_ips.create(self.gateway)

    def delete(self, fip):
        return self._provider.networking._floating_ips.delete(self.gateway,
                                                              fip)


class BaseSubnetSubService(SubnetSubService, BasePageableObjectMixin):

    def __init__(self, provider, network):
        self.__provider = provider
        self.network = network

    @property
    def _provider(self):
        return self.__provider

    def get(self, subnet_id):
        sn = self._provider.networking.subnets.get(subnet_id)
        if sn.network_id != self.network.id:
            log.warning("The SubnetSubService nested in the network '{}' "
                        "returned subnet '{}' which is attached to another "
                        "network '{}'".format(str(self.network), str(sn),
                                              str(sn.network)))
        return sn

    def list(self, limit=None, marker=None):
        return self._provider.networking.subnets.list(network=self.network,
                                                      limit=limit,
                                                      marker=marker)

    def find(self, **kwargs):
        return self._provider.networking.subnets.find(network=self.network,
                                                      **kwargs)

    def create(self, label, cidr_block):
        return self._provider.networking.subnets.create(label,
                                                        self.network,
                                                        cidr_block)

    def delete(self, subnet):
        return self._provider.networking.subnets.delete(subnet)
