"""
DataTypes used by this provider
"""
import inspect
import json

from cloudbridge.cloud.base.resources import BaseBucket, BaseSecurityGroup, BaseSecurityGroupRule


class AzureSecurityGroup(BaseSecurityGroup):
    def __init__(self, provider, security_group):
        super(AzureSecurityGroup, self).__init__(provider, security_group)

    @property
    def network_id(self):
        return self._security_group.resource_guid

    @property
    def rules(self):
        security_group_rules = []
        for rule in self._security_group.default_security_rules:
            if rule.direction == "Inbound":
                sg_rule = AzureSecurityGroupRule(self._provider, rule, self)
                sg_rule.is_default = True
                security_group_rules.append(sg_rule)
        for custom_rule in self._security_group.security_rules:
            sg_custom_rule = AzureSecurityGroupRule(self._provider, custom_rule, self)
            sg_custom_rule.is_default = False
            security_group_rules.append(sg_custom_rule)
        return security_group_rules

    def add_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        """
        Create a security group rule.

        You need to pass in either ``src_group`` OR ``ip_protocol``,
        ``from_port``, ``to_port``, and ``cidr_ip``.  In other words, either
        you are authorizing another group or you are authorizing some
        ip-based rule.

        :type ip_protocol: str
        :param ip_protocol: Either ``tcp`` | ``udp`` | ``icmp``

        :type from_port: int
        :param from_port: The beginning port number you are enabling

        :type to_port: int
        :param to_port: The ending port number you are enabling

        :type cidr_ip: str or list of strings
        :param cidr_ip: The CIDR block you are providing access to.

        :type src_group: ``object`` of :class:`.SecurityGroup`
        :param src_group: The Security Group you are granting access to.

        :rtype: :class:``.SecurityGroupRule``
        :return: Rule object if successful or ``None``.
        """

        return None

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        for rule in self.rules:
            if (rule.ip_protocol == ip_protocol and
               rule.from_port == from_port and
               rule.to_port == to_port and
               rule.cidr_ip == cidr_ip):
                return rule
        return None

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = [json.loads(r) for r in json_rules]
        if js.get('network_id'):
            js.pop('network_id')  # Omit for consistency across cloud providers
        return json.dumps(js, sort_keys=True)


class AzureSecurityGroupRule(BaseSecurityGroupRule):

    def __init__(self, provider, rule, parent):
        super(AzureSecurityGroupRule, self).__init__(provider, rule, parent)

    @property
    def name(self):
        return self._rule.name

    @property
    def id(self):
        return self._rule.id

    @property
    def ip_protocol(self):
        return self._rule.protocol

    @property
    def from_port(self):
        if self._rule.source_port_range == '*':
            return self._rule.source_port_range
        source_port_range = self._rule.source_port_range
        port_range_split = source_port_range.split('-', 1)
        return port_range_split[0]

    @property
    def to_port(self):
        if self._rule.source_port_range == '*':
            return self._rule.source_port_range
        source_port_range = self._rule.source_port_range
        port_range_split = source_port_range.split('-', 1)
        return port_range_split[1]

    @property
    def cidr_ip(self):
        return self._rule.destination_address_prefix

    @property
    def group(self):
        return None

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        js['group'] = self.group.id if self.group else ''
        js['parent'] = self.parent.id if self.parent else ''
        return json.dumps(js, sort_keys=True)

    def delete(self):
        if self.is_default:
            raise Exception('Default Security Rules cannot be deleted!')
        security_group = self.parent.name
        resource_group = self._provider.resource_group
        sro = self._provider.azure_wrapper.delete_security_group_rule(self.name, resource_group, security_group)
        for i, o in enumerate(self.parent._security_group.security_rules):
            if o.name == self.name:
                del self.parent._security_group.security_rules[i]
                break


class AzureBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(AzureBucket, self).__init__(provider)
        self._bucket = bucket

    @property
    def id(self):
        return self._bucket.name

    @property
    def name(self):
        """
        Get this bucket's name.
        """
        return self._bucket.name

    def get(self, key):
        """
        Retrieve a given object from this bucket.
        """
        pass

    def list(self, limit=None, marker=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        pass

    def delete(self, delete_contents=False):
        """
        Delete this bucket.
        """
        pass

    def create_object(self, name):
        return None

    def exists(self, name):
        pass
