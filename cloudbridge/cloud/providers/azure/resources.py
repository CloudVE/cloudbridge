"""
DataTypes used by this provider
"""
import inspect
import json
from datetime import datetime

from cloudbridge.cloud.base.resources import BaseBucket, BaseSecurityGroup, BaseSecurityGroupRule, BaseBucketObject, \
    ClientPagedResultList


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
        security_group = self._security_group.name
        resource_group = self._provider.resource_group
        count = len(self.rules) + 1
        rule_name = "Rule - " + str(count)
        priority = count * 100
        destination_port_range = "*"
        destination_address_prefix = "*"
        access = "Allow"
        direction = "Inbound"
        parameters = {"protocol": ip_protocol, "source_port_range": str(from_port) + "-" + str(to_port),
                      "destination_port_range": destination_port_range,"priority": priority,
                      "source_address_prefix": cidr_ip, "destination_address_prefix": destination_address_prefix,
                      "access": access, "direction": direction}
        result = self._provider.azure_client.create_security_group_rule(security_group, rule_name, parameters)
        self._security_group.security_rules.append(result)
        return result

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
        return self._rule.source_address_prefix

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
        sro = self._provider.azure_client.delete_security_group_rule(self.name, security_group)
        for i, o in enumerate(self.parent._security_group.security_rules):
            if o.name == self.name:
                del self.parent._security_group.security_rules[i]
                break


class AzureBucketObject(BaseBucketObject):

    def __init__(self, provider, container, key):
        super(AzureBucketObject, self).__init__(provider)
        self._container = container
        self._key = key

    @property
    def id(self):
        return self._key.name

    @property
    def name(self):
        """
        Get this object's name.
        """
        return self._key.name

    @property
    def size(self):
        """
        Get this object's size.
        """
        return self._key.properties.content_length

    @property
    def last_modified(self):

        """
        Get the date and time this object was last modified.
        """

        return str(self._key.properties.last_modified)

    def iter_content(self):
        """
        Returns this object's content as an
        iterable.
        """
        blob = self._provider.azure_client.get_blob_content(self._container.name, self._key.name)
        return blob.content

    def upload(self, data):
        """
        Set the contents of this object to the data read from the source
        string.
        """
        self._provider.azure_client.create_blob_from_text(self._container.name, self.name, data)

    def upload_from_file(self, path):
        """
        Store the contents of the file pointed by the "path" variable.
        """
        self._provider.azure_client.create_blob_from_file(self._container.name, self.name, path)

    def delete(self):
        """
        Delete this object.

        :rtype: bool
        :return: True if successful
        """
        self._provider.azure_client.delete_blob(self._container.name, self.name)

    def generate_url(self, expires_in=0):
        """
        Generate a URL to this object.
        """
        return self._provider.azure_client.get_blob_url(self._container.name, self.name)


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
        obj =self._provider.azure_client.get_blob(self.name, key)
        if obj:
            return AzureBucketObject(self._provider, self, obj)

        return None

    def list(self, limit=None, marker=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        objects = [AzureBucketObject(self._provider, self, obj)
                  for obj in self._provider.azure_client.list_blobs(self.name) ]
        return ClientPagedResultList(self._provider, objects,
                                     limit=limit, marker=marker)

    def delete(self, delete_contents=True):
        """
        Delete this bucket.
        """
        self._provider.azure_client.delete_container(self.name)

    def create_object(self, name):
        obj = self._provider.azure_client.create_blob_from_text(self.name, name,'')
        return self.get(name)

    def exists(self, name):
        """
        Determine if an object with given name exists in this bucket.
        """
        return True if self.get(name) else False
